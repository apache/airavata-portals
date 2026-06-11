# Remove the Django-side account surface (user profiles, extended user profile
# fields/values, email verification, password reset, pending email change).
# Login and account self-service are now hosted by Keycloak; only EmailTemplate
# is retained. Models are deleted leaf-first so foreign keys / multi-table
# inheritance parent links are dropped before their targets (DROP TABLE only,
# which avoids the SQLite table-remake path that chokes on primary-key removal).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_airavata_auth', '0019_auto_20221118_1323'),
    ]

    operations = [
        # Standalone tables.
        migrations.DeleteModel(name='EmailVerification'),
        migrations.DeleteModel(name='PasswordResetRequest'),

        # Child choice tables.
        migrations.DeleteModel(name='ExtendedUserProfileMultiChoiceValueChoice'),
        migrations.DeleteModel(name='ExtendedUserProfileSingleChoiceFieldChoice'),
        migrations.DeleteModel(name='ExtendedUserProfileMultiChoiceFieldChoice'),
        migrations.DeleteModel(name='ExtendedUserProfileFieldLink'),

        # Extended-user-profile value MTI children, then the base value.
        migrations.DeleteModel(name='ExtendedUserProfileTextValue'),
        migrations.DeleteModel(name='ExtendedUserProfileSingleChoiceValue'),
        migrations.DeleteModel(name='ExtendedUserProfileMultiChoiceValue'),
        migrations.DeleteModel(name='ExtendedUserProfileAgreementValue'),
        migrations.DeleteModel(name='ExtendedUserProfileValue'),

        # Extended-user-profile field MTI children, then the base field.
        migrations.DeleteModel(name='ExtendedUserProfileTextField'),
        migrations.DeleteModel(name='ExtendedUserProfileSingleChoiceField'),
        migrations.DeleteModel(name='ExtendedUserProfileMultiChoiceField'),
        migrations.DeleteModel(name='ExtendedUserProfileAgreementField'),
        migrations.DeleteModel(name='ExtendedUserProfileField'),

        # User-profile-linked tables, then the user profile itself.
        migrations.DeleteModel(name='UserInfo'),
        migrations.DeleteModel(name='IDPUserInfo'),
        migrations.DeleteModel(name='PendingEmailChange'),
        migrations.DeleteModel(name='UserProfile'),
    ]
