import copy
import datetime
import json
import logging
import os
from pathlib import Path
from urllib.parse import quote
from airavata.model.application.io.ttypes import DataType

from airavata.model.appcatalog.appdeployment.ttypes import (
    ApplicationDeploymentDescription,
    CommandObject,
    SetEnvPaths
)
from airavata.model.appcatalog.appinterface.ttypes import (
    ApplicationInterfaceDescription
)
from airavata.model.appcatalog.computeresource.ttypes import (
    BatchQueue,
    ComputeResourceDescription
)
from airavata.model.appcatalog.gatewayprofile.ttypes import (
    GatewayResourceProfile,
    StoragePreference
)
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    ComputeResourceReservation,
    GroupComputeResourcePreference,
    GroupResourceProfile,
    ResourceType,
    SlurmComputeResourcePreference,
    AwsComputeResourcePreference
)
from airavata.model.appcatalog.parser.ttypes import Parser
from airavata.model.appcatalog.storageresource.ttypes import (
    StorageResourceDescription
)
from airavata.model.application.io.ttypes import (
    InputDataObjectType,
    OutputDataObjectType
)
from airavata.model.data.replica.ttypes import (
    DataProductModel,
    DataReplicaLocationModel
)
from airavata.model.experiment.ttypes import (
    ExperimentModel,
    ExperimentStatistics,
    ExperimentSummaryModel
)
from airavata.model.group.ttypes import GroupModel, ResourcePermissionType
from airavata.model.job.ttypes import JobModel
from airavata.model.status.ttypes import (
    ExperimentState,
    ExperimentStatus,
    ProcessStatus
)
from airavata.model.user.ttypes import UserProfile
from airavata.model.workspace.ttypes import (
    Notification,
    NotificationPriority
)
from airavata_django_portal_sdk import (
    experiment_util
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from . import models, thrift_utils, view_utils

log = logging.getLogger(__name__)

# Directory under user storage where uploaded experiment input files are staged
# (matches the legacy airavata_django_portal_sdk convention).
TMP_INPUT_FILE_UPLOAD_DIR = "tmp"


def user_has_access(request, resource_id, permission="WRITE"):
    """gRPC sharing access check (Track D — replaces the Thrift userHasAccess).

    ``permission`` is the ResourcePermissionType enum name (WRITE/READ/OWNER/
    MANAGE_SHARING); the backend prefixes the gateway internally. The acting user
    is taken from the authenticated token context server-side, so ``user_id`` is
    passed for the facade signature but ignored by the backend.
    """
    return request.airavata.sharing.user_has_access(
        resource_id=resource_id,
        user_id=request.user.username,
        permission_type=permission)


class FullyEncodedHyperlinkedIdentityField(
        serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, self.lookup_field):
            lookup_value = getattr(obj, self.lookup_field)
        else:
            lookup_value = obj.get(self.lookup_field)
        try:
            encoded_lookup_value = quote(lookup_value, safe="")
        except Exception:
            log.warning(
                "Failed to encode lookup_value [{}] for lookup_field "
                "[{}] of object [{}]".format(
                    lookup_value, self.lookup_field, obj))
            raise
        # Bit of a hack. Django's URL reversing does URL encoding but it
        # doesn't encode all characters including some like '/' that are used
        # in URL mappings.
        kwargs = {self.lookup_url_kwarg: "__PLACEHOLDER__"}
        url = self.reverse(view_name, kwargs=kwargs,
                           request=request, format=format)
        return url.replace("__PLACEHOLDER__", encoded_lookup_value)


class UTCPosixTimestampDateTimeField(serializers.DateTimeField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default = self.current_time_ms
        self.initial = self.initial_value
        self.required = False

    def to_representation(self, obj):
        # Create datetime instance from milliseconds that is aware of timezon
        dt = datetime.datetime.fromtimestamp(obj / 1000, datetime.timezone.utc)
        return super().to_representation(dt)

    def to_internal_value(self, data):
        dt = super().to_internal_value(data)
        return int(dt.timestamp() * 1000)

    def initial_value(self):
        return self.to_representation(self.current_time_ms())

    def current_time_ms(self):
        return int(datetime.datetime.utcnow().timestamp() * 1000)


class ProtoTimestampField(UTCPosixTimestampDateTimeField):
    """Renders a protobuf int64 epoch-millis field as the same ISO timestamp the
    Thrift-generated serializers produced.

    proto3 scalar int fields default to ``0`` (never None), so an unset timestamp
    reads as ``0``. When ``null_if_zero`` is set the field treats ``0`` as the
    Thrift ``None`` and renders ``null`` (matching the old ``allow_null`` fields
    whose adapters mapped ``pb.<time> or None``); otherwise ``0`` renders as the
    epoch like the old non-nullable fields did.
    """

    def __init__(self, *args, null_if_zero=False, **kwargs):
        self.null_if_zero = null_if_zero
        if null_if_zero:
            kwargs.setdefault('allow_null', True)
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        if self.null_if_zero and not obj:
            return None
        return super().to_representation(obj)


class ProtoEnumNameField(serializers.Field):
    """Renders a protobuf enum field as the enum member NAME, the same string the
    Thrift-generated ``ThriftEnumField`` / ``EnumChoiceField`` emitted.

    The instance is the protobuf message and ``source`` is the proto enum field
    name; ``to_representation`` receives that field's integer value and resolves
    it to the member name. Construct via :func:`proto_enum_name_field`, which
    snapshots the proto enum descriptor into the plain ``by_number``/``by_name``
    dicts this field holds (the descriptor itself cannot be deep-copied, and DRF
    deep-copies field instances when binding them). ``proto_prefix`` strips a
    proto-only member prefix (proto3 namespaces members that would otherwise
    collide, e.g. ``NOTIFICATION_PRIORITY_LOW`` -> ``LOW``); the bare-named
    ``*_UNKNOWN`` zero sentinel renders ``None`` to match the old nullable fields.
    """

    def __init__(self, by_number, by_name, proto_prefix='', **kwargs):
        self._by_number = by_number
        self._by_name = by_name
        self.proto_prefix = proto_prefix
        super().__init__(**kwargs)

    def to_representation(self, value):
        name = self._by_number[value]
        if self.proto_prefix and name.startswith(self.proto_prefix):
            name = name[len(self.proto_prefix):]
        if name.endswith('UNKNOWN') and value == 0:
            return None
        return name

    def to_internal_value(self, data):
        # Writes pass the member name; map back to the proto integer value.
        name = data
        if self.proto_prefix and (self.proto_prefix + name) in self._by_name:
            name = self.proto_prefix + name
        try:
            return self._by_name[name]
        except KeyError:
            self.fail('invalid_choice', input=data)


def proto_enum_name_field(enum_descriptor, proto_prefix='', **kwargs):
    """Build a :class:`ProtoEnumNameField` from a proto enum descriptor.

    Snapshots the descriptor into plain int<->name dicts so the resulting field
    is deep-copyable (DRF deep-copies fields when binding them to a serializer).
    """
    return ProtoEnumNameField(
        by_number={v.number: v.name for v in enum_descriptor.values},
        by_name={v.name: v.number for v in enum_descriptor.values},
        proto_prefix=proto_prefix, **kwargs)


class StoredJSONField(serializers.JSONField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            if value:
                return json.loads(value)
            else:
                return value
        except Exception:
            return value

    def to_internal_value(self, data):
        try:
            return json.dumps(data)
        except (TypeError, ValueError):
            self.fail('invalid')


class OrderedListField(serializers.ListField):

    def __init__(self, *args, **kwargs):
        self.order_by = kwargs.pop('order_by', None)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if rep is not None:
            rep.sort(key=lambda item: item[self.order_by])
        return rep

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        # Update order field based on order in array
        items = validated_data if validated_data else []
        for i in range(len(items)):
            items[i][self.order_by] = i
        return validated_data


class GroupSerializer(thrift_utils.create_serializer_class(GroupModel)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:group-detail',
        lookup_field='id',
        lookup_url_kwarg='group_id')
    isAdmin = serializers.SerializerMethodField()
    isOwner = serializers.SerializerMethodField()
    isMember = serializers.SerializerMethodField()
    isGatewayAdminsGroup = serializers.SerializerMethodField()
    isReadOnlyGatewayAdminsGroup = serializers.SerializerMethodField()
    isDefaultGatewayUsersGroup = serializers.SerializerMethodField()

    class Meta:
        required = ('name',)
        read_only = ('ownerId',)

    def create(self, validated_data):
        group = super().create(validated_data)
        group.ownerId = self.context['request'].user.username + \
            "@" + settings.GATEWAY_ID
        return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get(
            'description', instance.description)
        # Calculate added and removed members
        old_members = set(instance.members)
        new_members = set(validated_data.get('members', instance.members))
        removed_members = old_members - new_members
        added_members = new_members - old_members
        instance._removed_members = list(removed_members)
        instance._added_members = list(added_members)
        instance.members = validated_data.get('members', instance.members)
        # Calculate added and removed admins
        old_admins = set(instance.admins)
        new_admins = set(validated_data.get('admins', instance.admins))
        removed_admins = old_admins - new_admins
        added_admins = new_admins - old_admins
        instance._removed_admins = list(removed_admins)
        instance._added_admins = list(added_admins)
        instance.admins = validated_data.get('admins', instance.admins)
        # Add new admins that aren't members to the added_members list
        instance._added_members.extend(list(added_admins - new_members))
        instance.members.extend(list(added_admins - new_members))
        return instance

    def get_isAdmin(self, group):
        request = self.context['request']
        return request.airavata.sharing.gm_has_admin_access(
            group.id,
            request.user.username + "@" + settings.GATEWAY_ID)

    def get_isOwner(self, group):
        request = self.context['request']
        return group.ownerId == (request.user.username +
                                 "@" +
                                 settings.GATEWAY_ID)

    def get_isMember(self, group):
        request = self.context['request']
        username = request.user.username + "@" + settings.GATEWAY_ID
        return group.members and username in group.members

    def get_isGatewayAdminsGroup(self, group):
        return group.id == self._gateway_groups()['adminsGroupId']

    def get_isReadOnlyGatewayAdminsGroup(self, group):
        return group.id == self._gateway_groups()['readOnlyAdminsGroupId']

    def get_isDefaultGatewayUsersGroup(self, group):
        return group.id == self._gateway_groups()['defaultGatewayUsersGroupId']

    def _gateway_groups(self):
        request = self.context['request']
        # gateway_groups_middleware sets this session variable
        if 'GATEWAY_GROUPS' in request.session:
            return request.session['GATEWAY_GROUPS']
        else:
            gg = request.airavata.compute.get_gateway_groups()
            return {
                'adminsGroupId': gg.admins_group_id,
                'readOnlyAdminsGroupId': gg.read_only_admins_group_id,
                'defaultGatewayUsersGroupId': gg.default_gateway_users_group_id,
            }


class ProjectSerializer(serializers.Serializer):
    """Proto-native serializer for the gRPC ``Project`` message.

    Reads protobuf fields directly (``project_id``, ``creation_time``, ...) and
    emits the historical Thrift-named JSON keys (``projectID``, ``creationTime``,
    ...) so the REST contract with the Vue frontend is unchanged. ``save()``
    returns a proto ``Project`` the view passes straight to the gRPC facade.
    """

    projectID = serializers.CharField(source='project_id', read_only=True)
    owner = serializers.CharField(read_only=True)
    gatewayId = serializers.CharField(source='gateway_id', read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(
        allow_blank=True, allow_null=True, required=False)
    creationTime = ProtoTimestampField(
        source='creation_time', null_if_zero=True, read_only=True)
    sharedUsers = serializers.ListField(
        source='shared_users', child=serializers.CharField(),
        read_only=True)
    sharedGroups = serializers.ListField(
        source='shared_groups', child=serializers.CharField(),
        read_only=True)
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:project-detail',
        lookup_field='project_id',
        lookup_url_kwarg='project_id')
    experiments = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:project-experiments',
        lookup_field='project_id',
        lookup_url_kwarg='project_id')
    userHasWriteAccess = serializers.SerializerMethodField()
    isOwner = serializers.SerializerMethodField()

    def create(self, validated_data):
        from airavata_sdk.generated.org.apache.airavata.model.workspace import (
            workspace_pb2,
        )
        return workspace_pb2.Project(
            owner=validated_data.get('owner', '') or '',
            gateway_id=validated_data.get('gateway_id', '') or '',
            name=validated_data.get('name', '') or '',
            description=validated_data.get('description', '') or '',
        )

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            instance.name = validated_data['name'] or ''
        if 'description' in validated_data:
            instance.description = validated_data['description'] or ''
        return instance

    def get_userHasWriteAccess(self, project):
        return user_has_access(self.context['request'], project.project_id)

    def get_isOwner(self, project):
        request = self.context['request']
        return project.owner == request.user.username


class ApplicationModuleSerializer(serializers.Serializer):
    """Proto-native serializer for the gRPC ``ApplicationModule`` message.

    Reads the protobuf directly and emits the historical Thrift-named JSON keys.
    ``save()`` returns a proto ``ApplicationModule`` the view passes to the facade.
    """

    appModuleId = serializers.CharField(source='app_module_id', read_only=True)
    appModuleName = serializers.CharField(source='app_module_name')
    appModuleVersion = serializers.CharField(
        source='app_module_version', allow_blank=True, allow_null=True,
        required=False)
    appModuleDescription = serializers.CharField(
        source='app_module_description', allow_blank=True, allow_null=True,
        required=False)
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-detail',
        lookup_field='app_module_id',
        lookup_url_kwarg='app_module_id')
    applicationInterface = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-application-interface',
        lookup_field='app_module_id',
        lookup_url_kwarg='app_module_id')
    applicationDeployments = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-application-deployments',
        lookup_field='app_module_id',
        lookup_url_kwarg='app_module_id')
    userHasWriteAccess = serializers.SerializerMethodField()

    def create(self, validated_data):
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment import (  # noqa: E501
            app_deployment_pb2,
        )
        return app_deployment_pb2.ApplicationModule(
            app_module_name=validated_data.get('app_module_name', '') or '',
            app_module_version=validated_data.get('app_module_version', '') or '',
            app_module_description=validated_data.get(
                'app_module_description', '') or '',
        )

    def update(self, instance, validated_data):
        if 'app_module_name' in validated_data:
            instance.app_module_name = validated_data['app_module_name'] or ''
        if 'app_module_version' in validated_data:
            instance.app_module_version = (
                validated_data['app_module_version'] or '')
        if 'app_module_description' in validated_data:
            instance.app_module_description = (
                validated_data['app_module_description'] or '')
        return instance

    def get_userHasWriteAccess(self, appModule):
        request = self.context['request']
        return request.is_gateway_admin


class EnumChoiceField(serializers.ChoiceField):
    def __init__(self, enum_class, **kwargs):
        self.enum_class = enum_class
        kwargs['choices'] = [(member.name, member.name) for member in enum_class]
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                return self.enum_class(data)
            except ValueError:
                self.fail('invalid_choice', input=data)
        try:
            return self.enum_class[data]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        return value.name


class InputDataObjectTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    type = EnumChoiceField(enum_class=DataType)
    applicationArgument = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    standardInput = serializers.BooleanField(default=False)
    userFriendlyDescription = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    metaData = StoredJSONField(allow_null=True, required=False)
    inputOrder = serializers.IntegerField(required=False, allow_null=True)
    isRequired = serializers.BooleanField(default=False)
    requiredToAddedToCommandLine = serializers.BooleanField(default=False)
    dataStaged = serializers.BooleanField(default=False)
    storageResourceId = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    isReadOnly = serializers.BooleanField(default=False)
    overrideFilename = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    def create(self, validated_data):
        return InputDataObjectType(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance

class OutputDataObjectTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    type = EnumChoiceField(enum_class=DataType)
    applicationArgument = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    isRequired = serializers.BooleanField(default=False)
    requiredToAddedToCommandLine = serializers.BooleanField(default=False)
    dataMovement = serializers.BooleanField(default=False)
    location = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    searchQuery = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    outputStreaming = serializers.BooleanField(default=False)
    storageResourceId = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    metaData = StoredJSONField(allow_null=True, required=False)

    def create(self, validated_data):
        return OutputDataObjectType(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance

class ApplicationInterfaceDescriptionSerializer(serializers.Serializer):
    applicationInterfaceId = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    applicationName = serializers.CharField()
    applicationDescription = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    applicationModules = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    applicationInputs = InputDataObjectTypeSerializer(many=True, allow_null=True, required=False)
    applicationOutputs = OutputDataObjectTypeSerializer(many=True, allow_null=True, required=False)
    archiveWorkingDirectory = serializers.BooleanField(default=False)
    hasOptionalFileInputs = serializers.BooleanField(default=False, read_only=True)

    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-interface-detail',
        lookup_field='applicationInterfaceId',
        lookup_url_kwarg='app_interface_id', read_only=True)
    userHasWriteAccess = serializers.SerializerMethodField()
    showQueueSettings = serializers.BooleanField(required=False)
    queueSettingsCalculatorId = serializers.CharField(allow_null=True, required=False)

    def create(self, validated_data):
        # Convert inputs/outputs from dicts to Thrift objects
        inputs_data = validated_data.pop('applicationInputs', None)
        outputs_data = validated_data.pop('applicationOutputs', None)

        # Remove Django specific fields
        validated_data.pop('showQueueSettings', None)
        validated_data.pop('queueSettingsCalculatorId', None)
        validated_data.pop('url', None)
        validated_data.pop('userHasWriteAccess', None)

        if 'applicationInterfaceId' in validated_data and validated_data['applicationInterfaceId'] is None:
            validated_data['applicationInterfaceId'] = ""

        application_interface = ApplicationInterfaceDescription(**validated_data)

        if inputs_data is not None:
            application_interface.applicationInputs = [InputDataObjectType(**inp) for inp in inputs_data]
        if outputs_data is not None:
            application_interface.applicationOutputs = [OutputDataObjectType(**out) for out in outputs_data]

        return application_interface

    def update(self, instance, validated_data):
        defaults = {}
        if "showQueueSettings" in validated_data:
            defaults["show_queue_settings"] = validated_data.pop("showQueueSettings")
        if "queueSettingsCalculatorId" in validated_data:
            defaults["queue_settings_calculator_id"] = validated_data.pop("queueSettingsCalculatorId")
        application_module_id = instance.applicationModules[0]
        if defaults:
            models.ApplicationSettings.objects.update_or_create(
                application_module_id=application_module_id, defaults=defaults
            )

        inputs_data = validated_data.pop('applicationInputs', None)
        outputs_data = validated_data.pop('applicationOutputs', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if inputs_data is not None:
            instance.applicationInputs = [InputDataObjectType(**inp) for inp in inputs_data]
        if outputs_data is not None:
            instance.applicationOutputs = [OutputDataObjectType(**out) for out in outputs_data]

        return instance

    def get_userHasWriteAccess(self, appDeployment):
        request = self.context['request']
        return request.is_gateway_admin


class CommandObjectSerializer(
        thrift_utils.create_serializer_class(CommandObject)):
    pass


class SetEnvPathsSerializer(
        thrift_utils.create_serializer_class(SetEnvPaths)):
    pass


class ApplicationDeploymentDescriptionSerializer(
    thrift_utils.create_serializer_class(
        ApplicationDeploymentDescription)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-deployment-detail',
        lookup_field='appDeploymentId',
        lookup_url_kwarg='app_deployment_id')
    # Default values returned in these results have been overridden with app
    # deployment defaults for any that exist
    queues = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:application-deployment-queues',
        lookup_field='appDeploymentId',
        lookup_url_kwarg='app_deployment_id')
    userHasWriteAccess = serializers.SerializerMethodField()
    moduleLoadCmds = OrderedListField(
        order_by='commandOrder',
        child=CommandObjectSerializer(),
        allow_null=True)
    preJobCommands = OrderedListField(
        order_by='commandOrder',
        child=CommandObjectSerializer(),
        allow_null=True)
    postJobCommands = OrderedListField(
        order_by='commandOrder',
        child=CommandObjectSerializer(),
        allow_null=True)
    libPrependPaths = OrderedListField(
        order_by='envPathOrder',
        child=SetEnvPathsSerializer(),
        allow_null=True)
    libAppendPaths = OrderedListField(
        order_by='envPathOrder',
        child=SetEnvPathsSerializer(),
        allow_null=True)
    setEnvironment = OrderedListField(
        order_by='envPathOrder',
        child=SetEnvPathsSerializer(),
        allow_null=True)

    def get_userHasWriteAccess(self, appDeployment):
        return user_has_access(
            self.context['request'], appDeployment.appDeploymentId)


class ComputeResourceDescriptionSerializer(
        thrift_utils.create_serializer_class(ComputeResourceDescription)):
    pass


class BatchQueueSerializer(thrift_utils.create_serializer_class(BatchQueue)):
    pass


class ExperimentStatusSerializer(
        thrift_utils.create_serializer_class(ExperimentStatus)):
    timeOfStateChange = UTCPosixTimestampDateTimeField()


class ProcessStatusSerializer(
        thrift_utils.create_serializer_class(ProcessStatus)):
    timeOfStateChange = UTCPosixTimestampDateTimeField()


class ExperimentSerializer(
        thrift_utils.create_serializer_class(ExperimentModel)):
    class Meta:
        required = ('projectId', 'experimentType', 'experimentName')
        read_only = ('userName', 'gatewayId')

    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:experiment-detail',
        lookup_field='experimentId',
        lookup_url_kwarg='experiment_id')
    full_experiment = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:full-experiment-detail',
        lookup_field='experimentId',
        lookup_url_kwarg='experiment_id')
    project = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:project-detail',
        lookup_field='projectId',
        lookup_url_kwarg='project_id')
    jobs = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:experiment-jobs',
        lookup_field='experimentId',
        lookup_url_kwarg='experiment_id')
    shared_entity = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:shared-entity-detail',
        lookup_field='experimentId',
        lookup_url_kwarg='entity_id')
    experimentInputs = OrderedListField(
        order_by='inputOrder',
        child=InputDataObjectTypeSerializer(),
        allow_null=True)
    experimentOutputs = serializers.ListField(
        child=OutputDataObjectTypeSerializer(),
        allow_null=True)
    creationTime = UTCPosixTimestampDateTimeField(allow_null=True)
    experimentStatus = ExperimentStatusSerializer(many=True, allow_null=True)
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, experiment):
        return user_has_access(self.context['request'], experiment.experimentId)

    def to_representation(self, experiment):
        result = super().to_representation(experiment)
        self._add_intermediate_output_information(experiment, result)
        return result

    def _add_intermediate_output_information(self, experiment, representation):
        request = self.context['request']

        # If experiment is EXECUTING, add intermediateOutput information to
        # experiment outputs
        if (experiment.experimentStatus and
                experiment.experimentStatus[-1].state == ExperimentState.EXECUTING):
            for output in representation["experimentOutputs"]:
                output["intermediateOutput"] = {"processStatus": None}
                try:
                    can_fetch = experiment_util.intermediate_output.can_fetch_intermediate_output(request, experiment, output["name"])
                    output["intermediateOutput"]["canFetch"] = can_fetch
                    process_status = experiment_util.intermediate_output.get_intermediate_output_process_status(
                        request, experiment, output["name"])
                    if process_status:
                        serializer = ProcessStatusSerializer(
                            process_status, context={'request': request})
                        output["intermediateOutput"]["processStatus"] = serializer.data
                    data_products = experiment_util.intermediate_output.get_intermediate_output_data_products(
                        request, experiment=experiment, output_name=output["name"])
                    data_product_serializer = DataProductSerializer(
                        data_products, context={'request': request}, many=True)
                    output["intermediateOutput"]["dataProducts"] = data_product_serializer.data
                except Exception:
                    log.debug("Failed to get intermediate output status", exc_info=True)


class DataReplicaLocationSerializer(
        thrift_utils.create_serializer_class(DataReplicaLocationModel)):
    creationTime = UTCPosixTimestampDateTimeField()
    lastModifiedTime = UTCPosixTimestampDateTimeField()


class DataProductSerializer(
        thrift_utils.create_serializer_class(DataProductModel)):
    creationTime = UTCPosixTimestampDateTimeField()
    modifiedTime = UTCPosixTimestampDateTimeField()
    lastModifiedTime = UTCPosixTimestampDateTimeField()
    replicaLocations = DataReplicaLocationSerializer(many=True)
    downloadURL = serializers.SerializerMethodField()
    isInputFileUpload = serializers.SerializerMethodField()
    filesize = serializers.SerializerMethodField()
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_downloadURL(self, data_product):
        """Lazy portal URL to the byte-streaming download endpoint.

        Returns None when the data product has no replica. Resolving the bytes
        is deferred to the endpoint, so this getter makes no backend call.
        """
        request = self.context['request']
        if not getattr(data_product, 'replicaLocations', None):
            return None
        base = request.build_absolute_uri(
            reverse('django_airavata_api:download-file'))
        return base + '?data-product-uri=' + quote(data_product.productUri)

    def get_isInputFileUpload(self, data_product):
        """Return True if this is an uploaded input file.

        Derived from the data product alone (no backend call): an uploaded
        input file lives directly under the input-staging directory
        (TMP_INPUT_FILE_UPLOAD_DIR == "tmp"), so the first replica's file path
        has that directory as its immediate parent.
        """
        replicas = getattr(data_product, 'replicaLocations', None) or []
        if not replicas or not replicas[0].filePath:
            return False
        parent = os.path.dirname(replicas[0].filePath)
        return os.path.basename(parent) == TMP_INPUT_FILE_UPLOAD_DIR

    def get_filesize(self, data_product):
        # productSize comes from the data product registry; no backend call.
        return getattr(data_product, 'productSize', None) or 0

    def get_userHasWriteAccess(self, data_product: DataProductModel):
        """Whether the requesting user may write this data product.

        Derived without a backend file-metadata call: the owner always has
        write access; in a shared directory only gateway admins do; otherwise
        (a user's own private storage) write is allowed.
        """
        request = self.context['request']
        owner = getattr(data_product, 'ownerName', None)
        if owner and owner == request.user.username:
            return True
        replicas = getattr(data_product, 'replicaLocations', None) or []
        if replicas and replicas[0].filePath:
            if view_utils.is_shared_path(replicas[0].filePath):
                # Only admins can edit files in a shared directory.
                return request.is_gateway_admin
        return True


# TODO move this into airavata_sdk?
class FullExperiment:
    """Experiment with referenced data models."""

    def __init__(self, experimentModel, project=None, outputDataProducts=None,
                 inputDataProducts=None, applicationModule=None,
                 computeResource=None, jobDetails=None, outputViews=None):
        self.experiment = experimentModel
        self.experimentId = experimentModel.experimentId
        self.project = project
        self.outputDataProducts = outputDataProducts
        self.inputDataProducts = inputDataProducts
        self.applicationModule = applicationModule
        self.computeResource = computeResource
        self.jobDetails = jobDetails
        self.outputViews = outputViews


class JobSerializer(thrift_utils.create_serializer_class(JobModel)):
    creationTime = UTCPosixTimestampDateTimeField()


class FullExperimentSerializer(serializers.Serializer):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:full-experiment-detail',
        lookup_field='experimentId',
        lookup_url_kwarg='experiment_id')
    experiment = ExperimentSerializer()
    experimentId = serializers.CharField(read_only=True)
    outputDataProducts = DataProductSerializer(many=True, read_only=True)
    inputDataProducts = DataProductSerializer(many=True, read_only=True)
    applicationModule = ApplicationModuleSerializer(read_only=True)
    computeResource = ComputeResourceDescriptionSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    jobDetails = JobSerializer(many=True, read_only=True)
    outputViews = serializers.DictField(read_only=True)

    def create(self, validated_data):
        raise Exception("Not implemented")

    def update(self, instance, validated_data):
        raise Exception("Not implemented")


class BaseExperimentSummarySerializer(
        thrift_utils.create_serializer_class(ExperimentSummaryModel)):
    creationTime = UTCPosixTimestampDateTimeField()
    statusUpdateTime = UTCPosixTimestampDateTimeField()
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:experiment-detail',
        lookup_field='experimentId',
        lookup_url_kwarg='experiment_id')
    project = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:project-detail',
        lookup_field='projectId',
        lookup_url_kwarg='project_id')


class ExperimentSummarySerializer(BaseExperimentSummarySerializer):
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, experiment):
        return user_has_access(self.context['request'], experiment.experimentId)


class UserProfileSerializer(
        thrift_utils.create_serializer_class(UserProfile)):
    creationTime = UTCPosixTimestampDateTimeField()
    lastAccessTime = UTCPosixTimestampDateTimeField()


class ComputeResourceReservationSerializer(
        thrift_utils.create_serializer_class(ComputeResourceReservation)):
    startTime = UTCPosixTimestampDateTimeField(allow_null=True)
    endTime = UTCPosixTimestampDateTimeField(allow_null=True)


class GroupComputeResourcePreferenceSerializer(
        thrift_utils.create_serializer_class(GroupComputeResourcePreference)):
    reservations = serializers.SerializerMethodField()

    # Check if the object (e.g. SLURM type) has the 'reservations' attribute
    def get_reservations(self, obj):
        if hasattr(obj, 'reservations'):
            reservations_data = getattr(obj, 'reservations')
            if reservations_data is not None:
                return ComputeResourceReservationSerializer(reservations_data, many=True, context=self.context).data

        return []

    @staticmethod
    def _convert_nested_list_fields_to_thrift(slurm_pref):
        from collections import OrderedDict
        from airavata.model.appcatalog.groupresourceprofile.ttypes import (
            ComputeResourceReservation,
            GroupAccountSSHProvisionerConfig
        )

        if hasattr(slurm_pref, 'reservations') and slurm_pref.reservations:
            if isinstance(slurm_pref.reservations, list):
                converted_reservations = []
                for res in slurm_pref.reservations:
                    if isinstance(res, (dict, OrderedDict)):
                        converted_reservations.append(ComputeResourceReservation(**res))
                    else:
                        converted_reservations.append(res)
                slurm_pref.reservations = converted_reservations

        if hasattr(slurm_pref, 'groupSSHAccountProvisionerConfigs') and slurm_pref.groupSSHAccountProvisionerConfigs:
            if isinstance(slurm_pref.groupSSHAccountProvisionerConfigs, list):
                converted_configs = []
                for cfg in slurm_pref.groupSSHAccountProvisionerConfigs:
                    if isinstance(cfg, (dict, OrderedDict)):
                        converted_configs.append(GroupAccountSSHProvisionerConfig(**cfg))
                    else:
                        converted_configs.append(cfg)
                slurm_pref.groupSSHAccountProvisionerConfigs = converted_configs

    @staticmethod
    def _convert_specific_preferences_dict_to_thrift(pref_instance, resource_type):
        from collections import OrderedDict

        if not hasattr(pref_instance, 'specificPreferences'):
            return

        if isinstance(pref_instance.specificPreferences, (dict, OrderedDict)):
            specific_prefs_dict = pref_instance.specificPreferences

            union_type_class = None
            try:
                from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                    EnvironmentSpecificPreferences
                )
                union_type_class = EnvironmentSpecificPreferences
                log.debug(
                    "GCPreference: Got union type class from import: %s",
                    union_type_class.__name__,
                )
            except ImportError as e:
                log.error(
                    "GCPreference: Failed to import EnvironmentSpecificPreferences: %s",
                    str(e),
                    exc_info=True,
                )

            if union_type_class:
                pref_instance.specificPreferences = union_type_class()

                if resource_type == ResourceType.SLURM:
                    if 'slurm' in specific_prefs_dict:
                        slurm_data = specific_prefs_dict['slurm']
                    else:
                        slurm_data = specific_prefs_dict

                    if slurm_data and isinstance(slurm_data, dict) and len(slurm_data) > 0:
                        try:
                            from collections import OrderedDict
                            from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                                ComputeResourceReservation,
                                GroupAccountSSHProvisionerConfig
                            )

                            if 'reservations' in slurm_data and slurm_data['reservations']:
                                reservations_list = slurm_data['reservations']
                                if isinstance(reservations_list, list):
                                    converted_reservations = []
                                    for res in reservations_list:
                                        if isinstance(res, (dict, OrderedDict)):
                                            converted_reservations.append(ComputeResourceReservation(**res))
                                        else:
                                            converted_reservations.append(res)
                                    slurm_data['reservations'] = converted_reservations

                            if 'groupSSHAccountProvisionerConfigs' in slurm_data and slurm_data['groupSSHAccountProvisionerConfigs']:
                                configs_list = slurm_data['groupSSHAccountProvisionerConfigs']
                                if isinstance(configs_list, list):
                                    converted_configs = []
                                    for cfg in configs_list:
                                        if isinstance(cfg, (dict, OrderedDict)):
                                            converted_configs.append(GroupAccountSSHProvisionerConfig(**cfg))
                                        else:
                                            converted_configs.append(cfg)
                                    slurm_data['groupSSHAccountProvisionerConfigs'] = converted_configs

                            slurm_pref = SlurmComputeResourcePreference(**slurm_data)
                            pref_instance.specificPreferences.slurm = slurm_pref
                            GroupComputeResourcePreferenceSerializer._convert_nested_list_fields_to_thrift(slurm_pref)
                            log.info(
                                "GCPreference: Converted specificPreferences dict to SLURM Thrift union type, computeResourceId=%s",
                                pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                            )
                        except Exception as e:
                            log.error(
                                "GCPreference: Failed to create SlurmComputeResourcePreference from dict: %s, computeResourceId=%s",
                                str(e),
                                pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                                exc_info=True,
                            )
                    else:
                        log.info(
                            "GCPreference: specificPreferences dict is empty, created empty union type, computeResourceId=%s",
                            pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                        )
                elif resource_type == ResourceType.AWS:
                    if 'aws' in specific_prefs_dict:
                        aws_data = specific_prefs_dict['aws']
                    else:
                        aws_data = specific_prefs_dict

                    if aws_data and isinstance(aws_data, dict) and len(aws_data) > 0:
                        try:
                            aws_pref = AwsComputeResourcePreference(**aws_data)
                            pref_instance.specificPreferences.aws = aws_pref
                            log.info(
                                "GCPreference: Converted specificPreferences dict to AWS Thrift union type, computeResourceId=%s",
                                pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                            )
                        except Exception as e:
                            log.error(
                                "GCPreference: Failed to create AwsComputeResourcePreference from dict: %s, computeResourceId=%s",
                                str(e),
                                pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                                exc_info=True,
                            )
                    else:
                        log.info(
                            "GCPreference: specificPreferences dict is empty, created empty union type, computeResourceId=%s",
                            pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                        )
            else:
                log.error(
                    "GCPreference: Could not get union type class to convert specificPreferences dict, computeResourceId=%s",
                    pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                )
                union_type_created = False
                try:
                    test_instance = GroupComputeResourcePreference(resourceType=resource_type)
                    if test_instance.specificPreferences is not None:
                        pref_instance.specificPreferences = type(test_instance.specificPreferences)()
                        union_type_created = True
                        log.info(
                            "GCPreference: Created empty union type from test instance, computeResourceId=%s",
                            pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                        )
                except Exception as e:
                    log.warning(
                        "GCPreference: Failed to create union type from test instance: %s, trying direct construction",
                        str(e),
                    )

                if not union_type_created:
                    if hasattr(pref_instance, 'resourceType') and pref_instance.resourceType:
                        try:
                            temp = GroupComputeResourcePreference(resourceType=pref_instance.resourceType)
                            if temp.specificPreferences is not None:
                                pref_instance.specificPreferences = type(temp.specificPreferences)()
                                union_type_created = True
                                log.info(
                                    "GCPreference: Created empty union type using pref_instance.resourceType, computeResourceId=%s",
                                    pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                                )
                        except Exception as e2:
                            log.error(
                                "GCPreference: All attempts to create union type failed: %s, computeResourceId=%s",
                                str(e2),
                                pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                                exc_info=True,
                            )

                if not union_type_created:
                    log.error(
                        "GCPreference: Could not create union type at all! specificPreferences will remain as dict, computeResourceId=%s",
                        pref_instance.computeResourceId if hasattr(pref_instance, 'computeResourceId') else 'unknown',
                    )
        else:
            if hasattr(pref_instance.specificPreferences, 'slurm') and pref_instance.specificPreferences.slurm:
                GroupComputeResourcePreferenceSerializer._convert_nested_list_fields_to_thrift(
                    pref_instance.specificPreferences.slurm
                )

    def to_representation(self, instance):
        """
        Override to extract fields from specificPreferences union type.
        """
        ret = super().to_representation(instance)

        if hasattr(instance, 'specificPreferences') and instance.specificPreferences:
            if hasattr(instance.specificPreferences, 'slurm') and instance.specificPreferences.slurm:
                slurm_pref = instance.specificPreferences.slurm
                if hasattr(slurm_pref, 'allocationProjectNumber'):
                    ret['allocationProjectNumber'] = slurm_pref.allocationProjectNumber
                if 'specificPreferences' in ret and isinstance(ret['specificPreferences'], dict):
                    if 'slurm' not in ret['specificPreferences']:
                        ret['specificPreferences'] = {'slurm': ret['specificPreferences']}
            elif hasattr(instance.specificPreferences, 'aws') and instance.specificPreferences.aws:
                aws_pref = instance.specificPreferences.aws
                aws_fields = {
                    'region': getattr(aws_pref, 'region', None),
                    'preferredAmiId': getattr(aws_pref, 'preferredAmiId', None),
                    'preferredInstanceType': getattr(aws_pref, 'preferredInstanceType', None),
                }
                ret['specificPreferences'] = aws_fields

        return ret

    def create(self, validated_data):
        """
        Override create() to properly handle resourceType and specificPreferences union type.
        """
        if isinstance(validated_data, GroupComputeResourcePreference):
            resource_type = None
            if not hasattr(validated_data, 'resourceType') or validated_data.resourceType is None:
                from collections import OrderedDict
                if hasattr(validated_data, 'specificPreferences') and validated_data.specificPreferences:
                    if isinstance(validated_data.specificPreferences, (dict, OrderedDict)):
                        specific_prefs_dict = validated_data.specificPreferences
                        if 'slurm' in specific_prefs_dict or 'allocationProjectNumber' in specific_prefs_dict:
                            resource_type = ResourceType.SLURM
                        elif 'aws' in specific_prefs_dict or 'region' in specific_prefs_dict:
                            resource_type = ResourceType.AWS
                        else:
                            resource_type = ResourceType.SLURM
                    elif hasattr(validated_data.specificPreferences, 'slurm') and validated_data.specificPreferences.slurm:
                        resource_type = ResourceType.SLURM
                    elif hasattr(validated_data.specificPreferences, 'aws') and validated_data.specificPreferences.aws:
                        resource_type = ResourceType.AWS
                    else:
                        resource_type = ResourceType.SLURM
                else:
                    resource_type = ResourceType.SLURM

                if resource_type:
                    validated_data.resourceType = resource_type
            else:
                resource_type = validated_data.resourceType

            if resource_type:
                self._convert_specific_preferences_dict_to_thrift(validated_data, resource_type)

            return validated_data

        data = copy.deepcopy(validated_data)

        resource_type = data.get('resourceType')
        if resource_type is None:
            if 'allocationProjectNumber' in data or ('specificPreferences' in data and isinstance(data.get('specificPreferences'), dict) and 'slurm' in data.get('specificPreferences', {})):
                resource_type = ResourceType.SLURM
            elif 'specificPreferences' in data and isinstance(data.get('specificPreferences'), dict) and 'aws' in data.get('specificPreferences', {}):
                resource_type = ResourceType.AWS
            elif 'region' in data or 'preferredAmiId' in data or 'preferredInstanceType' in data:
                resource_type = ResourceType.AWS
            else:
                resource_type = ResourceType.SLURM

        if isinstance(resource_type, str):
            try:
                resource_type = ResourceType[resource_type]
            except (KeyError, AttributeError):
                resource_type = ResourceType.SLURM
        elif isinstance(resource_type, int):
            try:
                resource_type = ResourceType(resource_type)
            except (ValueError, AttributeError):
                resource_type = ResourceType.SLURM

        data['resourceType'] = resource_type

        specific_prefs = data.pop('specificPreferences', None)

        slurm_data = {}
        aws_data = {}

        slurm_fields = ['allocationProjectNumber', 'preferredBatchQueue', 'qualityOfService',
                       'usageReportingGatewayId', 'sshAccountProvisioner',
                       'groupSSHAccountProvisionerConfigs', 'sshAccountProvisionerAdditionalInfo',
                       'reservations']
        aws_fields = ['region', 'preferredAmiId', 'preferredInstanceType']

        for field in slurm_fields:
            if field in data:
                slurm_data[field] = data.pop(field)
        for field in aws_fields:
            if field in data:
                aws_data[field] = data.pop(field)

        thrift_spec = GroupComputeResourcePreference.thrift_spec
        for field_spec in thrift_spec:
            if field_spec:
                field_name = field_spec[2]
                default_value = field_spec[4]
                if default_value is not None:
                    if field_name in data and data[field_name] is None:
                        del data[field_name]

        instance = GroupComputeResourcePreference(**data)

        instance.resourceType = resource_type

        union_type_class = None
        try:
            from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                EnvironmentSpecificPreferences
            )
            union_type_class = EnvironmentSpecificPreferences
        except ImportError as e:
            log.error(
                "GCPreference create: Failed to import EnvironmentSpecificPreferences: %s",
                str(e),
                exc_info=True,
            )

        if specific_prefs is None:
            if resource_type == ResourceType.SLURM and slurm_data:
                from collections import OrderedDict
                from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                    GroupAccountSSHProvisionerConfig
                )

                if 'reservations' in slurm_data and slurm_data['reservations']:
                    reservations_list = slurm_data['reservations']
                    if isinstance(reservations_list, list):
                        converted_reservations = []
                        for res in reservations_list:
                            if isinstance(res, (dict, OrderedDict)):
                                converted_reservations.append(ComputeResourceReservation(**res))
                            else:
                                converted_reservations.append(res)
                        slurm_data['reservations'] = converted_reservations

                if 'groupSSHAccountProvisionerConfigs' in slurm_data and slurm_data['groupSSHAccountProvisionerConfigs']:
                    configs_list = slurm_data['groupSSHAccountProvisionerConfigs']
                    if isinstance(configs_list, list):
                        converted_configs = []
                        for cfg in configs_list:
                            if isinstance(cfg, (dict, OrderedDict)):
                                converted_configs.append(GroupAccountSSHProvisionerConfig(**cfg))
                            else:
                                converted_configs.append(cfg)
                        slurm_data['groupSSHAccountProvisionerConfigs'] = converted_configs

                slurm_pref = SlurmComputeResourcePreference(**slurm_data)
                if union_type_class:
                    instance.specificPreferences = union_type_class()
                    instance.specificPreferences.slurm = slurm_pref
                else:
                    try:
                        test_instance = GroupComputeResourcePreference(resourceType=resource_type)
                        if test_instance.specificPreferences is not None:
                            instance.specificPreferences = type(test_instance.specificPreferences)()
                            instance.specificPreferences.slurm = slurm_pref
                        else:
                            log.warning(
                                "GCPreference create: Could not create union type, instance may be invalid"
                            )
                    except Exception as e:
                        log.error(
                            "GCPreference create: Failed to set specificPreferences.slurm: %s",
                            str(e),
                            exc_info=True,
                        )
            elif resource_type == ResourceType.AWS and aws_data:
                aws_pref = AwsComputeResourcePreference(**aws_data)
                if union_type_class:
                    instance.specificPreferences = union_type_class()
                    instance.specificPreferences.aws = aws_pref
                else:
                    try:
                        test_instance = GroupComputeResourcePreference(resourceType=resource_type)
                        if test_instance.specificPreferences is not None:
                            instance.specificPreferences = type(test_instance.specificPreferences)()
                            instance.specificPreferences.aws = aws_pref
                    except Exception as e:
                        log.error(
                            "GCPreference create: Failed to set specificPreferences.aws: %s",
                            str(e),
                            exc_info=True,
                        )
        elif isinstance(specific_prefs, dict):
            if 'slurm' in specific_prefs:
                slurm_dict = specific_prefs['slurm'].copy() if isinstance(specific_prefs['slurm'], dict) else {}
                slurm_dict.update(slurm_data)
                from collections import OrderedDict
                from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                    GroupAccountSSHProvisionerConfig
                )

                if 'reservations' in slurm_dict and slurm_dict['reservations']:
                    reservations_list = slurm_dict['reservations']
                    if isinstance(reservations_list, list):
                        converted_reservations = []
                        for res in reservations_list:
                            if isinstance(res, (dict, OrderedDict)):
                                converted_reservations.append(ComputeResourceReservation(**res))
                            else:
                                converted_reservations.append(res)
                        slurm_dict['reservations'] = converted_reservations

                if 'groupSSHAccountProvisionerConfigs' in slurm_dict and slurm_dict['groupSSHAccountProvisionerConfigs']:
                    configs_list = slurm_dict['groupSSHAccountProvisionerConfigs']
                    if isinstance(configs_list, list):
                        converted_configs = []
                        for cfg in configs_list:
                            if isinstance(cfg, (dict, OrderedDict)):
                                converted_configs.append(GroupAccountSSHProvisionerConfig(**cfg))
                            else:
                                converted_configs.append(cfg)
                        slurm_dict['groupSSHAccountProvisionerConfigs'] = converted_configs

                slurm_pref = SlurmComputeResourcePreference(**slurm_dict)
                if union_type_class:
                    instance.specificPreferences = union_type_class()
                    instance.specificPreferences.slurm = slurm_pref
            elif 'aws' in specific_prefs:
                aws_pref = AwsComputeResourcePreference(**specific_prefs['aws'])
                if union_type_class:
                    instance.specificPreferences = union_type_class()
                    instance.specificPreferences.aws = aws_pref
            elif slurm_data:
                from collections import OrderedDict
                from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                    GroupAccountSSHProvisionerConfig
                )

                if 'reservations' in slurm_data and slurm_data['reservations']:
                    reservations_list = slurm_data['reservations']
                    if isinstance(reservations_list, list):
                        converted_reservations = []
                        for res in reservations_list:
                            if isinstance(res, (dict, OrderedDict)):
                                converted_reservations.append(ComputeResourceReservation(**res))
                            else:
                                converted_reservations.append(res)
                        slurm_data['reservations'] = converted_reservations

                if 'groupSSHAccountProvisionerConfigs' in slurm_data and slurm_data['groupSSHAccountProvisionerConfigs']:
                    configs_list = slurm_data['groupSSHAccountProvisionerConfigs']
                    if isinstance(configs_list, list):
                        converted_configs = []
                        for cfg in configs_list:
                            if isinstance(cfg, (dict, OrderedDict)):
                                converted_configs.append(GroupAccountSSHProvisionerConfig(**cfg))
                            else:
                                converted_configs.append(cfg)
                        slurm_data['groupSSHAccountProvisionerConfigs'] = converted_configs

                slurm_pref = SlurmComputeResourcePreference(**slurm_data)
                if union_type_class:
                    instance.specificPreferences = union_type_class()
                    instance.specificPreferences.slurm = slurm_pref

        if not hasattr(instance, 'resourceType') or instance.resourceType is None:
            if hasattr(instance, 'specificPreferences') and instance.specificPreferences:
                from collections import OrderedDict
                if isinstance(instance.specificPreferences, (dict, OrderedDict)):
                    if 'slurm' in instance.specificPreferences or 'allocationProjectNumber' in instance.specificPreferences:
                        instance.resourceType = ResourceType.SLURM
                    elif 'aws' in instance.specificPreferences or 'region' in instance.specificPreferences:
                        instance.resourceType = ResourceType.AWS
                    else:
                        instance.resourceType = ResourceType.SLURM
                elif hasattr(instance.specificPreferences, 'slurm') and instance.specificPreferences.slurm:
                    instance.resourceType = ResourceType.SLURM
                elif hasattr(instance.specificPreferences, 'aws') and instance.specificPreferences.aws:
                    instance.resourceType = ResourceType.AWS
                else:
                    instance.resourceType = ResourceType.SLURM
            else:
                instance.resourceType = ResourceType.SLURM
            log.warning(
                "GCPreference create: Had to set resourceType=%s at end of create(), computeResourceId=%s",
                instance.resourceType.name if hasattr(instance.resourceType, 'name') else instance.resourceType,
                instance.computeResourceId if hasattr(instance, 'computeResourceId') else 'unknown',
            )

        if hasattr(instance, 'resourceType') and instance.resourceType:
            if instance.specificPreferences is None:
                try:
                    from airavata.model.appcatalog.groupresourceprofile.ttypes import (
                        EnvironmentSpecificPreferences
                    )
                    instance.specificPreferences = EnvironmentSpecificPreferences()
                    log.debug(
                        "GCPreference create: Initialized empty specificPreferences union type, computeResourceId=%s",
                        instance.computeResourceId if hasattr(instance, 'computeResourceId') else 'unknown',
                    )
                except ImportError as e:
                    log.warning(
                        "GCPreference create: Could not initialize empty specificPreferences: %s",
                        str(e),
                    )
            self._convert_specific_preferences_dict_to_thrift(instance, instance.resourceType)

        return instance


class GroupResourceProfileSerializer(
    thrift_utils.create_serializer_class(GroupResourceProfile)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:group-resource-profile-detail',
        lookup_field='groupResourceProfileId',
        lookup_url_kwarg='group_resource_profile_id')
    creationTime = UTCPosixTimestampDateTimeField(allow_null=True)
    updatedTime = UTCPosixTimestampDateTimeField(allow_null=True)
    userHasWriteAccess = serializers.SerializerMethodField()
    computePreferences = GroupComputeResourcePreferenceSerializer(many=True)

    class Meta:
        required = ('groupResourceProfileName',)

    def create(self, validated_data):
        """
        Override create() to preserve Thrift instances in computePreferences.
        """
        compute_prefs = validated_data.get('computePreferences')
        if compute_prefs:
            all_thrift_instances = all(
                isinstance(item, GroupComputeResourcePreference)
                for item in compute_prefs
            )
            if all_thrift_instances:
                validated_data_copy = copy.deepcopy(validated_data)
                validated_data_copy['computePreferences'] = []

                params = self.process_nested_fields(validated_data_copy)
                params['computePreferences'] = [copy.deepcopy(pref) for pref in compute_prefs]

                thrift_spec = GroupResourceProfile.thrift_spec
                for field_spec in thrift_spec:
                    if field_spec:
                        field_name = field_spec[2]
                        default_value = field_spec[4]
                        if default_value is not None:
                            if field_name in params and params[field_name] is None:
                                del params[field_name]

                return GroupResourceProfile(**params)

        params = self.process_nested_fields(validated_data)

        if 'computePreferences' in params and params['computePreferences']:
            compute_prefs = params['computePreferences']
            processed_compute_prefs = []
            for pref in compute_prefs:
                if isinstance(pref, GroupComputeResourcePreference):
                    processed_compute_prefs.append(pref)
                elif isinstance(pref, dict):
                    serializer = GroupComputeResourcePreferenceSerializer()
                    try:
                        log.debug(
                            "GCPreference create: Converting dict to Thrift instance, computeResourceId=%s",
                            pref.get('computeResourceId', 'unknown'),
                        )
                        thrift_pref = serializer.create(pref)
                        if isinstance(thrift_pref, GroupComputeResourcePreference):
                            log.debug(
                                "GCPreference create: Successfully created Thrift instance, computeResourceId=%s resourceType=%s",
                                thrift_pref.computeResourceId if hasattr(thrift_pref, 'computeResourceId') else 'unknown',
                                getattr(thrift_pref, 'resourceType', None),
                            )
                            processed_compute_prefs.append(thrift_pref)
                        else:
                            log.warning(
                                "GCPreference create: serializer.create() returned non-Thrift instance: %s, type=%s",
                                pref.get('computeResourceId', 'unknown'),
                                type(thrift_pref).__name__,
                            )
                            raise ValueError(f"serializer.create() returned {type(thrift_pref).__name__}, expected GroupComputeResourcePreference")
                    except Exception as e:
                        log.warning(
                            "GCPreference create: Failed to convert dict to Thrift instance using serializer.create(): %s, trying direct construction",
                            str(e),
                            exc_info=True,
                        )
                        pref_copy = copy.deepcopy(pref)
                        if 'resourceType' not in pref_copy or pref_copy.get('resourceType') is None:
                            if 'allocationProjectNumber' in pref_copy:
                                pref_copy['resourceType'] = ResourceType.SLURM
                            elif 'region' in pref_copy or 'preferredAmiId' in pref_copy:
                                pref_copy['resourceType'] = ResourceType.AWS
                            else:
                                pref_copy['resourceType'] = ResourceType.SLURM  # Default
                        try:
                            processed_compute_prefs.append(GroupComputeResourcePreference(**pref_copy))
                        except Exception as e2:
                            log.error(
                                "GCPreference create: Failed to create Thrift instance directly: %s",
                                str(e2),
                                exc_info=True,
                            )
                            processed_compute_prefs.append(pref)
                else:
                    processed_compute_prefs.append(pref)
            params['computePreferences'] = processed_compute_prefs

        thrift_spec = GroupResourceProfile.thrift_spec
        for field_spec in thrift_spec:
            if field_spec:
                field_name = field_spec[2]
                default_value = field_spec[4]
                if default_value is not None:
                    if field_name in params and params[field_name] is None:
                        del params[field_name]

        return GroupResourceProfile(**params)

    def process_nested_fields(self, validated_data):
        compute_prefs = validated_data.get('computePreferences')
        if compute_prefs is None or compute_prefs == []:
            validated_data_copy = copy.deepcopy(validated_data)
            validated_data_copy.pop('computePreferences', None)
            params = self._process_nested_fields_base(validated_data_copy)
            params['computePreferences'] = compute_prefs if compute_prefs is not None else []
            return params

        if compute_prefs and all(isinstance(item, GroupComputeResourcePreference) for item in compute_prefs):
            validated_data_copy = copy.deepcopy(validated_data)
            validated_data_copy.pop('computePreferences', None)
            params = self._process_nested_fields_base(validated_data_copy)
            params['computePreferences'] = compute_prefs
            return params

        return self._process_nested_fields_base(validated_data)

    def _process_nested_fields_base(self, validated_data):
        from rest_framework.serializers import ListField, ListSerializer, Serializer
        if not isinstance(validated_data, dict):
            return validated_data

        params = copy.deepcopy(validated_data)
        fields = self.fields

        for field_name, serializer in fields.items():
            if (isinstance(serializer, ListField) or isinstance(serializer, ListSerializer)):
                if (params.get(field_name, None) is not None or not serializer.allow_null):
                    if isinstance(serializer.child, Serializer):
                        items = params[field_name]
                        if items and all(not isinstance(item, dict) for item in items):
                            continue

                        if field_name == 'experimentInputs' and 'type' in serializer.child.fields:
                            for item in params[field_name]:
                                if isinstance(item, dict) and 'type' in item and isinstance(item['type'], int):
                                    item['type'] = DataType(item['type'])
                        elif field_name == 'experimentOutputs' and 'type' in serializer.child.fields:
                            for item in params[field_name]:
                                if isinstance(item, dict) and 'type' in item and isinstance(item['type'], int):
                                    item['type'] = DataType(item['type'])
                        elif field_name == 'experimentStatus' and 'state' in serializer.child.fields:
                            for item in params[field_name]:
                                if isinstance(item, dict) and 'state' in item and isinstance(item['state'], int):
                                    item['state'] = ExperimentState(item['state'])

                        processed_items = []
                        for item in params[field_name]:
                            if isinstance(item, dict):
                                if hasattr(serializer.child, 'create'):
                                    try:
                                        processed_items.append(serializer.child.create(item))
                                    except NotImplementedError:
                                        processed_items.append(item)
                                else:
                                    processed_items.append(item)
                            else:
                                processed_items.append(item)
                        params[field_name] = processed_items
                    else:
                        params[field_name] = serializer.to_representation(params[field_name])
            elif isinstance(serializer, Serializer):
                if field_name in params and params[field_name] is not None:
                    if not isinstance(params[field_name], dict):
                        continue
                    if hasattr(serializer, 'create'):
                        try:
                            params[field_name] = serializer.create(params[field_name])
                        except NotImplementedError:
                            pass

        return params

    def update(self, instance, validated_data):
        # Merge existing computePreferences with incoming data to preserve fields that aren't being updated
        if 'computePreferences' in validated_data and instance.computePreferences:
            existing_prefs_by_id = {
                pref.computeResourceId: pref
                for pref in instance.computePreferences
                if hasattr(pref, 'computeResourceId')
            }

            for incoming_pref in validated_data['computePreferences']:
                if isinstance(incoming_pref, dict):
                    compute_resource_id = incoming_pref.get('computeResourceId')
                    if compute_resource_id and compute_resource_id in existing_prefs_by_id:
                        existing_pref = existing_prefs_by_id[compute_resource_id]
                        if 'specificPreferences' in incoming_pref and isinstance(incoming_pref['specificPreferences'], dict):
                            if 'slurm' in incoming_pref['specificPreferences']:
                                incoming_slurm = incoming_pref['specificPreferences']['slurm']
                                if isinstance(incoming_slurm, dict):
                                    existing_slurm = None
                                    if (hasattr(existing_pref, 'specificPreferences') and
                                        existing_pref.specificPreferences and
                                        hasattr(existing_pref.specificPreferences, 'slurm') and
                                        existing_pref.specificPreferences.slurm):
                                        existing_slurm = existing_pref.specificPreferences.slurm

                                    simple_string_fields = [
                                        'preferredBatchQueue',
                                        'qualityOfService',
                                        'usageReportingGatewayId',
                                        'sshAccountProvisioner',
                                        'sshAccountProvisionerAdditionalInfo',
                                    ]
                                    for field in simple_string_fields:
                                        if incoming_slurm.get(field) is None and existing_slurm:
                                            existing_value = getattr(existing_slurm, field, None)
                                            if existing_value is not None:
                                                incoming_slurm[field] = existing_value
                                                log.debug(
                                                    "GCPreference update: Preserved existing %s=%s for computeResourceId=%s",
                                                    field,
                                                    existing_value,
                                                    compute_resource_id,
                                                )

                                    list_fields = [
                                        'groupSSHAccountProvisionerConfigs',
                                        'reservations',
                                    ]
                                    for field in list_fields:
                                        if incoming_slurm.get(field) is None and existing_slurm:
                                            existing_value = getattr(existing_slurm, field, None)
                                            if existing_value is not None and isinstance(existing_value, list) and len(existing_value) > 0:
                                                converted_list = []
                                                for item in existing_value:
                                                    if hasattr(item, '__dict__'):
                                                        if field == 'reservations':
                                                            try:
                                                                serializer = ComputeResourceReservationSerializer()
                                                                converted_list.append(serializer.to_representation(item))
                                                            except Exception as e:
                                                                log.warning(
                                                                    "GCPreference update: Could not serialize reservation item: %s",
                                                                    str(e),
                                                                )
                                                                item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                                                                converted_list.append(item_dict)
                                                        else:
                                                            item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                                                            converted_list.append(item_dict)
                                                    else:
                                                        converted_list.append(item)
                                                incoming_slurm[field] = converted_list
                                                log.debug(
                                                    "GCPreference update: Preserved existing %s (list with %d items) for computeResourceId=%s",
                                                    field,
                                                    len(converted_list),
                                                    compute_resource_id,
                                                )

        if 'computeResourcePolicies' in validated_data and instance.computeResourcePolicies:
            existing_policies_by_resource_id = {
                pol.computeResourceId: pol
                for pol in instance.computeResourcePolicies
                if hasattr(pol, 'computeResourceId') and hasattr(pol, 'resourcePolicyId')
            }

            for incoming_policy in validated_data['computeResourcePolicies']:
                if isinstance(incoming_policy, dict):
                    compute_resource_id = incoming_policy.get('computeResourceId')
                    if compute_resource_id and compute_resource_id in existing_policies_by_resource_id:
                        existing_policy = existing_policies_by_resource_id[compute_resource_id]
                        if 'resourcePolicyId' not in incoming_policy or incoming_policy.get('resourcePolicyId') is None:
                            incoming_policy['resourcePolicyId'] = existing_policy.resourcePolicyId
                            log.debug(
                                "GCPreference update: Preserved existing resourcePolicyId=%s for computeResourceId=%s",
                                existing_policy.resourcePolicyId,
                                compute_resource_id,
                            )

        if 'batchQueueResourcePolicies' in validated_data and instance.batchQueueResourcePolicies:
            existing_bq_policies_by_key = {}
            for pol in instance.batchQueueResourcePolicies:
                if hasattr(pol, 'computeResourceId') and hasattr(pol, 'queuename') and hasattr(pol, 'resourcePolicyId'):
                    key = (pol.computeResourceId, pol.queuename)
                    existing_bq_policies_by_key[key] = pol

            for incoming_bq_policy in validated_data['batchQueueResourcePolicies']:
                if isinstance(incoming_bq_policy, dict):
                    compute_resource_id = incoming_bq_policy.get('computeResourceId')
                    queuename = incoming_bq_policy.get('queuename')
                    if compute_resource_id and queuename:
                        key = (compute_resource_id, queuename)
                        if key in existing_bq_policies_by_key:
                            existing_bq_policy = existing_bq_policies_by_key[key]
                            if 'resourcePolicyId' not in incoming_bq_policy or incoming_bq_policy.get('resourcePolicyId') is None:
                                incoming_bq_policy['resourcePolicyId'] = existing_bq_policy.resourcePolicyId
                                log.debug(
                                    "GCPreference update: Preserved existing resourcePolicyId=%s for batchQueueResourcePolicy computeResourceId=%s queuename=%s",
                                    existing_bq_policy.resourcePolicyId,
                                    compute_resource_id,
                                    queuename,
                                )

        result = self.create(validated_data)
        result._removed_compute_resource_preferences = []
        result._removed_compute_resource_policies = []
        result._removed_batch_queue_resource_policies = []
        # Find all compute resource preferences that were removed
        for compute_resource_preference in instance.computePreferences:
            existing_compute_resource_preference = None
            for pref in result.computePreferences:
                if isinstance(pref, GroupComputeResourcePreference):
                    pref_id = pref.computeResourceId
                elif isinstance(pref, dict):
                    pref_id = pref.get('computeResourceId')
                else:
                    continue
                if pref_id == compute_resource_preference.computeResourceId:
                    existing_compute_resource_preference = pref
                    break
            if not existing_compute_resource_preference:
                result._removed_compute_resource_preferences.append(
                    compute_resource_preference)
        # Find all compute resource policies that were removed
        for compute_resource_policy in instance.computeResourcePolicies:
            existing_compute_resource_policy = None
            for pol in result.computeResourcePolicies:
                if hasattr(pol, 'resourcePolicyId'):
                    pol_id = pol.resourcePolicyId
                elif isinstance(pol, dict):
                    pol_id = pol.get('resourcePolicyId')
                else:
                    continue
                if pol_id == compute_resource_policy.resourcePolicyId:
                    existing_compute_resource_policy = pol
                    break
            if not existing_compute_resource_policy:
                result._removed_compute_resource_policies.append(
                    compute_resource_policy)
        # Find all batch queue resource policies that were removed
        for batch_queue_resource_policy in instance.batchQueueResourcePolicies:
            existing_batch_queue_resource_policy_for_update = None
            for bq in result.batchQueueResourcePolicies:
                if hasattr(bq, 'resourcePolicyId'):
                    bq_id = bq.resourcePolicyId
                elif isinstance(bq, dict):
                    bq_id = bq.get('resourcePolicyId')
                else:
                    continue
                if bq_id == batch_queue_resource_policy.resourcePolicyId:
                    existing_batch_queue_resource_policy_for_update = bq
                    break
            if not existing_batch_queue_resource_policy_for_update:
                result._removed_batch_queue_resource_policies.append(
                    batch_queue_resource_policy)
        return result

    def get_userHasWriteAccess(self, groupResourceProfile):
        request = self.context['request']
        write_access = user_has_access(
            request, groupResourceProfile.groupResourceProfileId, "WRITE")
        if not write_access:
            return False
        # Check that user has READ access to all tokens in this
        # GroupResourceProfile
        tokens = set([groupResourceProfile.defaultCredentialStoreToken] +
                     [cp.resourceSpecificCredentialStoreToken
                      for cp in groupResourceProfile.computePreferences])

        def check_token(token):
            return token is None or user_has_access(request, token, "READ")

        return all(map(check_token, tokens))


class UserPermissionSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    permissionType = serializers.IntegerField()


class GroupPermissionSerializer(serializers.Serializer):
    group = GroupSerializer()
    permissionType = serializers.IntegerField()


class SharedEntitySerializer(serializers.Serializer):
    entityId = serializers.CharField(read_only=True)
    userPermissions = UserPermissionSerializer(many=True)
    groupPermissions = GroupPermissionSerializer(many=True)
    owner = UserProfileSerializer(read_only=True)
    isOwner = serializers.SerializerMethodField()
    hasSharingPermission = serializers.SerializerMethodField()

    def create(self, validated_data):
        raise Exception("Not implemented")

    def update(self, instance, validated_data):
        # Compute lists of ids to grant/revoke READ/WRITE/MANAGE_SHARING
        # permission
        existing_user_permissions = {
            user['user'].airavataInternalUserId: user['permissionType']
            for user in instance['userPermissions']}
        new_user_permissions = {
            user['user']['airavataInternalUserId']:
                user['permissionType']
            for user in validated_data['userPermissions']}

        (
            user_grant_read_permission,
            user_grant_write_permission,
            user_grant_manage_sharing_permission,
            user_revoke_read_permission,
            user_revoke_write_permission,
            user_revoke_manage_sharing_permission) = self._compute_all_revokes_and_grants(
            existing_user_permissions,
            new_user_permissions)

        existing_group_permissions = {
            group['group'].id: group['permissionType']
            for group in instance['groupPermissions']}
        new_group_permissions = {
            group['group']['id']: group['permissionType']
            for group in validated_data['groupPermissions']}

        (
            group_grant_read_permission,
            group_grant_write_permission,
            group_grant_manage_sharing_permission,
            group_revoke_read_permission,
            group_revoke_write_permission,
            group_revoke_manage_sharing_permission) = self._compute_all_revokes_and_grants(
            existing_group_permissions,
            new_group_permissions)

        instance['_user_grant_read_permission'] = user_grant_read_permission
        instance['_user_grant_write_permission'] = user_grant_write_permission
        instance['_user_grant_manage_sharing_permission'] = user_grant_manage_sharing_permission
        instance['_user_revoke_read_permission'] = user_revoke_read_permission
        instance['_user_revoke_write_permission'] = user_revoke_write_permission
        instance['_user_revoke_manage_sharing_permission'] = user_revoke_manage_sharing_permission
        instance['_group_grant_read_permission'] = group_grant_read_permission
        instance['_group_grant_write_permission'] = group_grant_write_permission
        instance['_group_grant_manage_sharing_permission'] = group_grant_manage_sharing_permission
        instance['_group_revoke_read_permission'] = group_revoke_read_permission
        instance['_group_revoke_write_permission'] = group_revoke_write_permission
        instance['_group_revoke_manage_sharing_permission'] = group_revoke_manage_sharing_permission
        instance['userPermissions'] = [
            {'user': UserProfile(**data['user']),
             'permissionType': data['permissionType']}
            for data in validated_data.get(
                'userPermissions', instance['userPermissions'])]
        instance['groupPermissions'] = [
            {'group': GroupModel(**data['group']),
             'permissionType': data['permissionType']}
            for data in validated_data.get('groupPermissions', instance['groupPermissions'])]
        return instance

    def _compute_all_revokes_and_grants(self, existing_permissions,
                                        new_permissions):
        grant_read_permission = []
        grant_write_permission = []
        grant_manage_sharing_permission = []
        revoke_read_permission = []
        revoke_write_permission = []
        revoke_manage_sharing_permission = []
        # Union the two sets of user/group ids
        all_ids = existing_permissions.keys() | new_permissions.keys()
        for id in all_ids:
            revokes, grants = self._compute_revokes_and_grants(
                existing_permissions.get(id),
                new_permissions.get(id)
            )
            if ResourcePermissionType.READ in revokes:
                revoke_read_permission.append(id)
            if ResourcePermissionType.WRITE in revokes:
                revoke_write_permission.append(id)
            if ResourcePermissionType.MANAGE_SHARING in revokes:
                revoke_manage_sharing_permission.append(id)
            if ResourcePermissionType.READ in grants:
                grant_read_permission.append(id)
            if ResourcePermissionType.WRITE in grants:
                grant_write_permission.append(id)
            if ResourcePermissionType.MANAGE_SHARING in grants:
                grant_manage_sharing_permission.append(id)
        return (
            grant_read_permission,
            grant_write_permission,
            grant_manage_sharing_permission,
            revoke_read_permission,
            revoke_write_permission,
            revoke_manage_sharing_permission)

    def _compute_revokes_and_grants(self, current_permission=None,
                                    new_permission=None):
        read_permissions = set((ResourcePermissionType.READ,))
        write_permissions = set((ResourcePermissionType.READ,
                                 ResourcePermissionType.WRITE))
        manage_share_permissions = set(
            (ResourcePermissionType.READ,
             ResourcePermissionType.WRITE,
             ResourcePermissionType.MANAGE_SHARING))
        current_permissions_set = set()
        new_permissions_set = set()
        if current_permission == ResourcePermissionType.READ:
            current_permissions_set = read_permissions
        elif current_permission == ResourcePermissionType.WRITE:
            current_permissions_set = write_permissions
        elif current_permission == ResourcePermissionType.MANAGE_SHARING:
            current_permissions_set = manage_share_permissions
        if new_permission == ResourcePermissionType.READ:
            new_permissions_set = read_permissions
        elif new_permission == ResourcePermissionType.WRITE:
            new_permissions_set = write_permissions
        elif new_permission == ResourcePermissionType.MANAGE_SHARING:
            new_permissions_set = manage_share_permissions

        # return tuple: permissions to revoke and permissions to grant
        return (current_permissions_set - new_permissions_set,
                new_permissions_set - current_permissions_set)

    def get_isOwner(self, shared_entity):
        request = self.context['request']
        return shared_entity['owner'].userId == request.user.username

    def get_hasSharingPermission(self, shared_entity):
        request = self.context['request']
        return user_has_access(
            request, shared_entity['entityId'], "MANAGE_SHARING")


def _credential_store_pb2():
    from airavata_sdk.generated.org.apache.airavata.model.credential.store import (
        credential_store_pb2,
    )
    return credential_store_pb2


class CredentialSummarySerializer(serializers.Serializer):
    """Proto-native serializer for the gRPC ``CredentialSummary`` message."""

    type = proto_enum_name_field(
        _credential_store_pb2().SummaryType.DESCRIPTOR, read_only=True)
    gatewayId = serializers.CharField(source='gateway_id', read_only=True)
    username = serializers.CharField(read_only=True)
    publicKey = serializers.CharField(source='public_key', read_only=True)
    persistedTime = ProtoTimestampField(
        source='persisted_time', read_only=True)
    token = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, credential_summary):
        return user_has_access(
            self.context['request'], credential_summary.token)


class StoragePreferenceSerializer(
        thrift_utils.create_serializer_class(StoragePreference)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:storage-preference-detail',
        lookup_field='storageResourceId',
        lookup_url_kwarg='storage_resource_id')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Convert empty string to null
        if ret['resourceSpecificCredentialStoreToken'] == '':
            ret['resourceSpecificCredentialStoreToken'] = None
        return ret


class GatewayResourceProfileSerializer(
        thrift_utils.create_serializer_class(GatewayResourceProfile)):
    storagePreferences = StoragePreferenceSerializer(many=True)
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, gatewayResourceProfile):
        request = self.context['request']
        return request.is_gateway_admin


class StorageResourceSerializer(
        thrift_utils.create_serializer_class(StorageResourceDescription)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:storage-resource-detail',
        lookup_field='storageResourceId',
        lookup_url_kwarg='storage_resource_id')
    creationTime = UTCPosixTimestampDateTimeField()
    updateTime = UTCPosixTimestampDateTimeField()


class ParserSerializer(thrift_utils.create_serializer_class(Parser)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:parser-detail',
        lookup_field='id',
        lookup_url_kwarg='parser_id')


class UserHasWriteAccessToPathSerializer(serializers.Serializer):
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, instance):
        request = self.context['request']
        if "userHasWriteAccess" in instance:
            return instance["userHasWriteAccess"]
        is_shared_path = view_utils.is_shared_path(instance["path"])
        if is_shared_path:
            return request.is_gateway_admin
        else:
            return True


class UserStorageFileSerializer(UserHasWriteAccessToPathSerializer):
    name = serializers.CharField()
    downloadURL = serializers.SerializerMethodField()
    dataProductURI = serializers.CharField(source='data-product-uri')
    createdTime = serializers.DateTimeField(source='created_time')
    modifiedTime = serializers.DateTimeField(source='modified_time')
    mimeType = serializers.CharField(source='mime_type')
    size = serializers.IntegerField()
    hidden = serializers.BooleanField()

    def get_downloadURL(self, file):
        """Lazy portal URL to the byte-streaming download endpoint for this file.

        Returns None when the file has no data product URI; resolving the bytes is
        deferred to the endpoint, so this getter makes no backend call.
        """
        request = self.context['request']
        data_product_uri = file.get('data-product-uri')
        if not data_product_uri:
            return None
        base = request.build_absolute_uri(
            reverse('django_airavata_api:download-file'))
        return base + '?data-product-uri=' + quote(data_product_uri)


class UserStorageDirectorySerializer(UserHasWriteAccessToPathSerializer):
    name = serializers.CharField()
    path = serializers.CharField()
    createdTime = serializers.DateTimeField(source='created_time')
    modifiedTime = serializers.DateTimeField(source='modified_time')
    size = serializers.IntegerField()
    hidden = serializers.BooleanField()
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:user-storage-items',
        lookup_field='path',
        lookup_url_kwarg='path')
    isSharedDir = serializers.SerializerMethodField()

    def get_isSharedDir(self, directory):
        if "isSharedDir" in directory:
            return directory["isSharedDir"]
        return view_utils.is_shared_dir(directory["path"])


class UserStoragePathSerializer(UserHasWriteAccessToPathSerializer):
    isDir = serializers.BooleanField()
    directories = UserStorageDirectorySerializer(many=True)
    files = UserStorageFileSerializer(many=True)
    parts = serializers.ListField(child=serializers.CharField())
    path = serializers.CharField(required=False)
    # uploaded is populated after a file upload
    uploaded = DataProductSerializer(read_only=True)


# Fields for ExperimentStorageFileSerializer are the same as UserStorageFileSerializer
ExperimentStorageFileSerializer = UserStorageFileSerializer


class ExperimentStorageDirectorySerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    createdTime = serializers.DateTimeField(source='created_time')
    modifiedTime = serializers.DateTimeField(source='modified_time')
    size = serializers.IntegerField()
    url = serializers.SerializerMethodField()

    def get_url(self, dir):

        request = self.context['request']
        return request.build_absolute_uri(
            reverse("django_airavata_api:experiment-storage-items", kwargs={
                "experiment_id": dir['experiment_id'],
                "path": dir['path']
            }))


class ExperimentStoragePathSerializer(serializers.Serializer):
    isDir = serializers.BooleanField()
    directories = ExperimentStorageDirectorySerializer(many=True)
    files = ExperimentStorageFileSerializer(many=True)
    parts = serializers.ListField(child=serializers.CharField())


# ModelSerializers
class ApplicationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApplicationPreferences
        exclude = ('id', 'username', 'workspace_preferences')


class WorkspacePreferencesSerializer(serializers.ModelSerializer):
    application_preferences = ApplicationPreferencesSerializer(
        source="applicationpreferences_set", many=True)

    class Meta:
        model = models.WorkspacePreferences
        exclude = ('username',)


class IAMUserProfile(serializers.Serializer):
    airavataInternalUserId = serializers.CharField()
    userId = serializers.CharField()
    gatewayId = serializers.CharField()
    email = serializers.CharField()
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    enabled = serializers.BooleanField()
    emailVerified = serializers.BooleanField()
    airavataUserProfileExists = serializers.BooleanField()
    creationTime = UTCPosixTimestampDateTimeField()
    groups = GroupSerializer(many=True)
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:iam-user-profile-detail',
        lookup_field='userId',
        lookup_url_kwarg='user_id')
    userHasWriteAccess = serializers.SerializerMethodField()
    newUsername = serializers.CharField(write_only=True, required=False)
    externalIDPUserInfo = serializers.SerializerMethodField()
    userProfileInvalidFields = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        existing_group_ids = [group.id for group in instance['groups']]
        new_group_ids = [group['id'] for group in validated_data['groups']]
        instance['_added_group_ids'] = list(
            set(new_group_ids) - set(existing_group_ids))
        instance['_removed_group_ids'] = list(
            set(existing_group_ids) - set(new_group_ids))
        return instance

    def get_userHasWriteAccess(self, userProfile):
        request = self.context['request']
        return request.is_gateway_admin

    def get_externalIDPUserInfo(self, userProfile):
        result = {}
        try:
            if get_user_model().objects.filter(username=userProfile['userId']).exists():
                django_user = get_user_model().objects.get(username=userProfile['userId'])
                claims = django_user.user_profile.idp_userinfo.all()
                if claims.exists():
                    result['idp_alias'] = claims.first().idp_alias
                    result['userinfo'] = {}
                for claim in claims:
                    result['userinfo'][claim.claim] = claim.value
        except Exception as e:
            log.warning(f"Failed to load idp_userinfo for {userProfile['userId']}", exc_info=e)
        return result

    def get_userProfileInvalidFields(self, userProfile):
        try:
            User = get_user_model()
            if User.objects.filter(username=userProfile['userId']).exists():
                django_user = User.objects.get(username=userProfile['userId'])
                if hasattr(django_user, 'user_profile'):
                    return django_user.user_profile.invalid_fields
                else:
                    # For backwards compatibility, return True if no user_profile
                    return []
        except Exception as e:
            log.warning(f"Failed to get user_profile.invalid_fields for {userProfile['userId']}", exc_info=e)
        return []


class AckNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User_Notifications


class NotificationSerializer(thrift_utils.create_serializer_class(Notification)):
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:manage-notifications-detail',
        lookup_field='notificationId',
        lookup_url_kwarg='notification_id')
    priority = thrift_utils.ThriftEnumField(NotificationPriority)
    creationTime = UTCPosixTimestampDateTimeField(allow_null=True)
    publishedTime = UTCPosixTimestampDateTimeField()
    expirationTime = UTCPosixTimestampDateTimeField()
    userHasWriteAccess = serializers.SerializerMethodField()
    showInDashboard = serializers.BooleanField(default=False)

    def get_userHasWriteAccess(self, userProfile):
        request = self.context['request']
        return request.is_gateway_admin

    def validate(self, attrs):
        del attrs["showInDashboard"]

        return attrs

    def to_representation(self, notification):
        notification_extension_list = models.NotificationExtension.objects.filter(
            notification_id=notification.notificationId)
        setattr(notification, "showInDashboard",
                False if len(notification_extension_list) == 0 else notification_extension_list[0].showInDashboard)

        return super().to_representation(notification)

    def update_notification_extension(self, request, notification):
        if "showInDashboard" in request.data:
            existing_entries = models.NotificationExtension.objects.filter(notification_id=notification.notificationId)

            if len(existing_entries) > 0:
                existing_entries.update(
                    showInDashboard=request.data["showInDashboard"]
                )
            else:
                models.NotificationExtension.objects.create(
                    notification_id=notification.notificationId,
                    showInDashboard=request.data["showInDashboard"]
                )


class ExperimentStatisticsSerializer(
        thrift_utils.create_serializer_class(ExperimentStatistics)):
    allExperiments = BaseExperimentSummarySerializer(many=True)
    completedExperiments = BaseExperimentSummarySerializer(many=True)
    failedExperiments = BaseExperimentSummarySerializer(many=True)
    cancelledExperiments = BaseExperimentSummarySerializer(many=True)
    createdExperiments = BaseExperimentSummarySerializer(many=True)
    runningExperiments = BaseExperimentSummarySerializer(many=True)


class UnverifiedEmailUserProfile(serializers.Serializer):
    userId = serializers.CharField()
    gatewayId = serializers.CharField()
    email = serializers.CharField()
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    enabled = serializers.BooleanField()
    emailVerified = serializers.BooleanField()
    creationTime = UTCPosixTimestampDateTimeField()
    url = FullyEncodedHyperlinkedIdentityField(
        view_name='django_airavata_api:unverified-email-user-profile-detail',
        lookup_field='userId',
        lookup_url_kwarg='user_id')
    userHasWriteAccess = serializers.SerializerMethodField()

    def get_userHasWriteAccess(self, userProfile):
        request = self.context['request']
        return request.is_gateway_admin


class LogRecordSerializer(serializers.Serializer):
    level = serializers.CharField()
    message = serializers.CharField()
    details = StoredJSONField()
    stacktrace = serializers.ListField(child=serializers.CharField())


class SettingsSerializer(serializers.Serializer):
    fileUploadMaxFileSize = serializers.IntegerField()
    tusEndpoint = serializers.CharField()
    pgaUrl = serializers.CharField()


class QueueSettingsCalculatorSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
