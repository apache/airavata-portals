"""Portal-side proto construction for the experiments-core write path.

``build_experiment`` maps a form ``data`` dict to a proto ``ExperimentModel`` via
generic protobuf JSON parsing (``google.protobuf.json_format``), which handles
snake_case field names, numeric strings for int fields, and enum names or ints in
any language. Only two policy concerns stay portal-side: build *only*
user-submittable fields, and force ``gateway_id`` / ``user_name`` from the trusted
request context rather than the form.

``proto_enum_value`` stays as a general enum-coercion helper used across the API
views (grp resource type, parallelism, parser IO type, notification priority, ...).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from airavata.model.experiment.experiment_pb2 import ExperimentModel
    from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper


def proto_enum_value[EnumT: int](enum_cls: type[EnumT], value: object) -> EnumT:
    """Resolve a wire value to a proto enum's INT value, with the PROTO enum as
    the single source of type-truth — there is NO Thrift remapping.

    *EnumT* is a proto enum member type — ``class SomeEnum(int, metaclass=
    EnumTypeWrapper)``, so it is an ``int`` subclass; the bound keeps the precise
    type flowing out into proto constructors.

    Accepts the proto member NAME (full proto name, e.g. ``"EXPERIMENT_STATE_CREATED"``,
    or the prefix-stripped short alias, e.g. ``"LOCAL"``) or the proto int as-is;
    ``None`` / ``""`` / bool -> 0 (the proto UNKNOWN sentinel). *enum_cls* is a
    protobuf ``EnumTypeWrapper`` (e.g. ``compute_resource_pb2.JobSubmissionProtocol``).

    The return is typed as the precise enum member type so values flow into proto
    constructors (each enum field wants its own ``SomeEnum`` int subclass).
    """
    # ``.keys()`` / ``.Value()`` / ``.DESCRIPTOR`` live on the EnumTypeWrapper
    # metaclass, which ty can't see through ``type[EnumT]`` — view them through it.
    wrapper = cast("EnumTypeWrapper", enum_cls)
    if value is None or value == "" or isinstance(value, bool):
        return cast(EnumT, 0)
    if isinstance(value, int):
        return cast(EnumT, value)  # already the proto int — pass through, never remap
    name = str(value)
    # ``enum_cls`` is a protobuf EnumTypeWrapper, not a dict — ``.keys()`` is its
    # member-name list, so SIM118's ``in dict`` rewrite would not be equivalent.
    if name in wrapper.keys():  # noqa: SIM118
        return cast(EnumT, wrapper.Value(name))
    # short alias: re-attach the enum's SCREAMING_SNAKE prefix, derived from the
    # 0-sentinel member name (e.g. JOB_SUBMISSION_PROTOCOL_UNKNOWN -> prefix).
    # ``EnumTypeWrapper.DESCRIPTOR`` is typed ``None`` (its class-body default), but
    # is set to the real ``EnumDescriptor`` on every constructed wrapper.
    descriptor = wrapper.DESCRIPTOR
    if descriptor is None:
        return cast(EnumT, 0)
    zero = descriptor.values_by_number.get(0)
    if zero is not None and "_" in zero.name:
        prefix = zero.name[: zero.name.rfind("_") + 1]
        if (prefix + name) in wrapper.keys():  # noqa: SIM118
            return cast(EnumT, wrapper.Value(prefix + name))
    return cast(EnumT, 0)


# user-submittable ExperimentModel fields; status / errors / processes / workflow
# and the other server-managed fields (creation_time, gateway_execution_id, ...)
# are never built from the form, and gateway_id / user_name are forced from the
# trusted request context below.
_USER_FIELDS = frozenset(
    {
        "experiment_id",
        "project_id",
        "experiment_type",
        "experiment_name",
        "description",
        "execution_id",
        "enable_email_notification",
        "email_addresses",
        "experiment_inputs",
        "experiment_outputs",
        "user_configuration_data",
    }
)


def _clean(value: Any) -> Any:
    """Recursively drop blank scalars (``None`` / ``""``) so cleared form fields
    stay unset — this is what keeps ParseDict from choking on ``""`` in int / enum
    fields. Empty dicts survive (a message field submitted as ``{}`` must keep its
    presence) and scalar list entries pass through untouched (a blank email
    address is preserved, matching the old builder). ``meta_data`` is stringified
    because the proto field is a string, mirroring the old ``_meta_data_str``.
    """
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for k, v in value.items():
            if k == "meta_data" and v is not None and not isinstance(v, str):
                try:
                    v = json.dumps(v)
                except (TypeError, ValueError):
                    v = ""
            cv = _clean(v)
            if cv is None or cv == "":
                continue
            cleaned[k] = cv
        return cleaned
    if isinstance(value, list):
        return [_clean(v) if isinstance(v, dict) else v for v in value]
    return value


def build_experiment(
    gateway_id: str,
    user_name: str,
    data: dict[str, Any],
) -> ExperimentModel:
    """Assemble a proto ``ExperimentModel`` from a form *data* dict (no RPC).

    Generic protobuf JSON parsing does the field mapping (snake_case names,
    numeric strings for ints, enum names or ints), so only the two policy
    concerns stay here: build *only* user-submittable fields, and force
    ``gateway_id`` / ``user_name`` from the trusted args rather than the form.
    """
    from airavata.model.experiment import experiment_pb2
    from google.protobuf import json_format

    cleaned = {k: v for k, v in _clean(data).items() if k in _USER_FIELDS}
    exp = json_format.ParseDict(
        cleaned, experiment_pb2.ExperimentModel(), ignore_unknown_fields=True
    )
    exp.gateway_id = gateway_id or ""
    exp.user_name = user_name or ""
    return exp
