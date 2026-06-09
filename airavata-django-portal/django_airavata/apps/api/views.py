import base64
import io
import json
import logging
import os
import warnings
from datetime import datetime, timedelta
from urllib.parse import quote

from airavata.model.appcatalog.computeresource.ttypes import (
    CloudJobSubmission,
    LOCALSubmission,
    SSHJobSubmission,
    UnicoreJobSubmission
)
from airavata.model.application.io.ttypes import DataType
from airavata.model.data.movement.ttypes import (
    GridFTPDataMovement,
    LOCALDataMovement,
    SCPDataMovement
)
from airavata.model.experiment.ttypes import (
    ExperimentModel,
    ExperimentSearchFields
)
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    GroupComputeResourcePreference,
    ResourceType
)
from airavata.model.group.ttypes import ResourcePermissionType
from airavata.model.user.ttypes import Status
from airavata_django_portal_sdk import (
    experiment_util,
    queue_settings_calculators
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.gzip import gzip_page
from rest_framework import mixins, pagination, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from django_airavata.apps.admin.models import UserDataArchiveEntry
from django_airavata.apps.api.view_utils import (
    APIBackedViewSet,
    APIResultIterator,
    APIResultPagination,
    DataProductSharedDirPermission,
    GenericAPIBackedViewSet,
    IsInAdminsGroupPermission,
    UserStorageSharedDirPermission
)
from django_airavata.apps.auth import iam_admin_client
from django_airavata.apps.auth.models import EmailVerification

from . import (
    exceptions,
    grpc_adapters,
    grpc_requests,
    helpers,
    models,
    output_views,
    serializers,
    signals,
    thrift_utils,
    tus,
    view_utils
)

READ_PERMISSION_TYPE = '{}:READ'

# Input files uploaded for an experiment are staged under this directory in the
# user's storage (mirrors the legacy SDK's TMP_INPUT_FILE_UPLOAD_DIR).
TMP_INPUT_FILE_UPLOAD_DIR = "tmp"

log = logging.getLogger(__name__)


def _storage_upload_and_register(request, dir_path, uploaded_file, name=None,
                                 content_type=None, experiment_id=None):
    """Upload a file to user storage and register a data product for it (gRPC).

    Writes the bytes via the ``storage`` facade (the path is the full file path,
    ``~/``-prefixed so the backend resolves it against the storage root, or
    relative to the experiment data dir when ``experiment_id`` is given), then
    registers a data product via the ``research`` facade so the file has a
    canonical product URI. Returns the registered data product adapted to the
    ``DataProductSerializer`` shape. Replaces the legacy
    ``user_storage.save``/``save_input_file`` (which transferred bytes and
    registered the data product in one call).
    """
    storage = request.airavata.storage
    name = name or os.path.basename(getattr(uploaded_file, 'name', '') or '')
    # Full file path resolved against the storage root (or experiment data dir).
    upload_path = _user_storage_path(
        os.path.join(dir_path, name), experiment_id, request)
    content = uploaded_file.read()
    storage.upload_file(
        path=upload_path, content=content, name=name,
        content_type=content_type or '')
    # The upload response is minimal; resolve the absolute path the backend wrote
    # to and register the full data product.
    metadata = storage.get_file_metadata(upload_path)
    product_uri = request.airavata.research.register_data_product(
        grpc_requests.data_product_for_upload(
            gateway_id=settings.GATEWAY_ID,
            owner_name=request.user.username,
            product_name=name,
            file_path=metadata.path,
            storage_resource_id=storage.get_default_storage_resource_id(),
            content_type=content_type,
            product_size=metadata.size))
    return grpc_adapters.data_product(
        request.airavata.research.get_data_product(product_uri))


class GroupViewSet(APIBackedViewSet):
    serializer_class = serializers.GroupSerializer
    lookup_field = 'group_id'
    pagination_class = APIResultPagination
    pagination_viewname = 'django_airavata_api:group-list'

    def get_list(self):
        view = self

        class GroupResultsIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                groups = [
                    grpc_adapters.group(g)
                    for g in view.request.airavata.sharing.gm_get_groups()
                ]
                end = offset + limit if limit > 0 else len(groups)
                return groups[offset:end] if groups else []

        return GroupResultsIterator()

    def get_instance(self, lookup_value):
        return grpc_adapters.group(
            self.request.airavata.sharing.gm_get_group(lookup_value))

    def perform_create(self, serializer):
        group = serializer.save()
        group_id = self.request.airavata.sharing.gm_create_group(
            grpc_requests.group(group))
        group.id = group_id
        users_added_to_group = set(group.members) - {group.ownerId}
        self._send_users_added_to_group(users_added_to_group, group)

    def perform_update(self, serializer):
        group = serializer.save()
        sharing = self.request.airavata.sharing
        if len(group._added_members) > 0:
            sharing.gm_add_users_to_group(group._added_members, group.id)
            self._send_users_added_to_group(group._added_members, group)
        if len(group._removed_members) > 0:
            sharing.gm_remove_users_from_group(group._removed_members, group.id)
        if len(group._added_admins) > 0:
            sharing.gm_add_group_admins(group.id, group._added_admins)
        if len(group._removed_admins) > 0:
            sharing.gm_remove_group_admins(group.id, group._removed_admins)
        sharing.gm_update_group(grpc_requests.group(group))

    def perform_destroy(self, group):
        self.request.airavata.sharing.gm_delete_group(group.id, group.ownerId)

    def _send_users_added_to_group(self, internal_user_ids, group):
        for internal_user_id in internal_user_ids:
            user_id, gateway_id = internal_user_id.rsplit("@", maxsplit=1)
            user_profile = self.request.airavata.iam.get_user_profile_by_id(
                user_id, gateway_id)
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=[group],
                request=self.request)


class ProjectViewSet(APIBackedViewSet):
    serializer_class = serializers.ProjectSerializer
    lookup_field = 'project_id'
    pagination_class = APIResultPagination
    pagination_viewname = 'django_airavata_api:project-list'

    def get_list(self):
        view = self

        class ProjectResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return view.request.airavata.research.get_user_projects(
                    gateway_id=view.gateway_id, user_name=view.username,
                    limit=limit, offset=offset)

        return ProjectResultIterator()

    def get_instance(self, lookup_value):
        return self.request.airavata.research.get_project(lookup_value)

    def perform_create(self, serializer):
        project = serializer.save(
            owner=self.username,
            gateway_id=self.gateway_id)
        project_id = self.request.airavata.research.create_project(
            self.gateway_id, project)
        project.project_id = project_id
        self._update_most_recent_project(project_id)

    def perform_update(self, serializer):
        project = serializer.save()
        self.request.airavata.research.update_project(
            project.project_id, project)
        self._update_most_recent_project(project.project_id)

    @action(detail=False)
    def list_all(self, request):
        projects = self.request.airavata.research.get_user_projects(
            gateway_id=self.gateway_id, user_name=self.username,
            limit=-1, offset=0)
        serializer = serializers.ProjectSerializer(
            projects, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True)
    def experiments(self, request, project_id=None):
        experiments = [
            grpc_adapters.experiment(e)
            for e in request.airavata.research.get_experiments_in_project(
                project_id, -1, 0)
        ]
        serializer = serializers.ExperimentSerializer(
            experiments, many=True, context={'request': request})
        return Response(serializer.data)

    def _update_most_recent_project(self, project_id):
        prefs = helpers.WorkspacePreferencesHelper().get(self.request)
        prefs.most_recent_project_id = project_id
        prefs.save()


class ExperimentViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        GenericAPIBackedViewSet):
    serializer_class = serializers.ExperimentSerializer
    lookup_field = 'experiment_id'

    def get_instance(self, lookup_value):
        return grpc_adapters.experiment(
            self.request.airavata.research.get_experiment(lookup_value))

    def perform_create(self, serializer):
        experiment = serializer.save(
            gatewayId=self.gateway_id,
            userName=self.username)
        experiment_id = self.request.airavata.research.create_experiment(
            self.gateway_id, grpc_requests.experiment(experiment))
        self._update_workspace_preferences(
            project_id=experiment.projectId,
            group_resource_profile_id=experiment.userConfigurationData.groupResourceProfileId,
            compute_resource_id=experiment.userConfigurationData.computationalResourceScheduling.resourceHostId)
        experiment.experimentId = experiment_id

    def perform_update(self, serializer):
        experiment = serializer.save(
            gatewayId=self.gateway_id,
            userName=self.username)
        self.request.airavata.research.update_experiment(
            experiment.experimentId, grpc_requests.experiment(experiment))
        self._update_workspace_preferences(
            project_id=experiment.projectId,
            group_resource_profile_id=experiment.userConfigurationData.groupResourceProfileId,
            compute_resource_id=experiment.userConfigurationData.computationalResourceScheduling.resourceHostId)

    @action(methods=['post'], detail=True)
    def launch(self, request, experiment_id=None):
        try:
            experiment = grpc_adapters.experiment(
                request.airavata.research.get_experiment(experiment_id))
            if (experiment.enableEmailNotification):
                experiment.emailAddresses = [request.user.email]
            request.airavata.research.update_experiment(
                experiment_id, grpc_requests.experiment(experiment))
            experiment_util.launch(request, experiment_id)
            return Response({'success': True})
        except Exception as e:
            log.exception(f"Failed to launch experiment {experiment_id}", extra={'request': request})
            return Response({'success': False, 'errorMessage': str(e)})

    @action(methods=['get'], detail=True)
    def jobs(self, request, experiment_id=None):
        jobs = [
            grpc_adapters.job_model(j)
            for j in request.airavata.research.get_job_details(experiment_id)
        ]
        serializer = serializers.JobSerializer(
            jobs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def clone(self, request, experiment_id=None):
        # experiment_util.clone is the launch/clone orchestration (still Thrift);
        # re-fetch the cloned experiment via gRPC.
        cloned_experiment_id = experiment_util.clone(request, experiment_id)
        cloned_experiment = grpc_adapters.experiment(
            request.airavata.research.get_experiment(cloned_experiment_id))
        serializer = self.serializer_class(
            cloned_experiment, context={'request': request})
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def cancel(self, request, experiment_id=None):
        try:
            request.airavata.research.terminate_experiment(
                experiment_id, self.gateway_id)
            return Response({'success': True})
        except Exception as e:
            log.exception("Cancel action has thrown the following error", extra={'request': request})
            raise e

    @action(methods=['post'], detail=True)
    def fetch_intermediate_outputs(self, request, experiment_id=None):
        if "outputNames" not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            experiment_util.intermediate_output.fetch_intermediate_output(
                request, experiment_id, *request.data["outputNames"])
            return Response({'success': True})
        except Exception as e:
            log.exception("fetchIntermediateOutputs failed with the following error", extra={'request': request})
            raise e

    def _update_workspace_preferences(self, project_id,
                                      group_resource_profile_id,
                                      compute_resource_id):
        prefs = helpers.WorkspacePreferencesHelper().get(self.request)
        prefs.most_recent_project_id = project_id
        prefs.most_recent_group_resource_profile_id = group_resource_profile_id
        prefs.most_recent_compute_resource_id = compute_resource_id
        prefs.save()


class ExperimentSearchViewSet(mixins.ListModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.ExperimentSummarySerializer
    pagination_class = APIResultPagination
    pagination_viewname = 'django_airavata_api:experiment-search-list'

    def get_list(self):
        view = self

        # gRPC SearchExperiments takes filters as a map<string, string> keyed by
        # ExperimentSearchFields member name (the query-param key already is one).
        filters = {}
        for key, value in self.request.query_params.items():
            if key in ExperimentSearchFields.__members__:
                filters[key] = value

        class ExperimentSearchResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return list(view.request.airavata.research.search_experiments(
                    gateway_id=view.gateway_id, user_name=view.username,
                    filters=filters, limit=limit, offset=offset))

        # Preserve query parameters when moving to next and previous links
        return ExperimentSearchResultIterator(query_params=self.request.query_params.copy())

    def get_instance(self, lookup_value):
        raise NotImplementedError()


class FullExperimentViewSet(mixins.RetrieveModelMixin,
                            GenericAPIBackedViewSet):
    serializer_class = serializers.FullExperimentSerializer
    lookup_field = 'experiment_id'

    def get_instance(self, lookup_value):
        """Get FullExperiment instance with resolved references."""
        # TODO: move loading experiment and references to airavata_sdk?
        experimentModel = grpc_adapters.experiment(
            self.request.airavata.research.get_experiment(lookup_value))
        outputDataProducts = [
            grpc_adapters.data_product(
                self.request.airavata.research.get_data_product(output.value))
            for output in experimentModel.experimentOutputs
            if (output.value and
                output.value.startswith('airavata-dp') and
                output.type in (DataType.URI,
                                DataType.STDOUT,
                                DataType.STDERR))]
        outputDataProducts += [
            grpc_adapters.data_product(
                self.request.airavata.research.get_data_product(dp))
            for output in experimentModel.experimentOutputs
            if (output.value and
                output.type == DataType.URI_COLLECTION)
            for dp in output.value.split(',')
            if output.value.startswith('airavata-dp')]
        appInterfaceId = experimentModel.executionId
        try:
            applicationInterface = grpc_adapters.application_interface(
                self.request.airavata.research.get_application_interface(
                    appInterfaceId))
        except Exception as e:
            log.warning(f"Failed to load app interface: {e}")
            applicationInterface = None
        exp_output_views = output_views.get_output_views(
            self.request, experimentModel, applicationInterface)
        inputDataProducts = [
            grpc_adapters.data_product(
                self.request.airavata.research.get_data_product(inp.value))
            for inp in experimentModel.experimentInputs
            if (inp.value and
                inp.value.startswith('airavata-dp') and
                inp.type in (DataType.URI,
                             DataType.STDOUT,
                             DataType.STDERR))]
        inputDataProducts += [
            grpc_adapters.data_product(
                self.request.airavata.research.get_data_product(dp))
            for inp in experimentModel.experimentInputs
            if (inp.value and
                inp.type == DataType.URI_COLLECTION)
            for dp in inp.value.split(',')
            if inp.value.startswith('airavata-dp')]
        applicationModule = None
        try:
            if applicationInterface is not None:
                appModuleId = applicationInterface.applicationModules[0]
                applicationModule = (
                    self.request.airavata.research.get_application_module(
                        appModuleId))
            else:
                log.warning(
                    "Cannot load application model since app interface failed to load")
        except Exception:
            log.exception("Failed to load app interface/module", extra={'request': self.request})

        compute_resource_id = None
        user_conf = experimentModel.userConfigurationData
        if user_conf and user_conf.computationalResourceScheduling:
            comp_res_sched = user_conf.computationalResourceScheduling
            compute_resource_id = comp_res_sched.resourceHostId
        try:
            compute_resource = grpc_adapters.compute_resource(
                self.request.airavata.compute.get_compute_resource(
                    compute_resource_id)) \
                if compute_resource_id else None
        except Exception:
            log.exception("Failed to load compute resource for {}".format(
                compute_resource_id), extra={'request': self.request})
            compute_resource = None
        if serializers.user_has_access(
                self.request, experimentModel.projectId, 'READ'):
            project = self.request.airavata.research.get_project(
                experimentModel.projectId)
        else:
            # User may not have access to project, only experiment
            project = None
        job_details = [
            grpc_adapters.job_model(j)
            for j in self.request.airavata.research.get_job_details(lookup_value)]
        full_experiment = serializers.FullExperiment(
            experimentModel,
            project=project,
            outputDataProducts=outputDataProducts,
            inputDataProducts=inputDataProducts,
            applicationModule=applicationModule,
            computeResource=compute_resource,
            jobDetails=job_details,
            outputViews=exp_output_views)
        return full_experiment


class ApplicationModuleViewSet(APIBackedViewSet):
    serializer_class = serializers.ApplicationModuleSerializer
    lookup_field = 'app_module_id'

    def get_list(self):
        return list(self.request.airavata.research.get_accessible_app_modules(
            gateway_id=self.gateway_id))

    def get_instance(self, lookup_value):
        return self.request.airavata.research.get_application_module(
            lookup_value)

    def perform_create(self, serializer):
        app_module = serializer.save()
        app_module_id = self.request.airavata.research.register_application_module(
            self.gateway_id, app_module)
        app_module.app_module_id = app_module_id

    def perform_update(self, serializer):
        app_module = serializer.save()
        self.request.airavata.research.update_application_module(
            app_module.app_module_id, app_module)

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_module(
            instance.app_module_id)

    @action(detail=True)
    def application_interface(self, request, app_module_id):
        all_app_interfaces = [
            grpc_adapters.application_interface(i)
            for i in request.airavata.research.get_all_application_interfaces(
                self.gateway_id)]
        app_interfaces = []
        for app_interface in all_app_interfaces:
            if not app_interface.applicationModules:
                continue
            if app_module_id in app_interface.applicationModules:
                app_interfaces.append(app_interface)
        if len(app_interfaces) == 1:
            serializer = serializers.ApplicationInterfaceDescriptionSerializer(
                app_interfaces[0], context={'request': request})
            return Response(serializer.data)
        elif len(app_interfaces) > 1:
            log.error(
                "More than one application interface found for module {}: {}"
                .format(app_module_id, app_interfaces), extra={'request': request})
            raise Exception(
                'More than one application interface found for module {}'
                .format(app_module_id)
            )
        else:
            raise Http404("No application interface found for module id {}"
                          .format(app_module_id))

    @action(detail=True)
    def application_deployments(self, request, app_module_id):
        all_deployments = [
            grpc_adapters.application_deployment(d)
            for d in self.request.airavata.research
            .get_accessible_application_deployments(self.gateway_id)]
        app_deployments = [
            dep for dep in all_deployments if dep.appModuleId == app_module_id]
        serializer = serializers.ApplicationDeploymentDescriptionSerializer(
            app_deployments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def favorite(self, request, app_module_id):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = (
                workspace_preferences.applicationpreferences_set.get(
                    application_id=app_module_id))
            application_preferences.favorite = True
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username,
                application_id=app_module_id,
                favorite=True)

        return HttpResponse(status=204)

    @action(methods=['post'], detail=True)
    def unfavorite(self, request, app_module_id):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = (
                workspace_preferences.applicationpreferences_set.get(
                    application_id=app_module_id))
            application_preferences.favorite = False
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username,
                application_id=app_module_id,
                favorite=False)

        return HttpResponse(status=204)

    @action(detail=False)
    def list_all(self, request, format=None):
        all_modules = list(self.request.airavata.research.get_all_app_modules(
            gateway_id=self.gateway_id))
        serializer = self.serializer_class(
            all_modules, many=True, context={'request': request})
        return Response(serializer.data)


class ApplicationInterfaceViewSet(APIBackedViewSet):
    serializer_class = serializers.ApplicationInterfaceDescriptionSerializer
    lookup_field = 'app_interface_id'

    def get_list(self):
        return [
            grpc_adapters.application_interface(i)
            for i in self.request.airavata.research.get_all_application_interfaces(
                self.gateway_id)
        ]

    def get_instance(self, lookup_value):
        try:
            return grpc_adapters.application_interface(
                self.request.airavata.research.get_application_interface(
                    lookup_value))
        except Exception:
            # If it failed to load, check to see if it exists at all
            all_interfaces = self.request.airavata.research.get_all_application_interfaces(
                self.gateway_id)
            interface_ids = [i.application_interface_id for i in all_interfaces]
            if lookup_value not in interface_ids:
                raise Http404("Application interface does not exist")
            else:
                raise  # re-raise

    def perform_create(self, serializer):
        application_interface = serializer.save()
        self._update_input_metadata(application_interface)
        log.debug("application_interface: {}".format(application_interface))
        app_interface_id = self.request.airavata.research.register_application_interface(
            self.gateway_id, grpc_requests.application_interface(application_interface))
        application_interface.applicationInterfaceId = app_interface_id

    def perform_update(self, serializer):
        application_interface = serializer.save()
        self._update_input_metadata(application_interface)
        self.request.airavata.research.update_application_interface(
            application_interface.applicationInterfaceId,
            grpc_requests.application_interface(application_interface))

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_interface(
            instance.applicationInterfaceId)

    def _update_input_metadata(self, app_interface):
        for app_input in app_interface.applicationInputs:
            if app_input.metaData:
                metadata = json.loads(app_input.metaData)
                # Automatically add {showOptions: {isRequired: true/false}} to
                # toggle isRequired on hidden/shown inputs
                if ("editor" in metadata and
                    "dependencies" in metadata["editor"] and
                        "show" in metadata["editor"]["dependencies"]):
                    if "showOptions" not in metadata["editor"]["dependencies"]:
                        metadata["editor"]["dependencies"]["showOptions"] = {}
                    o = metadata["editor"]["dependencies"]["showOptions"]
                    o["isRequired"] = app_input.isRequired
                    app_input.metaData = json.dumps(metadata)

    @action(detail=True)
    def compute_resources(self, request, app_interface_id):
        compute_resources = request.airavata.research.get_available_app_interface_compute_resources(
            app_interface_id)
        return Response(compute_resources)


class ApplicationDeploymentViewSet(APIBackedViewSet):
    serializer_class = serializers.ApplicationDeploymentDescriptionSerializer
    lookup_field = 'app_deployment_id'

    def get_list(self):
        app_module_id = self.request.query_params.get('appModuleId', None)
        group_resource_profile_id = self.request.query_params.get(
            'groupResourceProfileId', None)
        if (app_module_id and not group_resource_profile_id)\
                or (not app_module_id and group_resource_profile_id):
            raise ParseError("Query params appModuleId and "
                             "groupResourceProfileId are required together.")
        if app_module_id and group_resource_profile_id:
            deployments = self.request.airavata.research.get_application_deployments_for_app_module_and_group_resource_profile(
                app_module_id, group_resource_profile_id)
        else:
            deployments = self.request.airavata.research.get_accessible_application_deployments(
                self.gateway_id)
        return [grpc_adapters.application_deployment(d) for d in deployments]

    def get_instance(self, lookup_value):
        return grpc_adapters.application_deployment(
            self.request.airavata.research.get_application_deployment(lookup_value))

    def perform_create(self, serializer):
        application_deployment = serializer.save()
        app_deployment_id = self.request.airavata.research.register_application_deployment(
            self.gateway_id, grpc_requests.application_deployment(application_deployment))
        application_deployment.appDeploymentId = app_deployment_id

    def perform_update(self, serializer):
        application_deployment = serializer.save()
        self.request.airavata.research.update_application_deployment(
            application_deployment.appDeploymentId,
            grpc_requests.application_deployment(application_deployment))

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_deployment(
            instance.appDeploymentId)

    @action(detail=True)
    def queues(self, request, app_deployment_id):
        """Return queues for this deployment with defaults overridden by deployment defaults if they exist"""
        app_deployment = grpc_adapters.application_deployment(
            self.request.airavata.research.get_application_deployment(
                app_deployment_id))
        compute_resource = grpc_adapters.compute_resource(
            request.airavata.compute.get_compute_resource(
                app_deployment.computeHostId))
        # Override defaults with app deployment default queue, if defined
        batch_queues = []
        for batch_queue in compute_resource.batchQueues:
            if app_deployment.defaultQueueName:
                if app_deployment.defaultQueueName == batch_queue.queueName:
                    batch_queue.isDefaultQueue = True
                    batch_queue.defaultNodeCount = app_deployment.defaultNodeCount
                    batch_queue.defaultCPUCount = app_deployment.defaultCPUCount
                    batch_queue.defaultWalltime = app_deployment.defaultWalltime
                else:
                    batch_queue.isDefaultQueue = False
            batch_queues.append(batch_queue)
        serializer = serializers.BatchQueueSerializer(
            batch_queues, many=True, context={'request': request})
        return Response(serializer.data)


class ComputeResourceViewSet(mixins.RetrieveModelMixin,
                             GenericAPIBackedViewSet):
    serializer_class = serializers.ComputeResourceDescriptionSerializer
    lookup_field = 'compute_resource_id'

    def get_instance(self, lookup_value, format=None):
        return grpc_adapters.compute_resource(
            self.request.airavata.compute.get_compute_resource(lookup_value))

    @action(detail=False)
    def all_names(self, request, format=None):
        """Return a map of compute resource names keyed by resource id."""
        return Response(
            request.airavata.compute.get_all_compute_resource_names())

    @action(detail=False)
    def all_names_list(self, request, format=None):
        """Return a list of compute resource names keyed by resource id."""
        all_names = request.airavata.compute.get_all_compute_resource_names()
        return Response([
            {
                'host_id': host_id,
                'host': host,
                'url': request.build_absolute_uri(
                    reverse('django_airavata_api:compute-resource-detail',
                            args=[host_id]))
            } for host_id, host in all_names.items()
        ])

    @action(detail=True)
    def queues(self, request, compute_resource_id, format=None):
        details = grpc_adapters.compute_resource(
            request.airavata.compute.get_compute_resource(compute_resource_id))
        serializer = self.serializer_class(instance=details,
                                           context={'request': request})
        data = serializer.data
        return Response([queue["queueName"] for queue in data["batchQueues"]])


class LocalJobSubmissionView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        job_submission_id = request.query_params["id"]
        local_job_submission = grpc_adapters.local_job_submission(
            request.airavata.compute.get_local_job_submission(job_submission_id))
        return Response(
            thrift_utils.create_serializer(
                LOCALSubmission,
                instance=local_job_submission).data)


class CloudJobSubmissionView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        job_submission_id = request.query_params["id"]
        job_submission = grpc_adapters.cloud_job_submission(
            request.airavata.compute.get_cloud_job_submission(job_submission_id))
        return Response(
            thrift_utils.create_serializer(
                CloudJobSubmission,
                instance=job_submission).data)


class SshJobSubmissionView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        job_submission_id = request.query_params["id"]
        job_submission = grpc_adapters.ssh_job_submission(
            request.airavata.compute.get_ssh_job_submission(job_submission_id))
        return Response(
            thrift_utils.create_serializer(
                SSHJobSubmission,
                instance=job_submission).data)


class UnicoreJobSubmissionView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        job_submission_id = request.query_params["id"]
        job_submission = grpc_adapters.unicore_job_submission(
            request.airavata.compute.get_unicore_job_submission(job_submission_id))
        return Response(
            thrift_utils.create_serializer(
                UnicoreJobSubmission,
                instance=job_submission).data)


class GridFtpDataMovementView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        data_movement_id = request.query_params["id"]
        data_movement = grpc_adapters.grid_ftp_data_movement(
            request.airavata.storage.get_grid_ftp_data_movement(data_movement_id))
        return Response(
            thrift_utils.create_serializer(
                GridFTPDataMovement,
                instance=data_movement).data)


class ScpDataMovementView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        data_movement_id = request.query_params["id"]
        data_movement = grpc_adapters.scp_data_movement(
            request.airavata.storage.get_scp_data_movement(data_movement_id))
        return Response(
            thrift_utils.create_serializer(
                SCPDataMovement,
                instance=data_movement).data)


class LocalDataMovementView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        data_movement_id = request.query_params["id"]
        data_movement = grpc_adapters.local_data_movement(
            request.airavata.storage.get_local_data_movement(data_movement_id))
        return Response(
            thrift_utils.create_serializer(
                LOCALDataMovement,
                instance=data_movement).data)


class DataProductView(APIView):

    serializer_class = serializers.DataProductSerializer
    permission_classes = [IsAuthenticated, DataProductSharedDirPermission]

    def get(self, request, format=None):
        data_product_uri = request.query_params['product-uri']
        data_product = grpc_adapters.data_product(
            request.airavata.research.get_data_product(data_product_uri))
        serializer = self.serializer_class(
            data_product, context={'request': request})
        return Response(serializer.data)

    def put(self, request, format=None):
        data_product_uri = request.query_params['product-uri']
        data_product = grpc_adapters.data_product(
            request.airavata.research.get_data_product(data_product_uri))
        if request.data and "fileContentText" in request.data:
            file_path = grpc_adapters.data_product_file_path(data_product)
            if file_path is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            # Overwrite the file content in place at the replica's path.
            request.airavata.storage.upload_file(
                path=file_path,
                content=request.data["fileContentText"].encode("utf-8"),
                name=data_product.productName or os.path.basename(file_path))
            return self.get(request=request, format=format)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=['POST'])
def upload_input_file(request):
    try:
        input_file = request.FILES['file']
        data_product = _storage_upload_and_register(
            request, TMP_INPUT_FILE_UPLOAD_DIR, input_file,
            content_type=input_file.content_type)
        serializer = serializers.DataProductSerializer(
            data_product, context={'request': request})
        return JsonResponse({'uploaded': True,
                             'data-product': serializer.data})
    except Exception as e:
        log.error("Failed to upload file", exc_info=True, extra={'request': request})
        resp = JsonResponse({'uploaded': False, 'error': str(e)})
        resp.status_code = 500
        return resp


@api_view(http_method_names=['POST'])
def tus_upload_finish(request):
    uploadURL = request.POST['uploadURL']

    def save_upload(file_path, file_name, file_type):
        with open(file_path, 'rb') as uploaded_file:
            return _storage_upload_and_register(
                request, TMP_INPUT_FILE_UPLOAD_DIR, uploaded_file,
                name=file_name, content_type=file_type)
    try:
        data_product = tus.save_tus_upload(uploadURL, save_upload)
        serializer = serializers.DataProductSerializer(
            data_product, context={'request': request})
        return JsonResponse({'uploaded': True,
                             'data-product': serializer.data})
    except Exception as e:
        return exceptions.generic_json_exception_response(e, status=400)


@gzip_page
@api_view()
def download_file(request):
    # TODO: remove this deprecated view
    warnings.warn("download_file view is deprecated; use 'download-file'", DeprecationWarning)
    # Redirect to the gRPC byte-streaming download endpoint.
    data_product_uri = request.GET.get('data-product-uri', '')
    return redirect(
        request.build_absolute_uri(reverse('django_airavata_api:download-file'))
        + '?data-product-uri=' + quote(data_product_uri))


@api_view()
def download(request):
    """Stream the bytes of a data product's first replica.

    Resolves ``?data-product-uri=`` via the gRPC research registry and streams
    the file from the gRPC storage facade. Replaces the legacy SDK
    download-URL/redirect path. The DataProductSerializer's ``downloadURL``
    field points here.
    """
    data_product_uri = request.GET.get('data-product-uri', '')
    try:
        data_product = grpc_adapters.data_product(
            request.airavata.research.get_data_product(data_product_uri))
    except Exception as e:
        log.warning("Failed to load DataProduct for {}".format(
            data_product_uri), exc_info=True, extra={'request': request})
        raise Http404("data product does not exist") from e
    file_path = grpc_adapters.data_product_file_path(data_product)
    if file_path is None:
        raise Http404("data product has no replica to download")
    resp = request.airavata.storage.download_file(file_path)
    file_name = resp.name or data_product.productName or os.path.basename(file_path)
    response = FileResponse(
        io.BytesIO(resp.content),
        as_attachment=False,
        filename=file_name,
        content_type=resp.content_type or 'application/octet-stream')
    return response


@api_view(http_method_names=['DELETE'])
@permission_classes([IsAuthenticated, DataProductSharedDirPermission])
def delete_file(request):
    # TODO check that user has write access to this file using sharing API
    data_product_uri = request.GET.get('data-product-uri', '')
    data_product = None
    try:
        data_product = grpc_adapters.data_product(
            request.airavata.research.get_data_product(data_product_uri))
    except Exception as e:
        log.warning("Failed to load DataProduct for {}"
                    .format(data_product_uri), exc_info=True)
        raise Http404("data product does not exist") from e
    try:
        if (data_product.gatewayId != settings.GATEWAY_ID or
                data_product.ownerName != request.user.username):
            raise PermissionDenied()
        file_path = grpc_adapters.data_product_file_path(data_product)
        if file_path is None:
            raise Http404("data product has no replica to delete")
        request.airavata.storage.delete_file(file_path)
        return HttpResponse(status=204)
    except ObjectDoesNotExist as e:
        raise Http404(str(e)) from e


class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         GenericAPIBackedViewSet):
    serializer_class = serializers.UserProfileSerializer

    def get_list(self):
        return [
            grpc_adapters.user_profile(p)
            for p in self.request.airavata.iam.get_all_user_profiles_in_gateway(
                self.gateway_id, 0, -1)
        ]

    def get_instance(self, lookup_value):
        return grpc_adapters.user_profile(
            self.request.airavata.iam.get_user_profile_by_id(
                self.request.user.username, self.gateway_id))


class GroupResourceProfileViewSet(APIBackedViewSet):
    serializer_class = serializers.GroupResourceProfileSerializer
    lookup_field = 'group_resource_profile_id'

    def get_list(self):
        return [
            grpc_adapters.group_resource_profile(p)
            for p in self.request.airavata.compute.get_group_resource_list()
        ]

    def get_instance(self, lookup_value):
        return grpc_adapters.group_resource_profile(
            self.request.airavata.compute.get_group_resource_profile(lookup_value))

    def perform_create(self, serializer):
        group_resource_profile = serializer.save()
        group_resource_profile.gatewayId = self.gateway_id
        created = self.request.airavata.compute.create_group_resource_profile(
            grpc_requests.group_resource_profile(group_resource_profile))
        group_resource_profile.groupResourceProfileId = created.group_resource_profile_id
        group_resource_profile.creationTime = created.creation_time

    def perform_update(self, serializer):
        original_instance = serializer.instance

        grp = serializer.save()
        for removed_compute_resource_preference \
                in grp._removed_compute_resource_preferences:
            self.request.airavata.compute.remove_group_compute_prefs(
                removed_compute_resource_preference.groupResourceProfileId,
                removed_compute_resource_preference.computeResourceId)
        for removed_compute_resource_policy \
                in grp._removed_compute_resource_policies:
            self.request.airavata.compute.remove_group_compute_resource_policy(
                removed_compute_resource_policy.resourcePolicyId)
        for removed_batch_queue_resource_policy \
                in grp._removed_batch_queue_resource_policies:
            self.request.airavata.compute.remove_group_batch_queue_resource_policy(
                removed_batch_queue_resource_policy.resourcePolicyId)
        if hasattr(grp, 'computePreferences') and grp.computePreferences:
            from collections import OrderedDict
            from django_airavata.apps.api.serializers import GroupComputeResourcePreferenceSerializer

            for pref in grp.computePreferences:
                if isinstance(pref, GroupComputeResourcePreference):
                    if not hasattr(pref, 'resourceType') or pref.resourceType is None:
                        resource_type = None
                        if hasattr(pref, 'specificPreferences') and pref.specificPreferences:
                            if isinstance(pref.specificPreferences, (dict, OrderedDict)):
                                specific_prefs_dict = pref.specificPreferences
                                if 'slurm' in specific_prefs_dict or 'allocationProjectNumber' in specific_prefs_dict:
                                    resource_type = ResourceType.SLURM
                                elif 'aws' in specific_prefs_dict or 'region' in specific_prefs_dict:
                                    resource_type = ResourceType.AWS
                                else:
                                    resource_type = ResourceType.SLURM
                            elif hasattr(pref.specificPreferences, 'slurm') and pref.specificPreferences.slurm:
                                resource_type = ResourceType.SLURM
                            elif hasattr(pref.specificPreferences, 'aws') and pref.specificPreferences.aws:
                                resource_type = ResourceType.AWS
                            else:
                                resource_type = ResourceType.SLURM
                        else:
                            resource_type = ResourceType.SLURM
                        pref.resourceType = resource_type

                    resource_type = pref.resourceType if hasattr(pref, 'resourceType') and pref.resourceType else None
                    if resource_type:
                        if hasattr(pref, 'specificPreferences') and isinstance(pref.specificPreferences, (dict, OrderedDict)):
                            GroupComputeResourcePreferenceSerializer._convert_specific_preferences_dict_to_thrift(
                                pref, resource_type
                            )
                        elif hasattr(pref, 'specificPreferences') and pref.specificPreferences:
                            GroupComputeResourcePreferenceSerializer._convert_specific_preferences_dict_to_thrift(
                                pref, resource_type
                            )

        from collections import OrderedDict
        from airavata.model.appcatalog.groupresourceprofile.ttypes import (
            ComputeResourcePolicy,
            BatchQueueResourcePolicy
        )

        if hasattr(grp, 'computeResourcePolicies') and grp.computeResourcePolicies:
            existing_policies_by_resource_id = {}
            if original_instance and hasattr(original_instance, 'computeResourcePolicies'):
                for existing_policy in original_instance.computeResourcePolicies:
                    if hasattr(existing_policy, 'computeResourceId') and hasattr(existing_policy, 'resourcePolicyId'):
                        existing_policies_by_resource_id[existing_policy.computeResourceId] = existing_policy

            indices_to_remove = []
            for idx, policy in enumerate(grp.computeResourcePolicies):
                if isinstance(policy, (dict, OrderedDict)):
                    try:
                        if isinstance(policy, OrderedDict):
                            policy = dict(policy)

                        compute_resource_id = policy.get('computeResourceId')
                        current_resource_policy_id = policy.get('resourcePolicyId')

                        if not current_resource_policy_id:
                            if compute_resource_id and compute_resource_id in existing_policies_by_resource_id:
                                existing_policy = existing_policies_by_resource_id[compute_resource_id]
                                policy['resourcePolicyId'] = existing_policy.resourcePolicyId
                            elif original_instance and hasattr(original_instance, 'computeResourcePolicies') and idx < len(original_instance.computeResourcePolicies):
                                existing_policy_by_idx = original_instance.computeResourcePolicies[idx]
                                if hasattr(existing_policy_by_idx, 'resourcePolicyId') and existing_policy_by_idx.resourcePolicyId:
                                    policy['resourcePolicyId'] = existing_policy_by_idx.resourcePolicyId

                        if not policy.get('resourcePolicyId'):
                            indices_to_remove.append(idx)
                            continue

                        grp.computeResourcePolicies[idx] = ComputeResourcePolicy(**policy)
                    except Exception as e:
                        log.error(
                            "GCPreference perform_update: Failed to convert computeResourcePolicies[%d] OrderedDict to Thrift: %s, policy keys: %s",
                            idx,
                            str(e),
                            list(policy.keys()) if isinstance(policy, dict) else list(policy.keys()),
                            exc_info=True,
                        )
                        raise

            for idx in reversed(indices_to_remove):
                grp.computeResourcePolicies.pop(idx)

        if hasattr(grp, 'batchQueueResourcePolicies') and grp.batchQueueResourcePolicies:
            existing_bq_policies_by_key = {}
            if original_instance and hasattr(original_instance, 'batchQueueResourcePolicies'):
                for existing_bq_policy in original_instance.batchQueueResourcePolicies:
                    if (hasattr(existing_bq_policy, 'computeResourceId') and
                        hasattr(existing_bq_policy, 'queuename') and
                        hasattr(existing_bq_policy, 'resourcePolicyId')):
                        key = (existing_bq_policy.computeResourceId, existing_bq_policy.queuename)
                        existing_bq_policies_by_key[key] = existing_bq_policy

            for idx, policy in enumerate(grp.batchQueueResourcePolicies):
                if isinstance(policy, (dict, OrderedDict)):
                    try:
                        compute_resource_id = policy.get('computeResourceId')
                        queuename = policy.get('queuename')
                        if compute_resource_id and queuename:
                            key = (compute_resource_id, queuename)
                            if key in existing_bq_policies_by_key:
                                existing_bq_policy = existing_bq_policies_by_key[key]
                                if 'resourcePolicyId' not in policy or policy.get('resourcePolicyId') is None:
                                    policy['resourcePolicyId'] = existing_bq_policy.resourcePolicyId
                        grp.batchQueueResourcePolicies[idx] = BatchQueueResourcePolicy(**policy)
                    except Exception as e:
                        log.error(
                            "GCPreference perform_update: Failed to convert batchQueueResourcePolicies[%d] OrderedDict to Thrift: %s",
                            idx,
                            str(e),
                            exc_info=True,
                        )

        if hasattr(grp, 'computePreferences') and grp.computePreferences:
            for idx, pref in enumerate(grp.computePreferences):
                if isinstance(pref, (dict, OrderedDict)):
                    from django_airavata.apps.api.serializers import GroupComputeResourcePreferenceSerializer
                    serializer = GroupComputeResourcePreferenceSerializer()
                    try:
                        pref = serializer.create(pref)
                        grp.computePreferences[idx] = pref
                    except Exception as e:
                        log.error(
                            "GCPreference perform_update: Failed to convert OrderedDict to Thrift: %s",
                            str(e),
                            exc_info=True,
                        )

                if isinstance(pref, GroupComputeResourcePreference):
                    if hasattr(pref, 'specificPreferences') and pref.specificPreferences:
                        if hasattr(pref.specificPreferences, 'slurm') and pref.specificPreferences.slurm:
                            GroupComputeResourcePreferenceSerializer._convert_nested_list_fields_to_thrift(
                                pref.specificPreferences.slurm
                            )
                            if hasattr(pref.specificPreferences.slurm, 'reservations') and pref.specificPreferences.slurm.reservations:
                                for res_idx, res in enumerate(pref.specificPreferences.slurm.reservations):
                                    if isinstance(res, (dict, OrderedDict)):
                                        from airavata.model.appcatalog.groupresourceprofile.ttypes import ComputeResourceReservation
                                        pref.specificPreferences.slurm.reservations[res_idx] = ComputeResourceReservation(**res)
                            if hasattr(pref.specificPreferences.slurm, 'groupSSHAccountProvisionerConfigs') and pref.specificPreferences.slurm.groupSSHAccountProvisionerConfigs:
                                for cfg_idx, cfg in enumerate(pref.specificPreferences.slurm.groupSSHAccountProvisionerConfigs):
                                    if isinstance(cfg, (dict, OrderedDict)):
                                        from airavata.model.appcatalog.groupresourceprofile.ttypes import GroupAccountSSHProvisionerConfig
                                        pref.specificPreferences.slurm.groupSSHAccountProvisionerConfigs[cfg_idx] = GroupAccountSSHProvisionerConfig(**cfg)

        self.request.airavata.compute.update_group_resource_profile(
            grp.groupResourceProfileId, grpc_requests.group_resource_profile(grp))

    def perform_destroy(self, instance):
        self.request.airavata.compute.remove_group_resource_profile(
            instance.groupResourceProfileId)


class SharedEntityViewSet(mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          GenericAPIBackedViewSet):
    serializer_class = serializers.SharedEntitySerializer
    lookup_field = 'entity_id'

    def get_instance(self, lookup_value):
        users = {}
        # Only load *directly* granted permissions since these are the only
        # ones that can be edited
        # Load accessible users in order of permission precedence: users that
        # have WRITE permission should also have READ
        users.update(self._load_directly_accessible_users(
            lookup_value, ResourcePermissionType.READ))
        users.update(self._load_directly_accessible_users(
            lookup_value, ResourcePermissionType.WRITE))
        users.update(self._load_directly_accessible_users(
            lookup_value, ResourcePermissionType.MANAGE_SHARING))
        owner_ids = self._load_directly_accessible_users(
            lookup_value, ResourcePermissionType.OWNER)
        # Assume that there is one and only one DIRECT owner (there may be one
        # or more INDIRECT cascading owners, which would the owners of the
        # ancestor entities, but getAllDirectlyAccessibleUsers does not return
        # indirectly cascading owners)
        owner_id = list(owner_ids.keys())[0]
        # Remove owner from the users list
        del users[owner_id]
        user_list = []
        for user_id in users:
            user_list.append({'user': self._load_user_profile(user_id),
                              'permissionType': users[user_id]})
        groups = {}
        groups.update(self._load_directly_accessible_groups(
            lookup_value, ResourcePermissionType.READ))
        groups.update(self._load_directly_accessible_groups(
            lookup_value, ResourcePermissionType.WRITE))
        groups.update(self._load_directly_accessible_groups(
            lookup_value, ResourcePermissionType.MANAGE_SHARING))
        group_list = []
        for group_id in groups:
            group_list.append({'group': self._load_group(group_id),
                               'permissionType': groups[group_id]})
        return {'entityId': lookup_value,
                'userPermissions': user_list,
                'groupPermissions': group_list,
                'owner': self._load_user_profile(owner_id)}

    def _load_accessible_users(self, entity_id, permission_type):
        users = self.request.airavata.sharing.get_all_accessible_users(
            entity_id, ResourcePermissionType(permission_type).name)
        return {user_id: permission_type for user_id in users}

    def _load_directly_accessible_users(self, entity_id, permission_type):
        users = self.request.airavata.sharing.get_all_directly_accessible_users(
            entity_id, ResourcePermissionType(permission_type).name)
        return {user_id: permission_type for user_id in users}

    def _load_user_profile(self, user_id):
        username = user_id[0:user_id.rindex('@')]
        return grpc_adapters.user_profile(
            self.request.airavata.iam.get_user_profile_by_id(
                username, settings.GATEWAY_ID))

    def _load_accessible_groups(self, entity_id, permission_type):
        groups = self.request.airavata.sharing.get_all_accessible_groups(
            entity_id, ResourcePermissionType(permission_type).name)
        return {group_id: permission_type for group_id in groups}

    def _load_directly_accessible_groups(self, entity_id, permission_type):
        groups = self.request.airavata.sharing.get_all_directly_accessible_groups(
            entity_id, ResourcePermissionType(permission_type).name)
        return {group_id: permission_type for group_id in groups}

    def _load_group(self, group_id):
        return grpc_adapters.group(
            self.request.airavata.sharing.gm_get_group(group_id))

    def perform_update(self, serializer):
        shared_entity = serializer.save()
        entity_id = shared_entity['entityId']
        if len(shared_entity['_user_grant_read_permission']) > 0:
            self._share_with_users(
                entity_id, ResourcePermissionType.READ,
                shared_entity['_user_grant_read_permission'])
        if len(shared_entity['_user_grant_write_permission']) > 0:
            self._share_with_users(
                entity_id, ResourcePermissionType.WRITE,
                shared_entity['_user_grant_write_permission'])
        if len(shared_entity['_user_grant_manage_sharing_permission']) > 0:
            self._share_with_users(
                entity_id, ResourcePermissionType.MANAGE_SHARING,
                shared_entity['_user_grant_manage_sharing_permission'])
        if len(shared_entity['_user_revoke_read_permission']) > 0:
            self._revoke_from_users(
                entity_id, ResourcePermissionType.READ,
                shared_entity['_user_revoke_read_permission'])
        if len(shared_entity['_user_revoke_write_permission']) > 0:
            self._revoke_from_users(
                entity_id, ResourcePermissionType.WRITE,
                shared_entity['_user_revoke_write_permission'])
        if len(shared_entity['_user_revoke_manage_sharing_permission']) > 0:
            self._revoke_from_users(
                entity_id, ResourcePermissionType.MANAGE_SHARING,
                shared_entity['_user_revoke_manage_sharing_permission'])
        if len(shared_entity['_group_grant_read_permission']) > 0:
            self._share_with_groups(
                entity_id, ResourcePermissionType.READ,
                shared_entity['_group_grant_read_permission'])
        if len(shared_entity['_group_grant_write_permission']) > 0:
            self._share_with_groups(
                entity_id, ResourcePermissionType.WRITE,
                shared_entity['_group_grant_write_permission'])
        if len(shared_entity['_group_grant_manage_sharing_permission']) > 0:
            self._share_with_groups(
                entity_id, ResourcePermissionType.MANAGE_SHARING,
                shared_entity['_group_grant_manage_sharing_permission'])
        if len(shared_entity['_group_revoke_read_permission']) > 0:
            self._revoke_from_groups(
                entity_id, ResourcePermissionType.READ,
                shared_entity['_group_revoke_read_permission'])
        if len(shared_entity['_group_revoke_write_permission']) > 0:
            self._revoke_from_groups(
                entity_id, ResourcePermissionType.WRITE,
                shared_entity['_group_revoke_write_permission'])
        if len(shared_entity['_group_revoke_manage_sharing_permission']) > 0:
            self._revoke_from_groups(
                entity_id, ResourcePermissionType.MANAGE_SHARING,
                shared_entity['_group_revoke_manage_sharing_permission'])

    def _share_with_users(self, entity_id, permission_type, user_ids):
        name = ResourcePermissionType(permission_type).name
        self.request.airavata.sharing.share_resource_with_users(
            entity_id, {user_id: name for user_id in user_ids})

    def _revoke_from_users(self, entity_id, permission_type, user_ids):
        name = ResourcePermissionType(permission_type).name
        self.request.airavata.sharing.revoke_sharing_of_resource_from_users(
            entity_id, {user_id: name for user_id in user_ids})

    def _share_with_groups(self, entity_id, permission_type, group_ids):
        name = ResourcePermissionType(permission_type).name
        self.request.airavata.sharing.share_resource_with_groups(
            entity_id, {group_id: name for group_id in group_ids})

    def _revoke_from_groups(self, entity_id, permission_type, group_ids):
        name = ResourcePermissionType(permission_type).name
        self.request.airavata.sharing.revoke_sharing_of_resource_from_groups(
            entity_id, {group_id: name for group_id in group_ids})

    @action(methods=['put'], detail=True)
    def merge(self, request, entity_id=None):
        # Validate updated sharing settings
        updated = self.get_serializer(data=request.data)
        updated.is_valid(raise_exception=True)
        # Get the existing sharing settings and merge in the updated settings
        existing_instance = self.get_object()
        existing = self.get_serializer(instance=existing_instance)
        merged_data = existing.data
        merged_data['userPermissions'] = existing.data['userPermissions'] + \
            updated.initial_data['userPermissions']
        merged_data['groupPermissions'] = existing.data['groupPermissions'] + \
            updated.initial_data['groupPermissions']
        # Create a merged_serializer from the existing sharing settings and the
        # merged settings. This will calculate all permissions that need to be
        # granted and revoked to go from the exisitng settings to the merged
        # settings.
        merged_serializer = self.get_serializer(
            existing_instance, data=merged_data)
        merged_serializer.is_valid(raise_exception=True)
        self.perform_update(merged_serializer)
        return Response(merged_serializer.data)

    @action(methods=['get'], detail=True)
    def all(self, request, entity_id=None):
        """Load direct plus indirectly (inherited) shared permissions."""
        users = {}
        # Load accessible users in order of permission precedence: users that
        # have WRITE permission should also have READ
        users.update(self._load_accessible_users(
            entity_id, ResourcePermissionType.READ))
        users.update(self._load_accessible_users(
            entity_id, ResourcePermissionType.WRITE))
        users.update(self._load_accessible_users(
            entity_id, ResourcePermissionType.MANAGE_SHARING))
        owner_ids = self._load_accessible_users(
            entity_id, ResourcePermissionType.OWNER)
        # Assume that there is one and only one DIRECT owner (there may be one
        # or more INDIRECT cascading owners, which would the owners of the
        # ancestor entities, but getAllAccessibleUsers does not return
        # indirectly cascading owners)
        owner_id = list(owner_ids.keys())[0]
        # Remove owner from the users list
        del users[owner_id]
        user_list = []
        for user_id in users:
            user_list.append({'user': self._load_user_profile(user_id),
                              'permissionType': users[user_id]})
        groups = {}
        groups.update(self._load_accessible_groups(
            entity_id, ResourcePermissionType.READ))
        groups.update(self._load_accessible_groups(
            entity_id, ResourcePermissionType.WRITE))
        groups.update(self._load_accessible_groups(
            entity_id, ResourcePermissionType.MANAGE_SHARING))
        group_list = []
        for group_id in groups:
            group_list.append({'group': self._load_group(group_id),
                               'permissionType': groups[group_id]})
        shared_entity = {'entityId': entity_id,
                         'userPermissions': user_list,
                         'groupPermissions': group_list,
                         'owner': self._load_user_profile(owner_id)}
        serializer = self.serializer_class(
            shared_entity, context={'request': request})
        return Response(serializer.data)


class CredentialSummaryViewSet(APIBackedViewSet):
    serializer_class = serializers.CredentialSummarySerializer

    def _credential_summaries(self, summary_type):
        return list(
            self.request.airavata.credential.get_all_credential_summaries(
                self.gateway_id, summary_type))

    def get_list(self):
        pb2 = serializers._credential_store_pb2()
        return (self._credential_summaries(pb2.SummaryType.SSH) +
                self._credential_summaries(pb2.SummaryType.PASSWD))

    def get_instance(self, lookup_value):
        return self.request.airavata.credential.get_credential_summary(
            lookup_value, self.gateway_id)

    @action(detail=False)
    def ssh(self, request):
        pb2 = serializers._credential_store_pb2()
        serializer = self.get_serializer(
            self._credential_summaries(pb2.SummaryType.SSH), many=True)
        return Response(serializer.data)

    @action(detail=False)
    def password(self, request):
        pb2 = serializers._credential_store_pb2()
        serializer = self.get_serializer(
            self._credential_summaries(pb2.SummaryType.PASSWD), many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def create_ssh(self, request):
        if 'description' not in request.data:
            raise ParseError("'description' is required in request")
        description = request.data.get('description')
        token_id = request.airavata.credential.generate_and_register_ssh_keys(
            self.gateway_id, self.username, description)
        credential_summary = request.airavata.credential.get_credential_summary(
            token_id, self.gateway_id)
        serializer = self.get_serializer(credential_summary)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def create_password(self, request):
        if ('username' not in request.data or
            'password' not in request.data or
                'description' not in request.data):
            raise ParseError("'username', 'password' and 'description' "
                             "are all required in request")
        username = request.data.get('username')
        password = request.data.get('password')
        description = request.data.get('description')
        token_id = request.airavata.credential.register_pwd_credential(
            self.gateway_id,
            grpc_requests.password_credential(
                self.gateway_id, self.username, username, password, description))
        credential_summary = request.airavata.credential.get_credential_summary(
            token_id, self.gateway_id)
        serializer = self.get_serializer(credential_summary)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        pb2 = serializers._credential_store_pb2()
        if instance.type == pb2.SummaryType.SSH:
            self.request.airavata.credential.delete_ssh_pub_key(
                instance.token, self.gateway_id)
        elif instance.type == pb2.SummaryType.PASSWD:
            self.request.airavata.credential.delete_pwd_credential(
                instance.token, self.gateway_id)


class CurrentGatewayResourceProfile(APIView):

    def get(self, request, format=None):
        gateway_resource_profile = grpc_adapters.gateway_resource_profile(
            request.airavata.compute.get_gateway_resource_profile(
                settings.GATEWAY_ID))
        serializer = serializers.GatewayResourceProfileSerializer(
            gateway_resource_profile, context={'request': request})
        return Response(serializer.data)

    def put(self, request, format=None):
        serializer = serializers.GatewayResourceProfileSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            gateway_resource_profile = serializer.save()
            request.airavata.compute.update_gateway_resource_profile(
                settings.GATEWAY_ID,
                grpc_requests.gateway_resource_profile(gateway_resource_profile))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExperimentArchiveView(APIView):

    def get(self, request, experiment_id=None, format=None):
        experiment = grpc_adapters.experiment(
            request.airavata.research.get_experiment(experiment_id))
        result = dict(archived=False, archive_name=None, created_date=None,
                      max_age=settings.GATEWAY_USER_DATA_ARCHIVE_MAX_AGE_DAYS)
        try:
            archive_entry = UserDataArchiveEntry.objects.get(
                entry_path=experiment.userConfigurationData.experimentDataDir,
                user_data_archive__rolled_back=False)
            result["archived"] = True
            result["archive_name"] = archive_entry.user_data_archive.archive_name
            result["created_date"] = archive_entry.user_data_archive.created_date
        except UserDataArchiveEntry.DoesNotExist:
            pass
        return Response(result, status=status.HTTP_200_OK)


class StorageResourceViewSet(mixins.RetrieveModelMixin,
                             GenericAPIBackedViewSet):
    serializer_class = serializers.StorageResourceSerializer
    lookup_field = 'storage_resource_id'

    def get_instance(self, lookup_value, format=None):
        return grpc_adapters.storage_resource(
            self.request.airavata.storage.get_storage_resource(lookup_value))

    @action(detail=False)
    def all_names(self, request, format=None):
        """Return a map of storage resource names keyed by resource id."""
        return Response(
            request.airavata.storage.get_all_storage_resource_names())


class StoragePreferenceViewSet(APIBackedViewSet):
    serializer_class = serializers.StoragePreferenceSerializer
    lookup_field = 'storage_resource_id'

    def get_list(self):
        return [
            grpc_adapters.storage_preference(p)
            for p in self.request.airavata.compute.get_all_gateway_storage_preferences(
                settings.GATEWAY_ID)
        ]

    def get_instance(self, lookup_value):
        return grpc_adapters.storage_preference(
            self.request.airavata.compute.get_gateway_storage_preference(
                settings.GATEWAY_ID, lookup_value))

    def perform_create(self, serializer):
        storage_preference = serializer.save()
        self.request.airavata.compute.add_gateway_storage_preference(
            settings.GATEWAY_ID,
            storage_preference.storageResourceId,
            grpc_requests.storage_preference(storage_preference))

    def perform_update(self, serializer):
        storage_preference = serializer.save()
        self.request.airavata.compute.update_gateway_storage_preference(
            settings.GATEWAY_ID,
            storage_preference.storageResourceId,
            grpc_requests.storage_preference(storage_preference))

    def perform_destroy(self, instance):
        self.request.airavata.compute.delete_gateway_storage_preference(
            settings.GATEWAY_ID, instance.storageResourceId)


class ParserViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    GenericAPIBackedViewSet):
    serializer_class = serializers.ParserSerializer
    lookup_field = 'parser_id'

    def get_list(self):
        return [
            grpc_adapters.parser(p)
            for p in self.request.airavata.research.list_all_parsers(
                settings.GATEWAY_ID)
        ]

    def get_instance(self, lookup_value):
        return grpc_adapters.parser(
            self.request.airavata.research.get_parser(
                lookup_value, settings.GATEWAY_ID))

    def perform_create(self, serializer):
        parser = serializer.save()
        parser.id = self.request.airavata.research.save_parser(
            grpc_requests.parser(parser))

    def perform_update(self, serializer):
        parser = serializer.save()
        self.request.airavata.research.save_parser(grpc_requests.parser(parser))


def _user_storage_path(path, experiment_id=None, request=None):
    """Resolve a user-storage path to the absolute, ``~/``-prefixed path the gRPC
    storage facade expects.

    A bare relative path is taken relative to the user's storage root (``~/``).
    When ``experiment_id`` is given, the path is relative to that experiment's
    data directory (resolved via the experiment's userConfigurationData).
    """
    rel = (path or "").lstrip("/")
    if experiment_id:
        experiment = grpc_adapters.experiment(
            request.airavata.research.get_experiment(experiment_id))
        data_dir = (experiment.userConfigurationData.experimentDataDir
                    if experiment.userConfigurationData else None) or ""
        base = data_dir.rstrip("/")
        full = base + ("/" + rel if rel else "")
        return full if (full.startswith("/") or full.startswith("~/")) else "~/" + full
    if rel.startswith("~"):
        return rel
    return "~/" + rel


class UserStoragePathView(APIView):
    serializer_class = serializers.UserStoragePathSerializer
    permission_classes = (IsAuthenticated, UserStorageSharedDirPermission)

    def get(self, request, path="/", format=None):
        # AIRAVATA-3460 Allow passing path as a query parameter instead
        path = request.query_params.get('path', path)
        experiment_id = request.query_params.get('experiment-id')
        return self._create_response(request, path, experiment_id=experiment_id)

    def post(self, request, path="/", format=None):
        path = request.data.get('path', path)
        experiment_id = request.data.get('experiment-id')
        storage = request.airavata.storage
        resolved = _user_storage_path(path, experiment_id, request)
        if not storage.dir_exists(resolved):
            storage.create_dir(resolved)

        data_product = None
        # Handle direct upload
        if 'file' in request.FILES:
            user_file = request.FILES['file']
            data_product = _storage_upload_and_register(
                request, path, user_file, name=user_file.name,
                content_type=user_file.content_type,
                experiment_id=experiment_id)
        # Handle a tus upload
        elif 'uploadURL' in request.POST:
            uploadURL = request.POST['uploadURL']

            def save_file(file_path, file_name, file_type):
                with open(file_path, 'rb') as uploaded_file:
                    return _storage_upload_and_register(
                        request, path, uploaded_file, name=file_name,
                        content_type=file_type, experiment_id=experiment_id)
            data_product = tus.save_tus_upload(uploadURL, save_file)
        return self._create_response(request, path, uploaded=data_product, experiment_id=experiment_id)

    # Accept either to replace file or to replace file content text.
    def put(self, request, path="/", format=None):
        path = request.POST.get('path', path)
        # Replace the file if the request has a file upload.
        if 'file' in request.FILES:
            self.delete(request=request, path=path, format=format)
            dir_path, file_name = os.path.split(path)
            self.post(request=request, path=dir_path, format=format)
        # Replace only the file content if the request body has the `fileContentText`
        elif request.data and "fileContentText" in request.data:
            request.airavata.storage.upload_file(
                path=_user_storage_path(path),
                content=request.data["fileContentText"].encode("utf-8"),
                name=os.path.basename(path))
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return self._create_response(request=request, path=path)

    def delete(self, request, path="/", format=None):
        path = request.data.get('path', path)
        experiment_id = request.data.get('experiment-id')
        storage = request.airavata.storage
        resolved = _user_storage_path(path, experiment_id, request)
        if storage.dir_exists(resolved):
            storage.delete_dir(resolved)
        else:
            storage.delete_file(resolved)

        return Response(status=204)

    def _create_response(self, request, path, uploaded=None, experiment_id=None):
        storage = request.airavata.storage
        resolved = _user_storage_path(path, experiment_id, request)
        if storage.dir_exists(resolved):
            listing = storage.list_dir(resolved)
            data = {
                'isDir': True,
                'directories': [
                    grpc_adapters.user_storage_directory(d) for d in listing.directories],
                'files': [grpc_adapters.user_storage_file(f) for f in listing.files],
            }
            if uploaded is not None:
                data['uploaded'] = uploaded
            data['parts'] = self._split_path(path)
            data['path'] = path
            serializer = self.serializer_class(
                data, context={'request': request})
            return Response(serializer.data)
        else:
            file = grpc_adapters.user_storage_file(storage.get_file_metadata(resolved))
            data = {
                'isDir': False,
                'directories': [],
                'files': [file]
            }
            if uploaded is not None:
                data['uploaded'] = uploaded
            data['parts'] = self._split_path(path)
            serializer = self.serializer_class(
                data, context={'request': request})
            return Response(serializer.data)

    def _split_path(self, path):
        head, tail = os.path.split(path)
        if head != path:
            return self._split_path(head) + [tail]
        elif tail != "":
            return [tail]
        else:
            return []


class ExperimentStoragePathView(APIView):

    serializer_class = serializers.ExperimentStoragePathSerializer

    def get(self, request, experiment_id=None, path="", format=None):
        return self._create_response(request, experiment_id, path)

    def _create_response(self, request, experiment_id, path):
        storage = request.airavata.storage
        resolved = _user_storage_path(path, experiment_id, request)
        if not storage.dir_exists(resolved):
            raise Http404(f"Path '{path}' does not exist for {experiment_id}")
        listing = storage.list_dir(resolved)

        def rel(entry_path):
            # Expose the path relative to the experiment data dir, as the legacy
            # list_experiment_dir did (resolved is the absolute experiment path).
            base = resolved.rstrip("/")
            p = entry_path
            if p.startswith(base + "/"):
                return p[len(base) + 1:]
            return os.path.basename(p)

        def add_expid(d):
            d['experiment_id'] = experiment_id
            return d
        data = {
            'isDir': True,
            'directories': [
                add_expid(grpc_adapters.user_storage_directory(
                    d, relative_path=os.path.join(path, rel(d.path)) if path else rel(d.path)))
                for d in listing.directories],
            'files': [
                add_expid(grpc_adapters.user_storage_file(
                    f, relative_path=os.path.join(path, rel(f.path)) if path else rel(f.path)))
                for f in listing.files],
        }
        data['parts'] = self._split_path(path)
        serializer = self.serializer_class(
            data, context={'request': request})
        return Response(serializer.data)

    def _split_path(self, path):
        head, tail = os.path.split(path)
        if head != "":
            return self._split_path(head) + [tail]
        elif tail != "":
            return [tail]
        else:
            return []


class WorkspacePreferencesView(APIView):
    serializer_class = serializers.WorkspacePreferencesSerializer

    def get(self, request, format=None):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        serializer = self.serializer_class(
            workspace_preferences, context={'request': request})
        return Response(serializer.data)


class ManageNotificationViewSet(APIBackedViewSet):
    serializer_class = serializers.NotificationSerializer
    lookup_field = 'notification_id'

    def get_instance(self, lookup_value):
        return grpc_adapters.notification(
            self.request.airavata.research.get_notification(
                settings.GATEWAY_ID, lookup_value))

    def get_list(self):
        return [
            grpc_adapters.notification(n)
            for n in self.request.airavata.research.get_all_notifications(
                self.gateway_id)
        ]

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_notification(
            settings.GATEWAY_ID, instance.notificationId)

    def perform_create(self, serializer):
        notification = serializer.save(gatewayId=self.gateway_id)
        notification.notificationId = self.request.airavata.research.create_notification(
            grpc_requests.notification(notification))

        serializer.update_notification_extension(self.request, notification)

    def perform_update(self, serializer):
        notification = serializer.save()
        self.request.airavata.research.update_notification(
            grpc_requests.notification(notification))

        serializer.update_notification_extension(self.request, notification)


class AckNotificationViewSet(APIView):

    def get(self, request, format=None):
        if 'id' in request.GET:
            notification_id = request.GET['id']
            try:
                notification = models.User_Notifications.objects.get(
                    notification_id=notification_id,
                    username=request.user.username)
                notification.is_read = True
                notification.save()
            except ObjectDoesNotExist:
                models.User_Notifications.objects.create(
                    username=request.user.username,
                    notification_id=notification.notificationId)
        return HttpResponse(status=204)


class IAMUserViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     GenericAPIBackedViewSet):
    serializer_class = serializers.IAMUserProfile
    pagination_class = APIResultPagination
    permission_classes = (IsAuthenticated, IsInAdminsGroupPermission,)
    lookup_field = 'user_id'

    def get_list(self):
        search = self.request.GET.get('search', None)

        convert_user_profile = self._convert_user_profile

        class IAMUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return map(convert_user_profile,
                           iam_admin_client.get_users(offset, limit, search))
        return IAMUsersResultIterator(query_params=self.request.query_params.copy())

    def get_instance(self, lookup_value):
        return self._convert_user_profile(
            iam_admin_client.get_user(lookup_value))

    def perform_update(self, serializer):
        managed_user_profile = serializer.save()
        sharing = self.request.airavata.sharing
        user_id = managed_user_profile['airavataInternalUserId']
        added_groups = []
        for group_id in managed_user_profile['_added_group_ids']:
            group = grpc_adapters.group(sharing.gm_get_group(group_id))
            sharing.gm_add_users_to_group([user_id], group_id)
            added_groups.append(group)
        if len(added_groups) > 0:
            user_profile = self.request.airavata.iam.get_user_profile_by_id(
                managed_user_profile['userId'], settings.GATEWAY_ID)
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=added_groups,
                request=self.request)
        for group_id in managed_user_profile['_removed_group_ids']:
            sharing.gm_remove_users_from_group([user_id], group_id)

    def perform_destroy(self, instance):
        iam_admin_client.delete_user(instance['userId'])

    @action(methods=['post'], detail=True)
    def enable(self, request, user_id=None):
        iam_admin_client.enable_user(user_id)
        instance = self.get_instance(user_id)
        serializer = self.serializer_class(instance=instance,
                                           context={'request': request})
        return Response(serializer.data)

    @action(methods=['put'], detail=False)
    def update_username(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_username = serializer.validated_data['userId']
        new_username = serializer.validated_data['newUsername']
        iam_admin_client.update_username(old_username, new_username)
        # set username_initialized to True so it is treated as valid.
        django_user = get_user_model().objects.get(username=old_username)
        django_user.user_profile.username_initialized = True
        django_user.user_profile.save()
        # Not strictly necessary since next time the user logs in, the Django
        # user record for the user will get updated to have the new username.
        # But this is done to keep it consistent.
        django_user.username = new_username
        django_user.save()
        instance = self.get_instance(new_username)
        serializer = self.serializer_class(instance=instance,
                                           context={'request': request})
        return Response(serializer.data)

    def _convert_user_profile(self, user_profile):
        # iam_admin_client returns a protobuf UserProfile; adapt it to the Thrift
        # attribute shape so the field reads and ``State`` comparison below are
        # unchanged.
        user_profile = grpc_adapters.user_profile(user_profile)
        airavata_user_profile_exists = self.request.airavata.iam.does_user_exist(
            user_profile.userId, self.gateway_id)
        groups = []
        if airavata_user_profile_exists:
            groups = [
                grpc_adapters.group(g)
                for g in self.request.airavata.sharing.gm_get_all_groups_user_belongs(
                    user_profile.airavataInternalUserId)
            ]
        return {
            'airavataInternalUserId': user_profile.airavataInternalUserId,
            'userId': user_profile.userId,
            'gatewayId': user_profile.gatewayId,
            'email': user_profile.emails[0],
            'firstName': user_profile.firstName,
            'lastName': user_profile.lastName,
            'enabled': user_profile.State == Status.ACTIVE,
            'emailVerified': (user_profile.State == Status.CONFIRMED or
                              user_profile.State == Status.ACTIVE),
            'airavataUserProfileExists': airavata_user_profile_exists,
            'creationTime': user_profile.creationTime,
            'groups': groups
        }


class ExperimentStatisticsView(APIView):
    # TODO: restrict to only Admins or Read Only Admins group members
    serializer_class = serializers.ExperimentStatisticsSerializer

    def get(self, request, format=None):
        if 'fromTime' in request.GET:
            from_time = view_utils.convert_utc_iso8601_to_date(
                request.GET['fromTime']).timestamp() * 1000
        else:
            from_time = (datetime.utcnow() -
                         timedelta(days=7)).timestamp() * 1000
        from_time = int(from_time)
        if 'toTime' in request.GET:
            to_time = view_utils.convert_utc_iso8601_to_date(
                request.GET['toTime']).timestamp() * 1000
        else:
            to_time = datetime.utcnow().timestamp() * 1000
        to_time = int(to_time)
        username = request.GET.get('userName', None)
        application_name = request.GET.get('applicationName', None)
        resource_hostname = request.GET.get('resourceHostName', None)
        limit = int(request.GET.get('limit', '50'))
        offset = int(request.GET.get('offset', '0'))

        statistics = request.airavata.research.get_experiment_statistics(
            settings.GATEWAY_ID, from_time, to_time,
            username or "", application_name or "", resource_hostname or "",
            limit, offset)
        serializer = self.serializer_class(statistics, context={'request': request})

        paginator = pagination.LimitOffsetPagination()
        paginator.count = statistics.all_experiment_count
        paginator.limit = limit
        paginator.offset = offset
        paginator.request = request
        response = paginator.get_paginated_response(serializer.data)
        # Also add limit and offset to the response
        response.data['limit'] = limit
        response.data['offset'] = offset
        return response


class UnverifiedEmailUserViewSet(mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin,
                                 GenericAPIBackedViewSet):
    serializer_class = serializers.UnverifiedEmailUserProfile
    pagination_class = APIResultPagination
    permission_classes = (IsAuthenticated, IsInAdminsGroupPermission,)
    lookup_field = 'user_id'

    def get_list(self):
        get_users = self._get_unverified_email_user_profiles

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return get_users(limit, offset)
        return UnverifiedEmailUsersResultIterator()

    def get_instance(self, lookup_value):
        users = self._get_unverified_email_user_profiles(
            limit=1, username=lookup_value)
        if len(users) == 0:
            raise Http404("No unverified email record found for user {}"
                          .format(lookup_value))
        else:
            return users[0]

    def _get_unverified_email_user_profiles(
            self, limit=-1, offset=0, username=None):
        unverified_emails = EmailVerification.objects.filter(
            verified=False).order_by('username').values('username').distinct()
        if username is not None:
            unverified_emails = unverified_emails.filter(username=username)
        if limit > 0:
            unverified_emails = unverified_emails[offset:offset + limit]
        results = []
        for unverified_email in unverified_emails:
            unverified_username = unverified_email['username']
            if iam_admin_client.is_user_exist(unverified_username):
                user_profile = iam_admin_client.get_user(unverified_username)
                if (user_profile.State == Status.CONFIRMED or
                        user_profile.State == Status.ACTIVE):
                    # TODO: test this
                    EmailVerification.objects.filter(
                        username=unverified_username).update(
                        verified=True)
                    continue
                results.append({
                    'userId': user_profile.userId,
                    'gatewayId': user_profile.gatewayId,
                    'email': user_profile.emails[0],
                    'firstName': user_profile.firstName,
                    'lastName': user_profile.lastName,
                    'enabled': user_profile.State == Status.ACTIVE,
                    'emailVerified': (user_profile.State == Status.CONFIRMED or
                                      user_profile.State == Status.ACTIVE),
                    'creationTime': user_profile.creationTime,
                })
            else:
                # Delete the EmailVerification records since that user no
                # longer exists in the IAM service
                EmailVerification.objects.filter(
                    username=unverified_username).delete()
        return results


class LogRecordConsumer(APIView):
    serializer_class = serializers.LogRecordSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        log_record = serializer.validated_data
        log_level = getattr(logging, log_record['level'], None)
        if log_level is not None:
            stacktrace = "".join(
                map(lambda a: "\n    " + a, log_record['stacktrace']))
            log.log(log_level,
                    "Frontend error: {}: {}\nstacktrace: {}".format(
                        log_record['message'],
                        json.dumps(log_record['details'], indent=4),
                        stacktrace), extra={'request': request})
        return Response(serializer.data)


class SettingsAPIView(APIView):
    serializer_class = serializers.SettingsSerializer

    def get(self, request, format=None):
        data = {
            'fileUploadMaxFileSize': settings.FILE_UPLOAD_MAX_FILE_SIZE,
            'tusEndpoint': settings.TUS_ENDPOINT,
            'pgaUrl': settings.PGA_URL
        }
        serializer = self.serializer_class(
            data, context={'request': request})
        return Response(serializer.data)


class APIServerStatusCheckView(APIView):

    def get(self, request, format=None):
        try:
            request.airavata.research.get_user_projects(
                gateway_id=settings.GATEWAY_ID,
                user_name=request.user.username,
                limit=1,
                offset=0)
            data = {
                "apiServerUp": True
            }
        except Exception as e:
            log.debug("API server status check failed: {}".format(str(e)))
            data = {
                "apiServerUp": False
            }
        return Response(data)


@api_view()
def notebook_output_view(request):
    provider_id = request.GET['provider-id']
    experiment_id = request.GET['experiment-id']
    experiment_output_name = request.GET['experiment-output-name']
    data = output_views.generate_data(request,
                                      provider_id,
                                      experiment_output_name,
                                      experiment_id)
    return HttpResponse(data['output'])


@api_view()
def html_output_view(request):
    data = _generate_output_view_data(request)
    return JsonResponse(data)


@api_view()
def image_output_view(request):
    data = _generate_output_view_data(request)
    # data should contain 'image' as a file-like object or raw bytes with the
    # file data and 'mime-type' with the images mimetype
    data['image'] = base64.b64encode(data['image']).decode('utf-8')
    return JsonResponse(data)


@api_view()
def link_output_view(request):
    data = _generate_output_view_data(request)
    return JsonResponse(data)


def _generate_output_view_data(request):
    params = request.GET.copy()
    provider_id = params.pop('provider-id')[0]
    experiment_id = params.pop('experiment-id')[0]
    experiment_output_name = params.pop('experiment-output-name')[0]
    test_mode = ('test-mode' in params and params.pop('test-mode')[0] == "true")
    return output_views.generate_data(request,
                                      provider_id,
                                      experiment_output_name,
                                      experiment_id,
                                      test_mode=test_mode,
                                      **params.dict())


class QueueSettingsCalculatorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.QueueSettingsCalculatorSerializer

    def get_list(self):
        return queue_settings_calculators.get_all()

    def get_instance(self, lookup_value):
        calcs = queue_settings_calculators.get_all()
        calc = [calc for calc in calcs if calc.id == lookup_value]
        if len(calc) == 0:
            return None
        return calc[0]

    @action(methods=['post'], detail=True, serializer_class=serializers.ExperimentSerializer)
    def calculate(self, request, pk=None):

        serializer = self.get_serializer(data=request.data)
        result = {}
        # Just ignore invalid experiment model since likely caused by late initialization
        if serializer.is_valid():
            experiment_model = serializer.save()
            result = queue_settings_calculators.calculate_queue_settings(pk, request, experiment_model)
        return Response(result)
