import logging

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import reverse
from django.template import Context

from django_airavata.apps.api.signals import user_added_to_group

from . import models, utils

log = logging.getLogger(__name__)


@receiver(user_added_to_group, dispatch_uid="auth_email_user_added_to_group")
def email_user_added_to_group(sender, user, groups, request, **kwargs):
    context = Context({
        "email": user.emails[0],
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.user_id,
        "portal_title": settings.PORTAL_TITLE,
        "dashboard_url": request.build_absolute_uri(
            reverse("django_airavata_workspace:dashboard")),
        "experiments_url": request.build_absolute_uri(
            reverse("django_airavata_workspace:experiments")),
        "group_names": [g.name for g in groups]
    })
    utils.send_email_to_user(models.USER_ADDED_TO_GROUP_TEMPLATE, context)


@receiver(user_logged_in, dispatch_uid="auth_initialize_user_profile")
def initialize_user_profile(sender, request, user, **kwargs):
    """Initialize user profile in Airavata in case this is a new user."""
    # NOTE: if the user verified their email address then they should already
    # have an Airavata user profile (See IAMAdminServices.enableUser). The
    # following is necessary for users coming from federated login who don't
    # need to verify their email.
    if request.authz_token is None:
        return
    try:
        exists = request.airavata.iam.does_user_exist(
            user.username, settings.GATEWAY_ID)
    except Exception:
        log.warning("Could not check Airavata user existence for %s",
                    user.username, exc_info=True)
        return
    if not exists:
        if user.user_profile.is_complete:
            # New federated-login user with a complete profile. Inform admins;
            # the Airavata user profile is provisioned server-side on first
            # authenticated request.
            utils.send_new_user_email(
                request, user.username, user.email, user.first_name,
                user.last_name)
            log.info("sent new user email for user {}".format(user.username))
        else:
            log.info(f"user profile not complete for {user.username}, "
                     "skipping initializing Airavata user profile")

    else:
        log.warning(f"Logged in user {user.username} has no access token")
