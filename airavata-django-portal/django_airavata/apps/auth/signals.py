import logging

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.template import Context
from django.urls import reverse

from django_airavata.apps.api.signals import user_added_to_group
from django_airavata.utils import create_airavata_client

from . import models, utils

log = logging.getLogger(__name__)


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
    """Initialize user profile in Airavata in case this is a new user."""
    # NOTE: if the user verified their email address then they should already
    # have an Airavata user profile (See IAMAdminServices.enableUser). The
    # following is necessary for users coming from federated login who don't
    # need to verify their email.
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
        iam_client.initialize_user_profile()
        log.info(f"initialized user profile for {user.username}")
        utils.send_new_user_email(request, user.username, user.email, user.first_name, user.last_name)
        log.info(f"sent new user email for user {user.username}")
    except (AttributeError, Exception) as e:
        log.warning(f"initialize_user_profile failed (IAM RPC may be unimplemented); skipping: {e}")
