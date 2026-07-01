from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import render

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:

    return render(
        request,
        "django_airavata_dataparsers/parsers-manage.html",
        {"bundle_name": "parser-list"},
    )


def parser_details(request: HttpRequest, parser_id: str) -> HttpResponse:
    return render(
        request,
        "django_airavata_dataparsers/parser-details.html",
        {"parser_id": parser_id, "bundle_name": "parser-details"},
    )


def edit_parser(request: HttpRequest, parser_id: str) -> HttpResponse:
    return render(
        request,
        "django_airavata_dataparsers/edit-parser.html",
        {"parser_id": parser_id, "bundle_name": "parser-edit"},
    )


def create_parser(request: HttpRequest) -> HttpResponse:
    # Same editor bundle as edit, but with no parser_id — the Vue ParserEditContainer
    # treats an empty data-parser-id as "new parser" (it only fetches when an id is set).
    return render(
        request,
        "django_airavata_dataparsers/edit-parser.html",
        {"parser_id": "", "bundle_name": "parser-edit"},
    )
