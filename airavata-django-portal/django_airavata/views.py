from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render


def health(request):
    return JsonResponse({"status": "ok"})


def landing(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "django_airavata/landing.html", {
        "portal_title": getattr(settings, "PORTAL_TITLE", "CyberShuttle Portal"),
    })


def home(request):
    # If the Wagtail CMS has been bootstrapped with the Airavata fixture (site_name
    # "Airavata Portal", created by set_wagtail_site after load_cms_data), serve the
    # CMS homepage from /pages/ instead of the plain Django Welcome card. Fall back
    # to the static template when no branded CMS site exists.
    try:
        from wagtail.models import Site

        if Site.objects.filter(site_name="Airavata Portal").exists():
            return redirect("/pages/")
    except Exception:
        pass
    return render(request, "django_airavata/home.html", {})


def error500(request):
    return render(
        request,
        "django_airavata/error_page.html",
        status=500,
        context={
            "title": "Error",
            "text": """An error occurred while processing your
                      request. The gateway administrator has been notified
                      of this error.""",
        },
    )


def error400(request, exception):
    return render(
        request,
        "django_airavata/error_page.html",
        status=400,
        context={
            "title": "Bad Request",
            "text": """An error occurred while processing your
                      request because the request was malformed.""",
        },
    )


def error404(request, exception):
    return render(
        request,
        "django_airavata/error_page.html",
        status=404,
        context={"title": "Page Not Found", "text": """We couldn't find that page."""},
    )


def error403(request, exception):
    return render(
        request,
        "django_airavata/error_page.html",
        status=403,
        context={
            "title": "Permission Denied",
            "text": """An error occurred because you don't have
                      permission to make this request. If you feel this was
                      an error, please contact the gateway administrator.""",
        },
    )
