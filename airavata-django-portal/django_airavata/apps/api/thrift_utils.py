"""
Used to create Django Rest Framework serializers for Apache Thrift Data Types
"""
import copy
import datetime
import logging
import enum

from rest_framework.serializers import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    DictField,
    Field,
    IntegerField,
    ListField,
    ListSerializer,
    Serializer,
    SerializerMetaclass,
    ValidationError
)
from thrift.Thrift import TType
from airavata.model.experiment.ttypes import ExperimentType
from airavata.model.status.ttypes import ExperimentState
from airavata.model.application.io.ttypes import DataType
from airavata.model.appcatalog.parallelism.ttypes import ApplicationParallelismType

logger = logging.getLogger(__name__)

# used to map apache thrift data types to django serializer fields
mapping = {
    TType.STRING: CharField,
    TType.I08: IntegerField,
    TType.I16: IntegerField,
    TType.I32: IntegerField,
    TType.I64: IntegerField,
    TType.DOUBLE: DecimalField,
    TType.BOOL: BooleanField,
    TType.MAP: DictField
}


class UTCPosixTimestampDateTimeField(DateTimeField):

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


class ThriftEnumField(Field):

    def __init__(self, enumClass, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enumClass = enumClass

    def to_representation(self, obj):
        # For IntEnum, obj is the enum member, its `.name` is the string
        if obj is None:
            return None
        return obj.name

    def to_internal_value(self, data):
        # Convert string name back into an IntEnum member
        if self.allow_null and data is None:
            return None
        try:
            return self.enumClass[data]
        except KeyError:
            raise ValidationError(f"'{data}' is not a valid name for enum {self.enumClass.__name__}")


def create_serializer(thrift_data_type, enable_date_time_conversion=False, **kwargs):
    """
    Create django rest framework serializer based on the thrift data type
    :param thrift_data_type: Thrift data type
    :param kwargs: Other Django Framework Serializer initialization parameters
    :param enable_date_time_conversion: enable conversion of field with name ending with time to
            UTCPosixTimestampDateTimeField instead of IntegerField
    :return: instance of custom serializer for the given thrift data type
    """
    return create_serializer_class(thrift_data_type, enable_date_time_conversion)(**kwargs)


def create_serializer_class(thrift_data_type, enable_date_time_conversion=False):
    class CustomSerializerMeta(SerializerMetaclass):

        def __new__(cls, name, bases, attrs):
            meta = attrs.get('Meta', None)
            thrift_spec = thrift_data_type.thrift_spec
            for field in thrift_spec:
                # Don't replace existing attrs to allow subclasses to override
                if field and field[2] not in attrs:
                    required = (field[2] in meta.required
                                if meta and hasattr(meta, 'required')
                                else False)
                    read_only = (field[2] in meta.read_only
                                 if meta and hasattr(meta, 'read_only')
                                 else False)
                    allow_null = not required
                    field_serializer = process_field(
                        field, enable_date_time_conversion, required=required, read_only=read_only,
                        allow_null=allow_null)
                    attrs[field[2]] = field_serializer
            return super().__new__(cls, name, bases, attrs)

    class CustomSerializer(Serializer, metaclass=CustomSerializerMeta):
        """
        Custom Serializer which handle the list fields which holds custom class objects
        """

        def process_nested_fields(self, validated_data):
            fields = self.fields
            params = copy.deepcopy(validated_data)
            for field_name, serializer in fields.items():
                if (isinstance(serializer, ListField) or
                        isinstance(serializer, ListSerializer)):
                    if (params.get(field_name, None) is not None or
                            not serializer.allow_null):
                        if isinstance(serializer.child, Serializer):
                            # If this is a list of experiment inputs, need to manually
                            # convert the 'type' field from an integer to a DataType enum
                            if field_name == 'experimentInputs' and 'type' in serializer.child.fields:
                                for item in params[field_name]:
                                    if 'type' in item and isinstance(item['type'], int):
                                        item['type'] = DataType(item['type'])
                            elif field_name == 'experimentOutputs' and 'type' in serializer.child.fields:
                                for item in params[field_name]:
                                    if 'type' in item and isinstance(item['type'], int):
                                        item['type'] = DataType(item['type'])
                            elif field_name == 'experimentStatus' and 'state' in serializer.child.fields:
                                for item in params[field_name]:
                                    if 'state' in item and isinstance(item['state'], int):
                                        item['state'] = ExperimentState(item['state'])
                            params[field_name] = [serializer.child.create(
                                item) for item in params[field_name]]
                        else:
                            params[field_name] = serializer.to_representation(
                                params[field_name])
                elif isinstance(serializer, Serializer):
                    if field_name in params and params[field_name] is not None:
                        params[field_name] = serializer.create(
                            params[field_name])
            return params

        def create(self, validated_data):
            params = self.process_nested_fields(validated_data)

            # The Thrift models expect a mandatory ID but provide a default value for creation.
            # The latest library upgrade is tight and fails if an ID is explicitly passed as `None`.
            # This logic removes such fields allowing the default to be used.
            thrift_spec = thrift_data_type.thrift_spec
            for field_spec in thrift_spec:
                if field_spec:
                    field_name = field_spec[2]
                    default_value = field_spec[4]
                    if default_value is not None:
                        if field_name in params and params[field_name] is None:
                            del params[field_name]

            if (thrift_data_type.__name__ == 'ExperimentModel' and
                'experimentType' in params and isinstance(params['experimentType'], int)):
                params['experimentType'] = ExperimentType(params['experimentType'])

            if (thrift_data_type.__name__ == 'ApplicationDeploymentDescription' and
                'parallelism' in params and isinstance(params['parallelism'], int)):
                params['parallelism'] = ApplicationParallelismType(params['parallelism'])

            return thrift_data_type(**params)

        def update(self, instance, validated_data):
            return self.create(validated_data)

    return CustomSerializer


def process_field(field, enable_date_time_conversion, required=False, read_only=False, allow_null=False):
    """
    Used to process a thrift data type field
    :param field:
    :param required:
    :param read_only:
    :param allow_null:
    :return:
    """
    if field[1] in mapping:
        # handling scenarios when the thrift field type is present in the
        # mapping
        field_class = mapping[field[1]]
        kwargs = dict(required=required, read_only=read_only)
        # allow_null isn't allowed for BooleanField
        if field_class not in (BooleanField,):
            kwargs['allow_null'] = allow_null
        # allow_null CharField are also allowed to be blank
        if field_class == CharField:
            kwargs['allow_blank'] = allow_null
        thrift_model_class = mapping[field[1]]

        if thrift_model_class == IntegerField and field[3] is not None and isinstance(field[3], type) and issubclass(field[3], enum.IntEnum):
            return ThriftEnumField(field[3], required=required, read_only=read_only, allow_null=allow_null)

        if enable_date_time_conversion and thrift_model_class == IntegerField and field[2].lower().endswith("time"):
            thrift_model_class = UTCPosixTimestampDateTimeField
        return thrift_model_class(**kwargs)
    elif field[1] == TType.LIST:
        # handling scenario when the thrift field type is list
        list_field_serializer = process_list_field(field)
        return ListField(child=list_field_serializer,
                         required=required,
                         read_only=read_only,
                         allow_null=allow_null)
    elif field[1] == TType.STRUCT:
        # handling scenario when the thrift field type is struct
        return create_serializer(field[3][0],
                                 required=required,
                                 read_only=read_only,
                                 allow_null=allow_null)


def process_list_field(field):
    """
    Used to process thrift list type field
    :param field:
    :return:
    """
    list_details = field[3]
    item_ttype = list_details[0]
    # For enums, extra type info is the enum Class (e.g. ExperimentState)
    # For structs, it's a tuple of (StructClass, StructClass.thrift_spec)
    item_type_info = list_details[1]

    if (item_ttype == TType.I32 and
        item_type_info is not None and
        isinstance(item_type_info, type) and
        issubclass(item_type_info, enum.IntEnum)):
        return ThriftEnumField(item_type_info)

    if item_ttype in mapping:
        return mapping[item_ttype]()
    elif item_ttype == TType.STRUCT:
        return create_serializer(item_type_info[0])
