from django.db import migrations


def create_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    Locale = apps.get_model("wagtailcore.Locale")
    HomePage = apps.get_model("home.HomePage")

    # This migration depends on the full HomePage schema (FKs to wagtailimages /
    # wagtailcore.Page), so it runs after wagtailcore is fully migrated. Remove
    # the default Site and welcome Page created by wagtailcore.0002_initial_data
    # (delete the Site first; Page.delete would otherwise be blocked by the FK).
    Site.objects.filter(hostname="localhost").delete()
    page_content_type = ContentType.objects.get(
        model="page", app_label="wagtailcore"
    )
    Page.objects.filter(
        content_type=page_content_type, slug="home", depth=2
    ).delete()

    # Create content type for homepage model
    homepage_content_type, __ = ContentType.objects.get_or_create(
        model="homepage", app_label="home"
    )

    # The default locale exists by now (wagtailcore.0054_initial_locale).
    locale = Locale.objects.first()

    # Create a new homepage
    homepage = HomePage.objects.create(
        title="Home",
        draft_title="Home",
        slug="home",
        content_type=homepage_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        locale_id=locale.pk,
    )

    # Create a site with the new homepage set as the root
    Site.objects.create(hostname="localhost", root_page=homepage, is_default_site=True)


def remove_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model("contenttypes.ContentType")
    HomePage = apps.get_model("home.HomePage")

    # Delete the default homepage
    # Page and Site objects CASCADE
    HomePage.objects.filter(slug="home", depth=2).delete()

    # Delete content type for homepage model
    ContentType.objects.filter(model="homepage", app_label="home").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_homepage, remove_homepage),
    ]
