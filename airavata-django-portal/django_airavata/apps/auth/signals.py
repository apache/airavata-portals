import logging

import requests
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.template import Context
from django.urls import reverse

from django_airavata.apps.api.signals import user_added_to_group
from django_airavata.utils import create_airavata_client

from . import models, utils

log = logging.getLogger(__name__)

GATEWAY_PROJECT_NAME = "Gateway"


@receiver(user_added_to_group, dispatch_uid="auth_email_user_added_to_group")
def email_user_added_to_group(sender, user, groups, request, **kwargs):
    context = Context(
        {
            "email": user.emails[0],
            "first_name": user.firstName,
            "last_name": user.lastName,
            "username": user.userId,
            "portal_title": settings.PORTAL_TITLE,
            "dashboard_url": request.build_absolute_uri(reverse("django_airavata_workspace:applications")),
            "experiments_url": request.build_absolute_uri(reverse("django_airavata_workspace:applications")),
            "group_names": [g.name for g in groups],
        }
    )
    utils.send_email_to_user(models.USER_ADDED_TO_GROUP_TEMPLATE, context)


@receiver(user_logged_in, dispatch_uid="auth_initialize_user_profile")
def initialize_user_profile(sender, request, user, **kwargs):
    """Register a UserProfile in the Airavata IAM registry on first login.

    Portal user identity comes from Keycloak; the Airavata server maintains a
    separate UserProfile row for API-level authorization. This handler is
    idempotent: it checks `does_user_exist` and returns early if the profile
    already exists. Must run before `provision_user_projects` so that
    downstream SearchProjects calls (which validate user-exists) succeed.
    """
    if request.authz_token is None:
        log.warning(f"Logged in user {user.username} has no access token")
        return
    try:
        iam_client = create_airavata_client(request.authz_token["accessToken"], settings.GATEWAY_ID).iam
        if iam_client.does_user_exist(user.username, settings.GATEWAY_ID):
            return
        if not user.user_profile.is_complete:
            log.info(f"user profile not complete for {user.username}, skipping initializing Airavata user profile")
            return
        from airavata_sdk.generated.org.apache.airavata.model.user.user_profile_pb2 import (
            Status,
            UserProfile,
        )
        profile = UserProfile(
            user_model_version="1.0.0",
            user_id=user.username,
            gateway_id=settings.GATEWAY_ID,
            emails=[user.email] if user.email else [],
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            state=Status.ACTIVE,
        )
        iam_client.add_user_profile(profile)
        log.info(f"initialized user profile for {user.username}")
        utils.send_new_user_email(request, user.username, user.email, user.first_name, user.last_name)
        log.info(f"sent new user email for user {user.username}")
    except Exception as e:
        log.warning(f"initialize_user_profile failed for {user.username}: {e}")


@receiver(user_logged_in, dispatch_uid="auth_project_auto_provisioning")
def provision_user_projects(sender, request, user, **kwargs):
    """Idempotently ensure the user has a personal project and Gateway project membership.

    Runs on every login. Both steps are best-effort: failures are logged but do not
    block login. The Gateway project itself is created by DevGatewayInitializer on
    the server side; if it's missing we skip the membership step gracefully.
    """
    if request.authz_token is None:
        return
    try:
        access_token = request.authz_token["accessToken"]
    except (TypeError, KeyError):
        log.debug(f"no access token for {user.username}, skipping project provisioning")
        return

    try:
        client = create_airavata_client(access_token, settings.GATEWAY_ID, user.username)
    except Exception as e:
        log.warning(f"could not build airavata client for {user.username}, skipping project provisioning: {e}")
        return

    try:
        _ensure_personal_project(client, user.username)
    except Exception as e:
        log.warning(f"personal project provisioning failed for {user.username}: {e}")

    # Gateway project membership uses REST because the AddProjectMember / ListProjectMembers
    # gRPC stubs haven't been regenerated in the Python SDK yet (Task 18). HTTP/JSON
    # transcoding on the Armeria server exposes the same RPC at /api/v1/projects/...
    try:
        _ensure_gateway_membership(access_token, user.username)
    except Exception as e:
        log.warning(f"gateway membership provisioning failed for {user.username}: {e}")


def _ensure_personal_project(airavata_client, username):
    """Create a project named `username` owned by `username` if it doesn't already exist."""
    projects = airavata_client.research.get_user_projects(settings.GATEWAY_ID, username, -1, 0)
    for p in projects:
        if p.name == username:
            log.debug(f"personal project already exists for {username} (id={p.project_id})")
            return
    from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
        Project as ProjectProto,
    )
    # Only pass fields defined on the current generated pb2. The new fields from
    # Task 3 (is_system, admins, members) will become available after Task 18
    # regenerates the Python SDK stubs. In the meantime the server defaults them
    # correctly (is_system=false, admins/members empty) and the portal can add
    # members via the membership RPCs.
    proto_kwargs = {
        "owner": username,
        "gateway_id": settings.GATEWAY_ID,
        "name": username,
        "description": "Your personal workspace.",
    }
    field_names = {f.name for f in ProjectProto.DESCRIPTOR.fields}
    if "is_system" in field_names:
        proto_kwargs["is_system"] = False
    if "admins" in field_names:
        proto_kwargs["admins"] = [username]
    if "members" in field_names:
        proto_kwargs["members"] = [username]
    proto = ProjectProto(**proto_kwargs)
    project_id = airavata_client.research.create_project(settings.GATEWAY_ID, proto)
    log.info(f"Created personal project '{username}' (id={project_id}) for user {username}")


def _airavata_rest_base_url():
    scheme = "https" if getattr(settings, "AIRAVATA_API_SECURE", False) else "http"
    return f"{scheme}://{settings.AIRAVATA_API_HOST}:{settings.AIRAVATA_API_PORT}"


def _ensure_gateway_membership(access_token, username):
    """Self-enrol the caller into all system projects of their gateway.

    Calls the server's ``JoinSystemProjects`` RPC (exposed at
    ``POST /api/v1/projects/join-system``). The server looks up all projects
    flagged ``is_system=true`` in the caller's gateway and inserts
    PROJECT_MEMBER rows idempotently. Self-service — no admin permission
    required — because the caller can only enrol themselves.
    """
    import json as _json
    base = _airavata_rest_base_url()
    # Armeria's HTTP/JSON transcoding path strips to gRPC, so the GrpcAuthInterceptor
    # looks for identity in the x-claims header (not the JWT). Pass userName +
    # gatewayID there so the server-side RequestContext is populated.
    claims = _json.dumps({"userName": username, "gatewayID": settings.GATEWAY_ID})
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-claims": claims,
    }
    join_url = f"{base}/api/v1/projects/join-system"
    try:
        resp = requests.post(join_url, json={}, headers=headers, timeout=10)
    except requests.RequestException as e:
        log.warning(f"join_system_projects HTTP error for {username}: {e}")
        return
    if resp.status_code in (200, 204):
        log.info(f"Enrolled {username} into system projects for gateway {settings.GATEWAY_ID}")
    else:
        log.warning(
            f"join_system_projects returned {resp.status_code} for {username}: {resp.text[:200]}"
        )
    return


def _ensure_gateway_membership_legacy_unused(access_token, username):  # noqa: F401 - kept for reference
    """Legacy — replaced by the server-side JoinSystemProjects RPC. Not called."""
    base = _airavata_rest_base_url()
    headers = {"Authorization": f"Bearer {access_token}"}
    search_url = f"{base}/api/v1/projects"
    try:
        resp = requests.get(
            search_url,
            params={
                "gateway_id": settings.GATEWAY_ID,
                "user_name": username,
                "filters[PROJECT_NAME]": GATEWAY_PROJECT_NAME,
                "limit": -1,
                "offset": 0,
            },
            headers=headers,
            timeout=10,
        )
    except requests.RequestException as e:
        log.warning(f"Gateway project lookup HTTP error for {username}: {e}")
        return

    if resp.status_code != 200:
        log.warning(f"Gateway project lookup returned {resp.status_code} for {username}: {resp.text[:200]}")
        return

    payload = resp.json() or {}
    candidates = payload.get("projects", []) or []
    gateway_project = None
    for proj in candidates:
        if proj.get("name") == GATEWAY_PROJECT_NAME and proj.get("is_system"):
            gateway_project = proj
            break
    if gateway_project is None:
        log.info(
            f"Gateway system project not found in {settings.GATEWAY_ID}; "
            f"skipping membership for {username} (will be retried on next login)"
        )
        return

    project_id = gateway_project.get("project_id")
    if not project_id:
        log.warning(f"Gateway project entry missing project_id: {gateway_project}")
        return

    # Check current members — skip the add if user is already a member. This avoids
    # depending on the server's add-is-idempotent semantics.
    members_url = f"{base}/api/v1/projects/{project_id}/members"
    try:
        members_resp = requests.get(members_url, headers=headers, timeout=10)
    except requests.RequestException as e:
        log.warning(f"list_project_members HTTP error for {project_id}: {e}")
        return

    if members_resp.status_code == 200:
        body = members_resp.json() or {}
        existing_members = set(body.get("members", []) or [])
        if username in existing_members:
            log.debug(f"{username} is already a member of Gateway project {project_id}")
            return
    elif members_resp.status_code in (403, 404):
        # Can't list members (not an admin, etc.) — fall through and attempt add anyway.
        log.debug(f"list_project_members returned {members_resp.status_code}; attempting add")
    else:
        log.warning(
            f"list_project_members returned {members_resp.status_code} for {project_id}: "
            f"{members_resp.text[:200]}"
        )
        # Still attempt the add — the server will reject duplicates cleanly.

    add_url = f"{base}/api/v1/projects/{project_id}/members"
    try:
        add_resp = requests.post(
            add_url,
            json={"project_id": project_id, "user_name": username},
            headers=headers,
            timeout=10,
        )
    except requests.RequestException as e:
        log.warning(f"add_project_member HTTP error for {project_id}/{username}: {e}")
        return

    if add_resp.status_code in (200, 204):
        log.info(f"Added {username} to Gateway project (id={project_id})")
    elif add_resp.status_code == 409:
        log.debug(f"{username} already a member of Gateway project {project_id}")
    else:
        log.warning(
            f"add_project_member returned {add_resp.status_code} for {project_id}/{username}: "
            f"{add_resp.text[:200]}"
        )
