from django.shortcuts import render

ENTRY_POINTS = {
    "parser-list": "static/django_airavata_dataparsers/js/parser-listing-entry-point.js",
    "parser-details": "static/django_airavata_dataparsers/js/entry-parser-details.js",
    "parser-edit": "static/django_airavata_dataparsers/js/parser-edit-entry-point.js",
}


def home(request):

    request.active_nav_item = "manage"
    return render(
        request,
        "django_airavata_dataparsers/parsers-manage.html",
        {
            "bundle_name": "parser-list",
            "entry_point": ENTRY_POINTS["parser-list"],
        },
    )


def parser_details(request, parser_id):
    return render(
        request,
        "django_airavata_dataparsers/parser-details.html",
        {
            "parser_id": parser_id,
            "bundle_name": "parser-details",
            "entry_point": ENTRY_POINTS["parser-details"],
        },
    )


def edit_parser(request, parser_id):
    return render(
        request,
        "django_airavata_dataparsers/edit-parser.html",
        {
            "parser_id": parser_id,
            "bundle_name": "parser-edit",
            "entry_point": ENTRY_POINTS["parser-edit"],
        },
    )
