from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_airavata_api", "0010_add_default_project_created"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workspacepreferences",
            name="most_recent_group_resource_profile_id",
        ),
    ]
