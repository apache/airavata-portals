from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.dispatch import receiver
from django.shortcuts import reverse
from django.template import Context

from django_airavata.apps.api.signals import user_added_to_group

from . import utils
from .constants import USER_ADDED_TO_GROUP_TEMPLATE

if TYPE_CHECKING:
    from airavata.model.group.group_manager_pb2 import GroupModel
    from airavata.model.user.user_profile_pb2 import UserProfile
    from django.http import HttpRequest

log = logging.getLogger(__name__)


@receiver(user_added_to_group, dispatch_uid="auth_email_user_added_to_group")
def email_user_added_to_group(
    sender: Any,
    user: UserProfile,
    groups: list[GroupModel],
    request: HttpRequest,
    **kwargs: Any,
) -> None:
    context = Context(
        {
            "email": user.emails[0],
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.user_id,
            "portal_title": settings.PORTAL_TITLE,
            "dashboard_url": request.build_absolute_uri(
                reverse("django_airavata_workspace:dashboard")
            ),
            "experiments_url": request.build_absolute_uri(
                reverse("django_airavata_workspace:experiments")
            ),
            "group_names": [g.name for g in groups],
        }
    )
    utils.send_email_to_user(USER_ADDED_TO_GROUP_TEMPLATE, context)
