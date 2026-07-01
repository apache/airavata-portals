"""IAM admin operations via the raw IamAdminService gRPC stub.

These operations run in admin/service contexts (e.g. the user-management admin
views), so they use a Keycloak **service-account** token rather than a logged-in
user's token. Each call builds a short-lived Bearer-authenticated channel scoped
to that token and talks to the raw ``IamAdminServiceStub``; callers consume the
returned protobuf ``UserProfile`` directly (``user_id``/``first_name``/
``last_name``/``emails``).

``update_username`` talks to the Keycloak admin REST API directly (not the gRPC
backend).
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from airavata.services import iam_admin_service_pb2 as pb2
from django.conf import settings

from django_airavata.airavata_grpc import build_airavata_channel

from . import utils

if TYPE_CHECKING:
    from collections.abc import Iterator

    from airavata.model.user.user_profile_pb2 import UserProfile
    from airavata.services.iam_admin_service_pb2_grpc import IamAdminServiceStub

logger = logging.getLogger(__name__)


@contextmanager
def _iam() -> Iterator[IamAdminServiceStub]:
    """Yield the IamAdminService stub on a channel scoped to the Keycloak service
    account. The server derives the caller's gateway from the verified
    service-account token."""
    from airavata.services.iam_admin_service_pb2_grpc import (
        IamAdminServiceStub,
    )

    access_token = utils.get_service_account_authz_token().accessToken
    if access_token is None:
        raise RuntimeError("Keycloak service account returned no access token")
    channel = build_airavata_channel(access_token)
    try:
        yield IamAdminServiceStub(channel)
    finally:
        channel.close()


def is_username_available(username: str) -> bool:
    with _iam() as iam:
        return iam.IsUsernameAvailable(
            pb2.IsUsernameAvailableRequest(username=username)
        ).available


def enable_user(username: str) -> None:
    with _iam() as iam:
        iam.EnableUser(pb2.EnableUserRequest(username=username))


def delete_user(username: str) -> None:
    with _iam() as iam:
        iam.DeleteUser(pb2.DeleteUserRequest(username=username))


def get_user(username: str) -> UserProfile:
    with _iam() as iam:
        return iam.GetUser(pb2.GetIamUserRequest(username=username))


def get_users(offset: int, limit: int, search: str | None = None) -> list[UserProfile]:
    with _iam() as iam:
        return list(
            iam.GetUsers(
                pb2.GetIamUsersRequest(offset=offset, limit=limit, search=search or "")
            ).users
        )


def update_username(username: str, new_username: str) -> None:
    # make sure that new_username is available
    if not is_username_available(new_username):
        raise Exception(
            f"Can't change username of {username} to {new_username} because it is not available"
        )
    # fetch user representation
    authz_token = utils.get_service_account_authz_token()
    headers = {"Authorization": f"Bearer {authz_token.accessToken}"}
    parsed = urlparse(settings.KEYCLOAK_AUTHORIZE_URL)
    r = requests.get(
        f"{parsed.scheme}://{parsed.netloc}/auth/admin/realms/{settings.GATEWAY_ID}/users",
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
        f"{parsed.scheme}://{parsed.netloc}/auth/admin/realms/{settings.GATEWAY_ID}/users/{user['id']}",
        json=user,
        headers=headers,
    )
    r.raise_for_status()
