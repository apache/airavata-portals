# The portal has no database. The former EmailTemplate table is replaced by
# settings.PORTAL_EMAIL_TEMPLATES (rendered in apps/auth/utils.send_email_to_user).
# Only the "user added to group" notification is still sent from the portal
# (verify-email, password-reset, etc. are handled by Keycloak), so only its
# template-type key remains.

USER_ADDED_TO_GROUP_TEMPLATE = 4
