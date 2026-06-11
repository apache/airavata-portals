"""Generic proto-direct → snake_case JSON rendering for migrated ViewSets.

:func:`to_jsonable` turns an SDK return value (a proto ``Message``, a
:class:`~airavata_sdk.helpers._envelope.WithAccess` envelope, a composed pydantic
``BaseModel``, or a list/dict of those) into plain JSON-serializable Python with
snake_case keys; :class:`ProtoJSONRenderer` applies it on the DRF response path.

The ``MessageToDict`` options below are the source-of-truth read contract; the
defaults (enums → member NAMES, int64 → decimal STRING) are deliberate and
relied on by every migrated ViewSet — document any change.

``preserving_proto_field_name=True``  (REQUIRED)
    Emit proto field names verbatim (``project_id``) instead of the
    lowerCamelCase JSON names — this is what makes the output snake_case.

``always_print_fields_with_no_presence=True``
    Emit every singular field even at its default value, so the JSON shape is
    STABLE regardless of which fields the backend populated (the frontend reads a
    fixed key set). Repeated/map and explicit-presence fields are unaffected — an
    unset message stays absent, an empty list stays ``[]``.

Enums render as the member NAME string (rename-stable, frontend-readable);
int64 / uint64 / fixed64 render as decimal STRINGS (they exceed JS ``Number``
safe-integer range), e.g. ``creation_time`` epoch-millis as ``"1705320000000"``.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message

try:  # pydantic is optional on this path; only composed shapes use it
    from pydantic import BaseModel as _PydanticBaseModel
except Exception:  # pragma: no cover - pydantic always present in practice
    _PydanticBaseModel = None

from airavata_sdk.helpers._envelope import WithAccess, WithGroupAccess

# The single source of truth for how every proto on the read path is rendered.
_MESSAGE_TO_DICT_OPTS = dict(
    preserving_proto_field_name=True,
    always_print_fields_with_no_presence=True,
)


def proto_to_dict(message: Message) -> dict:
    return MessageToDict(message, **_MESSAGE_TO_DICT_OPTS)


def to_jsonable(obj):
    """Convert an SDK return value into JSON-serializable snake_case Python.

    An envelope (``WithAccess`` / ``WithGroupAccess``) renders its proto and
    merges its access scalars on top — the extras are exactly the cross-service
    fields kept OUT of the proto, so keys never collide. A ``dict`` recurses
    values but passes keys through unchanged (callers here already use snake_case).
    """
    if isinstance(obj, Message):
        return proto_to_dict(obj)
    if isinstance(obj, WithAccess):
        base = to_jsonable(obj.message)
        base["is_owner"] = obj.is_owner
        base["user_has_write_access"] = obj.user_has_write_access
        return base
    if isinstance(obj, WithGroupAccess):
        base = to_jsonable(obj.message)
        base["is_admin"] = obj.is_admin
        base["is_owner"] = obj.is_owner
        base["is_member"] = obj.is_member
        base["is_gateway_admins_group"] = obj.is_gateway_admins_group
        base["is_read_only_gateway_admins_group"] = \
            obj.is_read_only_gateway_admins_group
        base["is_default_gateway_users_group"] = \
            obj.is_default_gateway_users_group
        return base
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if _PydanticBaseModel is not None and isinstance(obj, _PydanticBaseModel):
        # Recurse field-by-field (NOT a flat ``model_dump()``) so a composed
        # model may carry protos / ``WithAccess`` envelopes / nested dicts that
        # the SAME renderer flattens.  Plain JSON-able fields are unchanged.
        return {
            name: to_jsonable(getattr(obj, name))
            for name in type(obj).model_fields
        }
    return obj


class ProtoJSONRenderer:
    """Plain JSON renderer that runs :func:`to_jsonable` over the data, then
    JSON-encodes it to bytes. Page views call ``.render(data) -> bytes``."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return json.dumps(
            to_jsonable(data), cls=DjangoJSONEncoder).encode('utf-8')
