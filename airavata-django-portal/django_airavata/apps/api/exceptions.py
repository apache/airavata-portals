from http import HTTPStatus

from django.http import JsonResponse


# For ad-hoc JSON error responses from function views that don't go through the
# web.py dispatch exception mapping (e.g. the tus upload-finish handler). The
# grpc->HTTP mapping that ``custom_exception_handler`` used to provide now lives
# in ``web.exception_to_response`` (``web.GRPC_STATUS_TO_HTTP``).
def generic_json_exception_response(
    exc: Exception, status: int = HTTPStatus.INTERNAL_SERVER_ERROR
) -> JsonResponse:
    return JsonResponse({"detail": str(exc)}, status=status)
