from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "django_airavata/home.html", {})


def error500(request: HttpRequest) -> HttpResponse:
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


def error400(request: HttpRequest, exception: Exception) -> HttpResponse:
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


def error404(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(
        request,
        "django_airavata/error_page.html",
        status=404,
        context={"title": "Page Not Found", "text": """We couldn't find that page."""},
    )


def error403(request: HttpRequest, exception: Exception) -> HttpResponse:
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
