"""
Wrapper around the IAM Admin Services client.
"""

import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

from django_airavata.utils import create_airavata_client

from . import utils

logger = logging.getLogger(__name__)


def _get_iam_client():
    """Create an AiravataClient using service account credentials and return its IAM sub-client."""
    authz_token = utils.get_service_account_authz_token()
    client = create_airavata_client(authz_token["accessToken"], settings.GATEWAY_ID)
    return client.iam


def is_username_available(username):
    return _get_iam_client().is_username_available(username)


def register_user(username, email_address, first_name, last_name, password):
    return _get_iam_client().register_user(username, email_address, first_name, last_name, password)


def is_user_enabled(username):
    return _get_iam_client().is_user_enabled(username)


def enable_user(username):
    return _get_iam_client().enable_user(username)


def delete_user(username):
    return _get_iam_client().delete_iam_user(username)


def is_user_exist(username):
    return _get_iam_client().is_user_exist(username)


def get_user(username):
    return _get_iam_client().get_iam_user(username)


def get_users(offset, limit, search=None):
    return _get_iam_client().get_iam_users(offset, limit, search or "")


def reset_user_password(username, new_password):
    return _get_iam_client().reset_user_password(username, new_password)


def update_username(username, new_username):
    # make sure that new_username is available
    if not is_username_available(new_username):
        raise Exception(f"Can't change username of {username} to {new_username} because it is not available")
    # fetch user representation
    authz_token = utils.get_service_account_authz_token()
    headers = {"Authorization": f"Bearer {authz_token['accessToken']}"}
    parsed = urlparse(settings.KEYCLOAK_AUTHORIZE_URL)
    r = requests.get(
        f"{parsed.scheme}://{parsed.netloc}/admin/realms/{settings.GATEWAY_ID}/users",
        params={"username": username},
        headers=headers,
    )
    r.raise_for_status()
    user_list = r.json()
    user = None
    # The users search finds partial matches. Loop to find the exact match.
    for u in user_list:
        if u["username"] == username:
            user = u
            break
    if user is None:
        raise Exception(f"Could not find user {username}")

    # update username
    user["username"] = new_username
    r = requests.put(
        f"{parsed.scheme}://{parsed.netloc}/admin/realms/{settings.GATEWAY_ID}/users/{user['id']}",
        json=user,
        headers=headers,
    )
    r.raise_for_status()


def list_user_project_groups(username):
    """
    Return the list of `/projects/<projectId>` groups the user belongs to.

    Under the Keycloak-authoritative identity model, project membership is
    expressed as Keycloak groups under `/projects/`. This helper queries
    Keycloak admin API with the pga client's service-account token and filters
    the user's group memberships down to the project groups. Admins sub-group
    memberships (`/projects/<id>/admins`) are skipped — callers that need
    admin-ness can look at the realm `gateway-admin` role or the `/admins`
    sub-group membership separately.

    Returns a list of dicts: [{"id", "name", "path"}]. Empty list on any error.
    """
    try:
        authz_token = utils.get_service_account_authz_token()
        headers = {"Authorization": f"Bearer {authz_token['accessToken']}"}
        parsed = urlparse(settings.KEYCLOAK_AUTHORIZE_URL)
        base = f"{parsed.scheme}://{parsed.netloc}/admin/realms/{settings.GATEWAY_ID}"
        r = requests.get(f"{base}/users", params={"username": username}, headers=headers, timeout=10)
        r.raise_for_status()
        matches = [u for u in r.json() if u.get("username") == username]
        if not matches:
            return []
        user_id = matches[0]["id"]

        r = requests.get(f"{base}/users/{user_id}/groups", headers=headers, timeout=10)
        r.raise_for_status()
        groups = []
        for g in r.json():
            path = g.get("path", "")
            # Keep only direct project groups (/projects/<id>), skip /admins sub-groups.
            if path.startswith("/projects/") and not path.endswith("/admins"):
                groups.append({"id": g["id"], "name": g["name"], "path": path})
        return groups
    except Exception as e:
        logger.warning(f"Failed to list project groups for {username}: {e}")
        return []


def update_user(username, first_name=None, last_name=None, email=None):
    # fetch user representation
    authz_token = utils.get_service_account_authz_token()
    headers = {"Authorization": f"Bearer {authz_token['accessToken']}"}
    parsed = urlparse(settings.KEYCLOAK_AUTHORIZE_URL)
    r = requests.get(
        f"{parsed.scheme}://{parsed.netloc}/admin/realms/{settings.GATEWAY_ID}/users",
        params={"username": username},
        headers=headers,
    )
    r.raise_for_status()
    user_list = r.json()
    user = None
    # The users search finds partial matches. Loop to find the exact match.
    for u in user_list:
        if u["username"] == username:
            user = u
            break
    if user is None:
        raise Exception(f"Could not find user {username}")

    # update user
    if first_name is not None:
        user["firstName"] = first_name
    if last_name is not None:
        user["lastName"] = last_name
    if email is not None:
        user["email"] = email
    r = requests.put(
        f"{parsed.scheme}://{parsed.netloc}/admin/realms/{settings.GATEWAY_ID}/users/{user['id']}",
        json=user,
        headers=headers,
    )
    r.raise_for_status()
