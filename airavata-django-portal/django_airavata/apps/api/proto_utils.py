"""
Used to create Django Rest Framework serializers for Airavata data types.

Migrated from thrift_utils.py -- now works with proto-compatible data classes
from django_airavata.proto_compat instead of Thrift-generated types.
"""

import copy
import datetime
import enum
import logging

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
    ValidationError,
)

from django_airavata.proto_compat import (
    ApplicationParallelismType,
    DataType,
    ExperimentState,
    ExperimentType,
)

logger = logging.getLogger(__name__)

# TType constants (formerly from thrift.Thrift.TType)
# These mirror the Thrift type IDs used in thrift_spec tuples.
TTYPE_BOOL = 2
TTYPE_I08 = 3
TTYPE_I16 = 6
TTYPE_I32 = 8
TTYPE_I64 = 10
TTYPE_DOUBLE = 4
TTYPE_STRING = 11
TTYPE_STRUCT = 12
TTYPE_MAP = 13
TTYPE_LIST = 15

# Map proto/thrift field type IDs to DRF serializer fields
mapping = {
    TTYPE_STRING: CharField,
    TTYPE_I08: IntegerField,
    TTYPE_I16: IntegerField,
    TTYPE_I32: IntegerField,
    TTYPE_I64: IntegerField,
    TTYPE_DOUBLE: DecimalField,
    TTYPE_BOOL: BooleanField,
    TTYPE_MAP: DictField,
}


class UTCPosixTimestampDateTimeField(DateTimeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default = self.current_time_ms
        self.initial = self.initial_value
        self.required = False

    def to_representation(self, value):  # type: ignore[override]
        dt = datetime.datetime.fromtimestamp(value / 1000, datetime.UTC)
        return super().to_representation(dt)

    def to_internal_value(self, value):  # type: ignore[override]
        dt = super().to_internal_value(value)
        return int(dt.timestamp() * 1000)

    def initial_value(self):
        return self.to_representation(self.current_time_ms())

    def current_time_ms(self):
        return int(datetime.datetime.utcnow().timestamp() * 1000)


class ThriftEnumField(Field):
    def __init__(self, enumClass, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enumClass = enumClass

    def to_representation(self, value):  # type: ignore[override]
        if value is None:
            return None
        return value.name

    def to_internal_value(self, data):
        if self.allow_null and data is None:
            return None
        try:
            return self.enumClass[data]
        except KeyError as e:
            raise ValidationError(f"'{data}' is not a valid name for enum {self.enumClass.__name__}") from e


def create_serializer(thrift_data_type, enable_date_time_conversion=False, **kwargs):
    """
    Create a DRF serializer based on the data type.
    :param thrift_data_type: Data type class (with thrift_spec)
    :param kwargs: Other Django Framework Serializer initialization parameters
    :param enable_date_time_conversion: enable conversion of fields ending with 'time'
    :return: instance of custom serializer for the given data type
    """
    return create_serializer_class(thrift_data_type, enable_date_time_conversion)(**kwargs)


def create_serializer_class(thrift_data_type, enable_date_time_conversion=False):
    class CustomSerializerMeta(SerializerMetaclass):
        def __new__(cls, name, bases, attrs):
            meta = attrs.get("Meta", None)
            thrift_spec = thrift_data_type.thrift_spec
            for field in thrift_spec:
                if field and field[2] not in attrs:
                    required = field[2] in meta.required if meta and hasattr(meta, "required") else False
                    read_only = field[2] in meta.read_only if meta and hasattr(meta, "read_only") else False
                    allow_null = not required
                    field_serializer = process_field(
                        field,
                        enable_date_time_conversion,
                        required=required,
                        read_only=read_only,
                        allow_null=allow_null,
                    )
                    attrs[field[2]] = field_serializer
            return super().__new__(cls, name, bases, attrs)

    class CustomSerializer(Serializer, metaclass=CustomSerializerMeta):
        """
        Custom Serializer which handles list fields holding custom class objects.
        """

        def process_nested_fields(self, validated_data):
            fields = self.fields
            params = copy.deepcopy(validated_data)
            for field_name, serializer in fields.items():
                if isinstance(serializer, (ListField, ListSerializer)):
                    if params.get(field_name, None) is not None or not serializer.allow_null:
                        if isinstance(serializer.child, Serializer):
                            if (
                                field_name == "experimentInputs"
                                and "type" in serializer.child.fields
                                or field_name == "experimentOutputs"
                                and "type" in serializer.child.fields
                            ):
                                for item in params[field_name]:
                                    if "type" in item and isinstance(item["type"], int):
                                        item["type"] = DataType(item["type"])
                            elif field_name == "experimentStatus" and "state" in serializer.child.fields:
                                for item in params[field_name]:
                                    if "state" in item and isinstance(item["state"], int):
                                        item["state"] = ExperimentState(item["state"])
                            params[field_name] = [serializer.child.create(item) for item in params[field_name]]
                        else:
                            params[field_name] = serializer.to_representation(params[field_name])
                elif isinstance(serializer, Serializer) and field_name in params and params[field_name] is not None:
                    params[field_name] = serializer.create(params[field_name])
            return params

        def create(self, validated_data):
            params = self.process_nested_fields(validated_data)

            # Remove fields with None values when they have defaults
            thrift_spec = thrift_data_type.thrift_spec
            for field_spec in thrift_spec:
                if field_spec:
                    field_name = field_spec[2]
                    default_value = field_spec[4]
                    if default_value is not None and field_name in params and params[field_name] is None:
                        del params[field_name]

            if (
                thrift_data_type.__name__ == "ExperimentModel"
                and "experimentType" in params
                and isinstance(params["experimentType"], int)
            ):
                params["experimentType"] = ExperimentType(params["experimentType"])

            if (
                thrift_data_type.__name__ == "ApplicationDeploymentDescription"
                and "parallelism" in params
                and isinstance(params["parallelism"], int)
            ):
                params["parallelism"] = ApplicationParallelismType(params["parallelism"])

            return thrift_data_type(**params)

        def update(self, instance, validated_data):
            return self.create(validated_data)

    return CustomSerializer


def process_field(field, enable_date_time_conversion, required=False, read_only=False, allow_null=False):
    if field[1] in mapping:
        field_class = mapping[field[1]]
        kwargs = dict(required=required, read_only=read_only)
        if field_class not in (BooleanField,):
            kwargs["allow_null"] = allow_null
        if field_class == CharField:
            kwargs["allow_blank"] = allow_null
        if field_class == DecimalField:
            kwargs["max_digits"] = 65
            kwargs["decimal_places"] = 30
        thrift_model_class = mapping[field[1]]

        if (
            thrift_model_class == IntegerField
            and field[3] is not None
            and isinstance(field[3], type)
            and issubclass(field[3], enum.IntEnum)
        ):
            return ThriftEnumField(field[3], required=required, read_only=read_only, allow_null=allow_null)

        if enable_date_time_conversion and thrift_model_class == IntegerField and field[2].lower().endswith("time"):
            thrift_model_class = UTCPosixTimestampDateTimeField
        return thrift_model_class(**kwargs)
    elif field[1] == TTYPE_LIST:
        list_field_serializer = process_list_field(field)
        return ListField(child=list_field_serializer, required=required, read_only=read_only, allow_null=allow_null)
    elif field[1] == TTYPE_STRUCT:
        return create_serializer(field[3][0], required=required, read_only=read_only, allow_null=allow_null)


def process_list_field(field):
    list_details = field[3]
    item_ttype = list_details[0]
    item_type_info = list_details[1]

    if (
        item_ttype == TTYPE_I32
        and item_type_info is not None
        and isinstance(item_type_info, type)
        and issubclass(item_type_info, enum.IntEnum)
    ):
        return ThriftEnumField(item_type_info)

    if item_ttype in mapping:
        field_cls = mapping[item_ttype]
        if field_cls == DecimalField:
            return field_cls(max_digits=65, decimal_places=30)
        return field_cls()
    elif item_ttype == TTYPE_STRUCT:
        return create_serializer(item_type_info[0])
