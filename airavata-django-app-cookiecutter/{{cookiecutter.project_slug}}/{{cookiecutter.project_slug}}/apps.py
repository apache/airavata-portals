import os

from django.apps import AppConfig


class {{ cookiecutter.app_config_class_name }}(AppConfig):
    # Standard Django app configuration. For more information on these settings,
    # see https://docs.djangoproject.com/en/2.2/ref/applications/#application-configuration
    name = '{{ cookiecutter.project_slug }}'
    label = name
    verbose_name = "{{ cookiecutter.project_name }}"

    # The following are Airavata Django Portal specific custom Django app settings

    # Set url_home to a namespaced URL that will be the homepage when the custom
    # app is selected from the main menu
    url_home = "{{ cookiecutter.project_slug }}:home"

    # Set fa_icon_class to a FontAwesome CSS class for an icon to associate with
    # the custom app. Find an icon class at https://fontawesome.com/icons?d=gallery&p=2&s=regular,solid&m=free
    fa_icon_class = "fa-circle"

    # Second level navigation. Defines sub-navigation that displays on the left
    # hand side navigation bar in the Django Portal. This is optional but
    # recommended if your custom Django app has multiple entry points. See the
    # description of *nav* in
    # https://apache-airavata-django-portal.readthedocs.io/en/latest/dev/new_django_app/#appconfig-settings
    # for more details for more details.

    def ready(self) -> None:
        # Uncomment to register your queue settings calculators.
        # from {{ cookiecutter.project_slug }} import queue_settings_calculators  # noqa
        pass

    def merge_settings(self, settings_module) -> None:
        # Register this app's Vite bundle manifest so the portal's vite_js /
        # vite_css template tags can resolve "{{ cookiecutter.project_slug | upper }}".
        # Only needed if this app serves its own Vite frontend (i.e. it has
        # page views that load static/{{ cookiecutter.project_slug }}/dist).
        settings_module.VITE_MANIFESTS["{{ cookiecutter.project_slug | upper }}"] = {
            "manifest": os.path.join(
                os.path.dirname(__file__),
                "static", "{{ cookiecutter.project_slug }}", "dist", ".vite", "manifest.json",
            ),
            "base": "/static/{{ cookiecutter.project_slug }}/dist/",
        }
