import logging
import sys

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler
from grpc import RpcError, StatusCode

log = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, RpcError):
        code = exc.code() if hasattr(exc, 'code') else None
        if code == StatusCode.PERMISSION_DENIED:
            log.warning("gRPC PermissionDenied", exc_info=exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_403_FORBIDDEN)
        elif code == StatusCode.NOT_FOUND:
            log.warning("gRPC NotFound", exc_info=exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_404_NOT_FOUND)
        elif code == StatusCode.UNAVAILABLE:
            log.warning("gRPC Unavailable (API server down)", exc_info=exc)
            return Response(
                {'detail': str(exc), 'apiServerDown': True},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            log.error("gRPC error", exc_info=exc, extra={'request': context['request']})
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, ObjectDoesNotExist):
        log.warning("ObjectDoesNotExist", exc_info=exc)
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, NotAuthenticated):
        log.debug("NotAuthenticated", exc_info=exc)
        if response is not None:
            response.data['is_authenticated'] = False

    if isinstance(exc, UnicodeEncodeError):
        fse = sys.getfilesystemencoding()
        if fse != 'utf-8':
            log.error(f"filesystem encoding is {fse}, not 'utf-8'. File paths with Unicode characters will produce errors.")

    # Generic handler
    if response is None:
        log.error("API exception", exc_info=exc, extra={'request': context['request']})
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


# For non-Django REST Framework error responses
def generic_json_exception_response(
        exc, status=status.HTTP_500_INTERNAL_SERVER_ERROR):
    return JsonResponse({'detail': str(exc)}, status=status)
