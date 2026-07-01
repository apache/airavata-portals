from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

@login_required
def home(request):

    # Example code: Airavata API client
    # The gRPC Airavata client is available as 'request.airavata' with one facade
    # per service (research / compute / storage / credential / iam / sharing).
    # Make calls to the Airavata API from your view, for example:
    #
    # experiments = request.airavata.research.search_experiments(
    #        settings.GATEWAY_ID, request.user.username, filters={}, limit=20, offset=0)
    #
    # Authentication (the Keycloak token + gateway/user claims) is carried by the
    # client automatically; 'settings.GATEWAY_ID' is the gateway id.

    # Example code: user storage
    # The storage facade manages a user's files in the gateway:
    #
    # request.airavata.storage.list_dir("~/")                 # list the user's home directory
    # request.airavata.storage.download_file("~/path/file")   # read a file's bytes
    # request.airavata.storage.upload_file(path="~/path/file", content=..., name="file")

    return render(request, "{{ cookiecutter.project_slug }}/home.html", {
        "project_name": "{{ cookiecutter.project_name }}",
        # VITE_MANIFESTS key registered by this app's AppConfig.merge_settings.
        # home.html is copied verbatim (not rendered), so the manifest key is
        # passed in as a template context variable named 'vite_app'.
        "vite_app": "{{ cookiecutter.project_slug | upper }}",
    })
