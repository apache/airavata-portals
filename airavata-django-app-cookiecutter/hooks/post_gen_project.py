"""Prune the generated app to the selected feature set.

Runs in the generated project root (the dir that holds setup.cfg). cookiecutter
renders this file through Jinja first, so the cookiecutter values below are
concrete by the time Python runs.
"""

import os
import shutil
import sys

MODULE = "{{ cookiecutter.project_slug }}"
INCLUDE_APP_PAGES = "{{ cookiecutter.include_app_pages }}"
INCLUDE_OUTPUT_VIEW = "{{ cookiecutter.include_output_view }}"

# Minimal AppConfig used when the app has no page views / Vite frontend.
APPS_PY_OUTPUT_VIEW_ONLY = '''from django.apps import AppConfig


class {{ cookiecutter.app_config_class_name }}(AppConfig):
    name = '{{ cookiecutter.project_slug }}'
    label = name
    verbose_name = "{{ cookiecutter.project_name }}"
    fa_icon_class = "fa-circle"

    def ready(self) -> None:
        # Uncomment to register your queue settings calculators.
        # from {{ cookiecutter.project_slug }} import queue_settings_calculators  # noqa
        pass
'''


def remove(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def strip_output_view_providers(setup_cfg):
    """Drop the airavata.output_view_providers entry-point group in place."""
    with open(setup_cfg) as f:
        lines = f.readlines()
    out = []
    skipping = False
    for line in lines:
        if line.strip().startswith("airavata.output_view_providers"):
            skipping = True
            continue
        # Continuation entries are indented and non-blank.
        if skipping and line[:1].isspace() and line.strip():
            continue
        skipping = False
        out.append(line)
    with open(setup_cfg, "w") as f:
        f.writelines(out)


def main():
    if INCLUDE_APP_PAGES == "no" and INCLUDE_OUTPUT_VIEW == "no":
        sys.exit(
            "Nothing to generate: set include_app_pages and/or include_output_view to 'yes'."
        )

    if INCLUDE_OUTPUT_VIEW == "no":
        remove(os.path.join(MODULE, "output_views", MODULE + "_output_view.py"))
        strip_output_view_providers("setup.cfg")

    if INCLUDE_APP_PAGES == "no":
        remove(os.path.join(MODULE, "views.py"))
        remove(os.path.join(MODULE, "urls.py"))
        remove(os.path.join(MODULE, "templates"))
        remove(os.path.join(MODULE, "static"))
        with open(os.path.join(MODULE, "apps.py"), "w") as f:
            f.write(APPS_PY_OUTPUT_VIEW_ONLY)


main()
