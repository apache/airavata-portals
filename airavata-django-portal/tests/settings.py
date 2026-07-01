from django_airavata.settings import *  # noqa

# Above imports the common settings, can override them below as needed.
# The portal has no database; tests inherit the dummy backend from settings.py.

PORTAL_TITLE = "Django Airavata Gateway"  # ty: ignore[invalid-assignment]  # overriding a star-imported settings value; literal-narrowing false positive
