from django.db import models

VERIFY_EMAIL_TEMPLATE = 1
NEW_USER_EMAIL_TEMPLATE = 2
PASSWORD_RESET_EMAIL_TEMPLATE = 3
USER_ADDED_TO_GROUP_TEMPLATE = 4
VERIFY_EMAIL_CHANGE_TEMPLATE = 5
USER_PROFILE_COMPLETED_TEMPLATE = 6


class EmailTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = (
        (VERIFY_EMAIL_TEMPLATE, 'Verify Email Template'),
        (NEW_USER_EMAIL_TEMPLATE, 'New User Email Template'),
        (PASSWORD_RESET_EMAIL_TEMPLATE, 'Password Reset Email Template'),
        (USER_ADDED_TO_GROUP_TEMPLATE, 'User Added to Group Template'),
        (VERIFY_EMAIL_CHANGE_TEMPLATE, 'Verify Email Change Template'),
        (USER_PROFILE_COMPLETED_TEMPLATE, 'User Profile Completed Template'),
    )
    template_type = models.IntegerField(
        primary_key=True, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        for choice in self.TEMPLATE_TYPE_CHOICES:
            if self.template_type == choice[0]:
                return choice[1]
        return "Unknown"
