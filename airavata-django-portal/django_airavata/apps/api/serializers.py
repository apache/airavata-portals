from __future__ import annotations

import json
import logging
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from airavata.model.group import group_manager_pb2

    from django_airavata.apps.api.helpers import WorkspacePreferences
    from django_airavata.apps.api.queue_settings import QueueSettingsCalculator
    from django_airavata.request import AiravataRequest

log = logging.getLogger(__name__)


def user_has_access(
    request: AiravataRequest, resource_id: str, permission: str = "WRITE"
) -> bool:
    """gRPC sharing access check (Track D — replaces the Thrift userHasAccess).

    ``permission`` is the ResourcePermissionType enum name (WRITE/READ/OWNER/
    MANAGE_SHARING); the backend prefixes the gateway internally. The acting user
    is taken from the authenticated token context server-side, so ``user_id`` is
    passed for the request shape but ignored by the backend.
    """
    from airavata.services import sharing_service_pb2 as pb2
    from airavata.services.sharing_service_pb2_grpc import (
        SharingServiceStub,
    )

    response = SharingServiceStub(request.airavata_channel).UserHasAccess(
        pb2.UserHasAccessRequest(
            resource_id=resource_id,
            user_id=request.user.username,
            permission_type=permission,
        )
    )
    return response.has_access


def _credential_store_pb2() -> ModuleType:
    from airavata.model.credential.store import (
        credential_store_pb2,
    )

    return credential_store_pb2


def workspace_preferences_data(
    workspace_preferences: WorkspacePreferences,
) -> dict[str, Any]:
    # Read-only; matches the old ModelSerializer (exclude username, nest the
    # application_preferences child list).
    return {
        "most_recent_project_id": workspace_preferences.most_recent_project_id,
        "most_recent_group_resource_profile_id": workspace_preferences.most_recent_group_resource_profile_id,
        "most_recent_compute_resource_id": workspace_preferences.most_recent_compute_resource_id,
        "application_preferences": [
            {"application_id": app_id, "favorite": favorite}
            for app_id, favorite in workspace_preferences.application_favorites.items()
        ],
    }


# IAM user write path (read/output is the SDK pydantic IAMUser). The old
# camelCase IAMUserProfile body is validated for its required field set; the
# group-membership diff drives the add/remove the view applies.
_IAM_USER_REQUIRED_FIELDS = (
    "airavataInternalUserId",
    "userId",
    "gatewayId",
    "email",
    "firstName",
    "lastName",
    "enabled",
    "emailVerified",
    "airavataUserProfileExists",
    "creationTime",
    "groups",
)


def validate_iam_user_body(data: Any) -> dict[str, Any]:
    """Validate the camelCase IAM user body, reproducing the old serializer's
    required-field 400 shape (``{field: ['This field is required.']}``)."""
    if not isinstance(data, dict):
        raise ValidationError("Invalid request body.")
    errors: dict[str, list[str]] = {}
    for field in _IAM_USER_REQUIRED_FIELDS:
        if data.get(field) is None:
            errors[field] = ["This field is required."]
    if errors:
        raise ValidationError(errors)
    return data


def iam_user_group_diff(
    existing_groups: Sequence[group_manager_pb2.GroupModel], data: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Compute the added/removed group-id diff the view applies.

    ``existing_groups`` are the proto ``GroupModel`` objects the user belongs to;
    the new ids are read from the request ``groups`` dicts by ``id`` (the field
    the frontend sends). Returns ``(added_group_ids, removed_group_ids)``.
    """
    existing_group_ids = [group.id for group in existing_groups]
    new_group_ids = [group["id"] for group in data.get("groups", [])]
    added_group_ids = list(set(new_group_ids) - set(existing_group_ids))
    removed_group_ids = list(set(existing_group_ids) - set(new_group_ids))
    return added_group_ids, removed_group_ids


def parse_update_username(data: Any) -> tuple[str, str]:
    """Validate an update-username body (the full profile plus ``newUsername``),
    returning ``(user_id, new_username)``."""
    validated = validate_iam_user_body(data)
    new_username = validated.get("newUsername")
    if not new_username:
        raise ValidationError({"newUsername": ["This field is required."]})
    return validated["userId"], new_username


class ValidationError(Exception):
    """Carries a DRF-style error mapping (``{field: [messages]}`` or a string)
    so plain validators can produce the 400 body the frontend expects."""

    def __init__(self, detail: Any) -> None:
        self.detail = detail
        super().__init__(detail)


def settings_data(
    file_upload_max_file_size: Any, tus_endpoint: str, pga_url: str
) -> dict[str, Any]:
    # camelCase keys preserved verbatim (frontend Settings.js contract).
    return {
        "fileUploadMaxFileSize": file_upload_max_file_size,
        "tusEndpoint": tus_endpoint,
        "pgaUrl": pga_url,
    }


def parse_log_record(data: Any) -> dict[str, Any]:
    """Validate a posted frontend log record, preserving the legacy
    ``LogRecordSerializer`` shape. ``details`` is stored as a JSON string (the
    old ``StoredJSONField.to_internal_value``) for logging; ``render_log_record``
    decodes it back for the echo response.
    """
    errors: dict[str, list[str]] = {}
    if not isinstance(data, dict):
        raise ValidationError("Invalid log record.")
    level = data.get("level")
    message = data.get("message")
    stacktrace = data.get("stacktrace")
    if not level:
        errors["level"] = ["This field is required."]
    if not message:
        errors["message"] = ["This field is required."]
    if "details" not in data:
        errors["details"] = ["This field is required."]
    if stacktrace is None:
        errors["stacktrace"] = ["This field is required."]
    elif not isinstance(stacktrace, list):
        errors["stacktrace"] = ["Expected a list of items."]
    if errors:
        raise ValidationError(errors)
    try:
        details = json.dumps(data["details"])
    except (TypeError, ValueError) as err:
        raise ValidationError({"details": ["Value must be valid JSON."]}) from err
    return {
        "level": level,
        "message": message,
        "details": details,
        "stacktrace": [str(s) for s in stacktrace],
    }


def render_log_record(validated: dict[str, Any]) -> dict[str, Any]:
    # Mirror the old serializer's read path: details JSON-decoded, rest verbatim.
    try:
        details = (
            json.loads(validated["details"])
            if validated["details"]
            else validated["details"]
        )
    except Exception:
        details = validated["details"]
    return {
        "level": validated["level"],
        "message": validated["message"],
        "details": details,
        "stacktrace": validated["stacktrace"],
    }


def queue_settings_calculator_data(
    calculator: QueueSettingsCalculator,
) -> dict[str, Any]:
    return {"id": calculator.id, "name": calculator.name}
