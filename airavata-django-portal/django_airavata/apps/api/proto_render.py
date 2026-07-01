"""Generic proto-direct → snake_case JSON rendering for migrated ViewSets.

:func:`to_jsonable` turns a return value (a proto ``Message``, a composed pydantic
``BaseModel``, or a list/dict of those) into plain JSON-serializable Python with
snake_case keys; :class:`ProtoJSONRenderer` applies it on the DRF response path.

A raw server ``*WithAccess`` proto — the wrapper shape ``{<resource> = 1,
access = 2}`` where ``access`` is an ``*AccessFlags`` message (see
:func:`_access_envelope_fields`) — is FLATTENED to the resource's fields with the
access flags merged on as siblings. This is what lets a ViewSet return the raw
generated proto from a direct stub call (no helper, no SDK envelope) without
changing the JSON the frontend reads. (The retired ``airavata`` ``_envelope``
dataclasses produced this same flattened shape; the structural detector replaced
them.)

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

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.core.serializers.json import DjangoJSONEncoder
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message

if TYPE_CHECKING:
    from google.protobuf.descriptor import FieldDescriptor

try:  # pydantic is optional on this path; only composed shapes use it
    from pydantic import BaseModel as _PydanticBaseModel
except Exception:  # pragma: no cover - pydantic always present in practice
    _PydanticBaseModel = None  # ty: ignore[invalid-assignment]  # optional-import fallback sentinel

# The single source of truth for how every proto on the read path is rendered.
_MESSAGE_TO_DICT_OPTS: dict[str, bool] = {
    "preserving_proto_field_name": True,
    "always_print_fields_with_no_presence": True,
}


def proto_to_dict(message: Message) -> dict[str, Any]:
    return MessageToDict(message, **_MESSAGE_TO_DICT_OPTS)


def _access_envelope_fields(
    message: Message,
) -> tuple[FieldDescriptor, FieldDescriptor] | None:
    """If ``message`` is a server ``*WithAccess`` wrapper, return its
    ``(resource_field, access_field)`` descriptors; otherwise ``None``.

    The wrapper convention is a two-field message ``{<resource> = 1, access = 2}``
    whose second field is named ``access`` and is an ``*AccessFlags`` message
    (``commons.AccessFlags`` or ``GroupAccessFlags``). Detecting it structurally
    lets the renderer flatten the access flags onto the resource — exactly the
    shape the SDK ``_envelope.WithAccess``/``WithGroupAccess`` produced — so the
    portal can consume raw generated protos and the SDK envelope can be retired.
    """
    descriptor = message.DESCRIPTOR
    # The base ``Message.DESCRIPTOR`` is typed ``None`` in the stubs; every concrete
    # generated message overrides it, so it is always set on a real instance.
    if descriptor is None:
        return None
    fields = descriptor.fields
    if len(fields) != 2:
        return None
    resource_f, access_f = fields
    if resource_f.message_type is None or access_f.message_type is None:
        return None
    if access_f.name != "access" or not access_f.message_type.name.endswith(
        "AccessFlags"
    ):
        return None
    return resource_f, access_f


def to_jsonable(obj: Any) -> Any:
    """Convert an SDK return value into JSON-serializable snake_case Python.

    An envelope (``WithAccess`` / ``WithGroupAccess``) renders its proto and
    merges its access scalars on top — the extras are exactly the cross-service
    fields kept OUT of the proto, so keys never collide. A ``dict`` recurses
    values but passes keys through unchanged (callers here already use snake_case).
    """
    if isinstance(obj, Message):
        env = _access_envelope_fields(obj)
        if env is not None:
            resource_f, access_f = env
            base = to_jsonable(getattr(obj, resource_f.name))
            base.update(proto_to_dict(getattr(obj, access_f.name)))
            return base
        return proto_to_dict(obj)
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if _PydanticBaseModel is not None and isinstance(obj, _PydanticBaseModel):
        # Recurse field-by-field (NOT a flat ``model_dump()``) so a composed
        # model may carry protos / ``WithAccess`` envelopes / nested dicts that
        # the SAME renderer flattens.  Plain JSON-able fields are unchanged.
        return {
            name: to_jsonable(getattr(obj, name)) for name in type(obj).model_fields
        }
    return obj


class ProtoJSONRenderer:
    """Plain JSON renderer that runs :func:`to_jsonable` over the data, then
    JSON-encodes it to bytes. Page views call ``.render(data) -> bytes``."""

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        return json.dumps(to_jsonable(data), cls=DjangoJSONEncoder).encode("utf-8")
