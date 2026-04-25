import re

from rest_framework import serializers


WALLTIME_RE = re.compile(r"^\d{1,3}:[0-5]\d:[0-5]\d$")


class RuntimeSerializer(serializers.Serializer):
    compute_resource_id = serializers.CharField()
    partition = serializers.CharField()
    walltime = serializers.CharField()
    nodes = serializers.IntegerField(min_value=1)
    cpus_per_node = serializers.IntegerField(min_value=1)

    def validate_walltime(self, value: str) -> str:
        if not WALLTIME_RE.match(value):
            raise serializers.ValidationError("walltime must match HH:MM:SS or HHH:MM:SS")
        return value


class StorageRefSerializer(serializers.Serializer):
    storage_id = serializers.CharField()
    path = serializers.CharField()


class ExperimentDraftSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=256)
    project_id = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    app_id = serializers.CharField()
    interface_name = serializers.CharField()
    inputs = serializers.DictField(child=serializers.JSONField())
    outputs = serializers.DictField(child=StorageRefSerializer())
    runtime = RuntimeSerializer()

    def validate_inputs(self, value):
        scalar_types = (str, int, float, bool)
        for name, v in value.items():
            if isinstance(v, dict):
                StorageRefSerializer(data=v).is_valid(raise_exception=True)
            elif not isinstance(v, scalar_types):
                raise serializers.ValidationError(
                    {name: "input must be a scalar (str/int/float/bool) or a {storage_id, path} object"}
                )
        return value


class PreviewResponseSerializer(serializers.Serializer):
    invocation_command = serializers.CharField()
    script_contents = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField(), default=list)
