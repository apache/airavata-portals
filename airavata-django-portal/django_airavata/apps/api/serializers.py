import json
import logging

log = logging.getLogger(__name__)


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


def _credential_store_pb2():
    from airavata_sdk.generated.org.apache.airavata.model.credential.store import (
        credential_store_pb2,
    )
    return credential_store_pb2


def application_preferences_data(application_preferences):
    # Same field set the old ModelSerializer emitted (exclude id/username/fk).
    return {
        'application_id': application_preferences.application_id,
        'favorite': application_preferences.favorite,
    }


def workspace_preferences_data(workspace_preferences):
    # Read-only; matches the old ModelSerializer (exclude username, nest the
    # application_preferences child list).
    return {
        'most_recent_project_id':
            workspace_preferences.most_recent_project_id,
        'most_recent_group_resource_profile_id':
            workspace_preferences.most_recent_group_resource_profile_id,
        'most_recent_compute_resource_id':
            workspace_preferences.most_recent_compute_resource_id,
        'application_preferences': [
            application_preferences_data(ap)
            for ap in workspace_preferences.applicationpreferences_set.all()],
    }


# IAM user write path (read/output is the SDK pydantic IAMUser). The old
# camelCase IAMUserProfile body is validated for its required field set; the
# group-membership diff drives the add/remove the view applies.
_IAM_USER_REQUIRED_FIELDS = (
    'airavataInternalUserId', 'userId', 'gatewayId', 'email', 'firstName',
    'lastName', 'enabled', 'emailVerified', 'airavataUserProfileExists',
    'creationTime', 'groups',
)


def validate_iam_user_body(data):
    """Validate the camelCase IAM user body, reproducing the old serializer's
    required-field 400 shape (``{field: ['This field is required.']}``)."""
    if not isinstance(data, dict):
        raise ValidationError("Invalid request body.")
    errors = {}
    for field in _IAM_USER_REQUIRED_FIELDS:
        if data.get(field) is None:
            errors[field] = ['This field is required.']
    if errors:
        raise ValidationError(errors)
    return data


def iam_user_group_diff(existing_groups, data):
    """Compute the added/removed group-id diff the view applies.

    ``existing_groups`` are the proto ``GroupModel`` objects the user belongs to;
    the new ids are read from the request ``groups`` dicts by ``id`` (the field
    the frontend sends). Returns ``(added_group_ids, removed_group_ids)``.
    """
    existing_group_ids = [group.id for group in existing_groups]
    new_group_ids = [group['id'] for group in data.get('groups', [])]
    added_group_ids = list(set(new_group_ids) - set(existing_group_ids))
    removed_group_ids = list(set(existing_group_ids) - set(new_group_ids))
    return added_group_ids, removed_group_ids


def parse_update_username(data):
    """Validate an update-username body (the full profile plus ``newUsername``),
    returning ``(user_id, new_username)``."""
    validated = validate_iam_user_body(data)
    new_username = validated.get('newUsername')
    if not new_username:
        raise ValidationError({'newUsername': ['This field is required.']})
    return validated['userId'], new_username


class ValidationError(Exception):
    """Carries a DRF-style error mapping (``{field: [messages]}`` or a string)
    so plain validators can produce the 400 body the frontend expects."""

    def __init__(self, detail):
        self.detail = detail
        super().__init__(detail)


def settings_data(file_upload_max_file_size, tus_endpoint, pga_url):
    # camelCase keys preserved verbatim (frontend Settings.js contract).
    return {
        'fileUploadMaxFileSize': file_upload_max_file_size,
        'tusEndpoint': tus_endpoint,
        'pgaUrl': pga_url,
    }


def parse_log_record(data):
    """Validate a posted frontend log record, preserving the legacy
    ``LogRecordSerializer`` shape. ``details`` is stored as a JSON string (the
    old ``StoredJSONField.to_internal_value``) for logging; ``render_log_record``
    decodes it back for the echo response.
    """
    errors = {}
    if not isinstance(data, dict):
        raise ValidationError("Invalid log record.")
    level = data.get('level')
    message = data.get('message')
    stacktrace = data.get('stacktrace')
    if not level:
        errors['level'] = ['This field is required.']
    if not message:
        errors['message'] = ['This field is required.']
    if 'details' not in data:
        errors['details'] = ['This field is required.']
    if stacktrace is None:
        errors['stacktrace'] = ['This field is required.']
    elif not isinstance(stacktrace, list):
        errors['stacktrace'] = ['Expected a list of items.']
    if errors:
        raise ValidationError(errors)
    try:
        details = json.dumps(data['details'])
    except (TypeError, ValueError):
        raise ValidationError({'details': ['Value must be valid JSON.']})
    return {
        'level': level,
        'message': message,
        'details': details,
        'stacktrace': [str(s) for s in stacktrace],
    }


def render_log_record(validated):
    # Mirror the old serializer's read path: details JSON-decoded, rest verbatim.
    try:
        details = json.loads(validated['details']) if validated['details'] else validated['details']
    except Exception:
        details = validated['details']
    return {
        'level': validated['level'],
        'message': validated['message'],
        'details': details,
        'stacktrace': validated['stacktrace'],
    }


def queue_settings_calculator_data(calculator):
    return {'id': calculator.id, 'name': calculator.name}
