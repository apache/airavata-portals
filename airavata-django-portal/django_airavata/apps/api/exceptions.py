import logging
import sys

import grpc
from airavata.api.error.ttypes import (
    AuthorizationException,
    ExperimentNotFoundException
)
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler
from thrift.Thrift import TException
from thrift.transport import TTransport

log = logging.getLogger(__name__)

# Track D: map new-stack gRPC status codes to HTTP responses, mirroring the
# Thrift exception handling below so migrated views behave identically.
GRPC_STATUS_TO_HTTP = {
    grpc.StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    grpc.StatusCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
    grpc.StatusCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    grpc.StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
    grpc.StatusCode.FAILED_PRECONDITION: status.HTTP_400_BAD_REQUEST,
    grpc.StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    grpc.StatusCode.UNIMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
}


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, grpc.RpcError):
        code = exc.code()
        detail = exc.details() or str(exc)
        if code == grpc.StatusCode.UNAVAILABLE:
            log.warning("gRPC UNAVAILABLE", exc_info=exc)
            return Response(
                {'detail': detail, 'apiServerDown': True},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        http_status = GRPC_STATUS_TO_HTTP.get(
            code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        if http_status >= 500:
            log.error("gRPC error %s", code, exc_info=exc,
                      extra={'request': context['request']})
        else:
            log.warning("gRPC error %s", code, exc_info=exc)
        return Response({'detail': detail}, status=http_status)

    if isinstance(exc, AuthorizationException):
        log.warning("AuthorizationException", exc_info=exc)
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, ExperimentNotFoundException):
        log.warning("ExperimentNotFoundException", exc_info=exc)
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, TTransport.TTransportException):
        log.warning("TTransportException", exc_info=exc)
        return Response(
            {'detail': str(exc), 'apiServerDown': True},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Default TException handler, should come after more specific subclasses of
    # TException
    if isinstance(exc, TException):
        log.error("TException", exc_info=exc, extra={'request': context['request']})
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
