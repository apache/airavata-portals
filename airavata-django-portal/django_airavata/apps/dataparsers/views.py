from django.shortcuts import render


def home(request):

    return render(
        request,
        "django_airavata_dataparsers/parsers-manage.html",
        {"bundle_name": "parser-list"},
    )


def parser_details(request, parser_id):
    return render(
        request,
        "django_airavata_dataparsers/parser-details.html",
        {"parser_id": parser_id, "bundle_name": "parser-details"},
    )


def edit_parser(request, parser_id):
    return render(
        request,
        "django_airavata_dataparsers/edit-parser.html",
        {"parser_id": parser_id, "bundle_name": "parser-edit"},
    )


def create_parser(request):
    # Same editor bundle as edit, but with no parser_id — the Vue ParserEditContainer
    # treats an empty data-parser-id as "new parser" (it only fetches when an id is set).
    return render(
        request,
        "django_airavata_dataparsers/edit-parser.html",
        {"parser_id": "", "bundle_name": "parser-edit"},
    )
