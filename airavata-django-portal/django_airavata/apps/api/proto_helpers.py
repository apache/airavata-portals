"""Thin helpers for proto <-> dict conversion. No business logic."""
from google.protobuf.json_format import MessageToDict, ParseDict


def proto_to_dict(proto_obj):
    """Convert a proto object to a snake_case dict for JSON response."""
    if proto_obj is None:
        return None
    return MessageToDict(proto_obj, preserving_proto_field_name=True)


def proto_list_to_dicts(proto_list):
    """Convert a list of proto objects to a list of snake_case dicts."""
    return [proto_to_dict(p) for p in (proto_list or [])]


def dict_to_proto(data, proto_class):
    """Convert a dict (from request.data) to a proto object."""
    return ParseDict(data, proto_class())
