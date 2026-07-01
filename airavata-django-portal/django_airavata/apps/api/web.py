"""Dependency-free replacement for the slice of Django REST Framework the portal
uses.

This module reimplements — over plain Django + stdlib + grpc, with **no**
``rest_framework`` import — the bounded DRF surface the API app relies on:
``Response``/``status``, permissions (``BasePermission``, ``IsAuthenticated``),
``ParseError``, ``APIView``, ``GenericViewSet`` + the five model mixins, the
``@action``/``@api_view`` decorators, ``LimitOffsetPagination``, the ``route()``
router (a ``DefaultRouter`` equivalent minus the ``.json`` format-suffix
variants, the api-root and the browsable API), plus ``reverse`` and the
``remove_query_param``/``replace_query_param`` helpers.

The classes mirror the exact DRF attributes/methods that ``view_utils.py`` and
``views.py`` call (``get_object``/``check_object_permissions``/``lookup_field``/
``lookup_url_kwarg``/``lookup_value_regex``/``kwargs``/``request``/
``paginate_queryset``/``get_paginated_response``/``pagination_class``/
``pagination_viewname``/``mixins.*``).
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Protocol, cast, override
from urllib import parse

import grpc
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.urls import re_path, reverse  # noqa: F401  (reverse re-exported)
from django.views import View

from .proto_render import to_jsonable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from django.urls import URLPattern

    from django_airavata.request import AiravataRequest

    class _ActionMethod(Protocol):
        """A viewset method after ``@action``/``@permission_classes`` has attached
        its routing metadata (mirrors ``rest_framework``'s decorated actions)."""

        __name__: str
        mapping: dict[str, str]
        detail: bool
        url_path: str
        url_name: str
        permission_classes: list[type[BasePermission]]

        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class _Status:
    """Namespace of the HTTP status constants callers reference as
    ``status.HTTP_*`` (mirrors ``rest_framework.status``)."""

    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_501_NOT_IMPLEMENTED = 501


status = _Status()


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class Response(HttpResponse):
    """An ``HttpResponse`` initialized with *unrendered* data (like DRF).

    Carries ``.data`` / ``.status_code`` and is itself a valid Django
    ``HttpResponse``. The JSON body is produced LAZILY on first access to
    ``.content`` (or ``.rendered_content``): ``json.dumps(to_jsonable(self.data),
    cls=DjangoJSONEncoder)`` with ``Content-Type: application/json``. This lets
    page views call ``SomeViewSet.as_view(...)(request)`` and then read
    ``response.data`` / ``response.status_code`` (and hand ``.data`` to
    ``ProtoJSONRenderer``) BEFORE the body is rendered, while real HTTP requests
    get the rendered ``.content`` after middleware.

    Matching DRF: status 204 or ``data is None`` → an EMPTY body (``b''``), no
    JSON ``null``.
    """

    def __init__(
        self,
        data: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> None:
        # Initialize the HttpResponse with an empty body; do NOT serialize yet.
        super().__init__(content=b"", status=status, content_type=content_type)
        self.data = data
        self._is_rendered = False
        if headers:
            for name, value in headers.items():
                self[name] = value

    @property
    def rendered_content(self) -> bytes:
        """The JSON-encoded body bytes for ``self.data`` (empty for 204/None)."""
        if self.status_code == status.HTTP_204_NO_CONTENT or self.data is None:
            return b""
        self["Content-Type"] = "application/json"
        return json.dumps(to_jsonable(self.data), cls=DjangoJSONEncoder).encode("utf-8")

    def render(self) -> Response:
        """Materialize ``rendered_content`` into ``self.content`` (idempotent).

        Django's response handling calls ``render()`` on template-style responses
        after middleware; ``HttpResponseBase.getvalue`` / ``__iter__`` also work
        once ``.content`` is set. Reading ``.content`` triggers this lazily.
        """
        if not self._is_rendered:
            # Assign through HttpResponse.content setter (encodes / sets body).
            HttpResponse.content.fset(self, self.rendered_content)
            self._is_rendered = True
        return self

    @property
    @override
    def content(self) -> bytes:
        # Lazily render on first read so page views can access ``.data`` first.
        if not self._is_rendered:
            self.render()
        return HttpResponse.content.fget(self)

    @content.setter
    @override
    def content(self, value: Any) -> None:
        HttpResponse.content.fset(self, value)
        self._is_rendered = True


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised for malformed request input; maps to HTTP 400."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Malformed request."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class BasePermission:
    """Base permission. Defaults allow; subclasses override the hooks."""

    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, view: APIView, obj: Any
    ) -> bool:
        return True


class IsAuthenticated(BasePermission):
    @override
    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)


# ---------------------------------------------------------------------------
# Exception → HTTP mapping (ports exceptions.custom_exception_handler /
# GRPC_STATUS_TO_HTTP without importing DRF).
# ---------------------------------------------------------------------------

GRPC_STATUS_TO_HTTP = {
    grpc.StatusCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    grpc.StatusCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
    grpc.StatusCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    grpc.StatusCode.INVALID_ARGUMENT: status.HTTP_400_BAD_REQUEST,
    grpc.StatusCode.FAILED_PRECONDITION: status.HTTP_400_BAD_REQUEST,
    grpc.StatusCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    grpc.StatusCode.UNIMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
}


class NotAuthenticated(Exception):
    """Permission failure for an unauthenticated request (maps to 401)."""

    pass


class PermissionDenied(Exception):
    """Permission failure for an authenticated request (maps to 403)."""

    pass


def exception_to_response(
    exc: Exception, request: HttpRequest | None = None
) -> Response:
    """Map an exception to a :class:`Response`, replicating
    ``exceptions.custom_exception_handler`` + ``GRPC_STATUS_TO_HTTP``."""
    if isinstance(exc, grpc.RpcError):
        # grpc declares code()/details() on grpc.Call, not the base RpcError; the
        # RpcError raised by a unary call is always a Call at runtime.
        call = cast("grpc.Call", exc)
        code = call.code()
        detail = call.details() or str(exc)
        if code == grpc.StatusCode.UNAVAILABLE:
            log.warning("gRPC UNAVAILABLE", exc_info=exc)
            return Response(
                {"detail": detail, "apiServerDown": True},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        http_status = GRPC_STATUS_TO_HTTP.get(
            code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if http_status >= 500:
            log.error("gRPC error %s", code, exc_info=exc)
        else:
            log.warning("gRPC error %s", code, exc_info=exc)
        return Response({"detail": detail}, status=http_status)

    if isinstance(exc, (ObjectDoesNotExist,)):
        log.warning("ObjectDoesNotExist", exc_info=exc)
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, Http404):
        return Response(
            {"detail": str(exc) or "Not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "detail": str(exc) or "Authentication credentials were not provided.",
                "is_authenticated": False,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "detail": str(exc)
                or "You do not have permission to perform this action."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ParseError):
        return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

    # Generic handler
    log.error("API exception", exc_info=exc)
    return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Query-param helpers (ports of DRF's ~10-line impls).
# ---------------------------------------------------------------------------


def replace_query_param(url: str, key: str, val: object) -> str:
    """Return ``url`` with the query parameter ``key`` set to ``val``."""
    (scheme, netloc, path, query, fragment) = parse.urlsplit(str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict[str(key)] = [str(val)]
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


def remove_query_param(url: str, key: str) -> str:
    """Return ``url`` with the query parameter ``key`` removed."""
    (scheme, netloc, path, query, fragment) = parse.urlsplit(str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict.pop(str(key), None)
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


# ---------------------------------------------------------------------------
# Rendering helpers shared by APIView / ViewSet dispatch.
# ---------------------------------------------------------------------------


def _render_response(result: Any) -> HttpResponseBase:
    """Normalize a handler return value into an ``HttpResponse`` to return.

    A :class:`Response` (now itself an ``HttpResponse`` with a lazily-rendered
    JSON body) is returned UNCHANGED so callers can still read ``.data`` /
    ``.status_code`` before the body renders. Any other bare ``HttpResponse``
    (``FileResponse`` / ``JsonResponse`` / ``StreamingHttpResponse`` /
    ``HttpResponse(status=204)``) passes through untouched. A handler that
    returned raw data is defensively wrapped in a :class:`Response`.
    """
    # HttpResponseBase (not HttpResponse) — FileResponse / StreamingHttpResponse extend
    # HttpResponseBase directly, so checking HttpResponse alone would wrap (and JSON-encode)
    # streamed file downloads, breaking them.
    if isinstance(result, HttpResponseBase):
        return result
    return Response(result)


def _instantiate_permissions(
    permission_classes: Iterable[type[BasePermission]],
) -> list[BasePermission]:
    return [p() for p in permission_classes]


# ---------------------------------------------------------------------------
# APIView
# ---------------------------------------------------------------------------


class APIView(View):
    """Plain-Django reimplementation of ``rest_framework.views.APIView``.

    ``dispatch`` runs permission checks (request-level for every
    ``permission_classes`` entry), routes to the ``get``/``post``/``put``/
    ``patch``/``delete`` handler, renders a returned :class:`Response`, and maps
    exceptions to HTTP via :func:`exception_to_response`. Provides
    ``self.request``/``self.args``/``self.kwargs``.
    """

    permission_classes: list[type[BasePermission]] = [IsAuthenticated]

    # Subclasses (and the ViewSet routing layer) may override.
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    def get_permissions(self) -> list[BasePermission]:
        return _instantiate_permissions(self.permission_classes)

    def permission_denied(
        self, request: HttpRequest, message: str | None = None
    ) -> None:
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            raise NotAuthenticated(message)
        raise PermissionDenied(message)

    def check_permissions(self, request: HttpRequest) -> None:
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request, message=getattr(permission, "message", None)
                )

    def check_object_permissions(self, request: HttpRequest, obj: Any) -> None:
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, "message", None)
                )

    def initial(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.check_permissions(request)

    @override
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.request = request
        self.args = args
        self.kwargs = kwargs
        try:
            self.initial(request, *args, **kwargs)
            handler = getattr(
                self, (request.method or "").lower(), self.http_method_not_allowed
            )
            result = handler(request, *args, **kwargs)
            return _render_response(result)
        except Exception as exc:
            return _render_response(exception_to_response(exc, request))

    @override
    def http_method_not_allowed(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Response:
        return Response(
            {"detail": f'Method "{request.method}" not allowed.'}, status=405
        )


# ---------------------------------------------------------------------------
# Serializer-less GenericViewSet / ViewSet + model mixins
# ---------------------------------------------------------------------------


class ViewSetMixin:
    """Reproduces DRF ``ViewSetMixin.as_view(actions)`` semantics: map each HTTP
    method to a named action, set ``self.action``/``self.action_map``, then
    dispatch (with permission checks + Response rendering inherited from
    ``APIView``)."""

    @classmethod
    def as_view(
        cls, actions: dict[str, str] | None = None, **initkwargs: Any
    ) -> Callable[..., HttpResponseBase]:
        if not actions:
            raise TypeError(
                "The `actions` argument must be provided when calling "
                "`.as_view()` on a ViewSet."
            )

        def view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
            self = cls(**initkwargs)
            if "get" in actions and "head" not in actions:
                actions["head"] = actions["get"]
            self.action_map = actions  # ty: ignore[unresolved-attribute]  # DRF shim: action_map set dynamically on the viewset instance
            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            return self.dispatch(request, *args, **kwargs)

        return view

    def initialize_request(self, request: HttpRequest) -> None:
        method = (request.method or "").lower()
        if method == "options":
            self.action = "metadata"
        else:
            self.action = self.action_map.get(method)  # ty: ignore[unresolved-attribute]  # DRF shim: action_map set on the instance by as_view()

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.initialize_request(request)
        try:
            self.initial(request, *args, **kwargs)  # ty: ignore[unresolved-attribute]  # mixin: always composed with APIView (ViewSet/GenericViewSet)
            handler = getattr(
                self,
                (request.method or "").lower(),
                self.http_method_not_allowed,  # ty: ignore[unresolved-attribute]  # mixin: always composed with APIView (ViewSet/GenericViewSet)
            )
            result = handler(request, *args, **kwargs)
            return _render_response(result)
        except Exception as exc:
            return _render_response(exception_to_response(exc, request))


class GenericViewSet(ViewSetMixin, APIView):
    """Generic viewset: object/queryset/serializer/pagination plumbing.

    Mirrors the DRF attributes/methods ``view_utils`` and ``views`` call.
    """

    # Match GenericAPIBackedViewSet's relaxed regex (Airavata ids contain '.').
    lookup_field = "pk"
    lookup_url_kwarg: str | None = None
    lookup_value_regex = "[^/]+"

    pagination_class: type[LimitOffsetPagination] | None = None
    _paginator: LimitOffsetPagination | None = None

    # -- pagination -------------------------------------------------------
    @property
    def paginator(self) -> LimitOffsetPagination | None:
        if self._paginator is None:
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset: Any) -> list[Any] | None:
        paginator = self.paginator
        if paginator is None:
            return None
        request = cast("AiravataRequest", self.request)
        return paginator.paginate_queryset(queryset, request, view=self)

    def get_paginated_response(self, data: Any) -> Response:
        paginator = self.paginator
        assert paginator is not None
        return paginator.get_paginated_response(data)


# -- model action mixins --------------------------------------------------


# Marker mixins declaring which default actions a viewset exposes so route()
# routes them. The portal's viewsets always implement each action directly
# (rendering protos / WithAccess envelopes via web.Response + ProtoJSONRenderer),
# never through a DRF serializer, so the bodies here are abstract. The one
# concrete default is DestroyModelMixin (below), which delegates to
# perform_destroy().
class ListModelMixin:
    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError(f"{type(self).__name__} must implement list()")


class RetrieveModelMixin:
    def retrieve(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError(f"{type(self).__name__} must implement retrieve()")


class CreateModelMixin:
    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError(f"{type(self).__name__} must implement create()")


class UpdateModelMixin:
    def update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        raise NotImplementedError(f"{type(self).__name__} must implement update()")

    def partial_update(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Response:
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin:
    def destroy(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance: Any) -> None:
        instance.delete()


# Namespace object so callers can write ``from . import web`` then ``web.mixins``
# (mirroring ``from rest_framework import mixins``).
class _Mixins:
    ListModelMixin = ListModelMixin
    RetrieveModelMixin = RetrieveModelMixin
    CreateModelMixin = CreateModelMixin
    UpdateModelMixin = UpdateModelMixin
    DestroyModelMixin = DestroyModelMixin


mixins = _Mixins()


# ---------------------------------------------------------------------------
# @action / @api_view decorators
# ---------------------------------------------------------------------------


def action(
    detail: bool = False,
    methods: list[str] | None = None,
    url_path: str | None = None,
    url_name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a viewset method as a routable extra action.

    Records ``mapping`` (http-method → method-name), ``detail``, ``url_path``
    (default = func name) and ``url_name`` (default = func name with
    ``_``→``-``), so :func:`route` can route to it (mirrors ``rest_framework``'s
    ``@action``).
    """
    methods = ["get"] if methods is None else methods
    methods = [m.lower() for m in methods]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        fn = cast("_ActionMethod", func)
        fn.mapping = dict.fromkeys(methods, fn.__name__)
        fn.detail = detail
        fn.url_path = url_path if url_path else fn.__name__
        fn.url_name = url_name if url_name else fn.__name__.replace("_", "-")
        return func

    return decorator


def api_view(
    http_method_names: list[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., HttpResponseBase]]:
    """Wrap a plain function as an ``APIView``-equivalent.

    Defaults to GET. Provides the same dispatch (Response rendering, exception
    mapping, ``IsAuthenticated`` by default; ``request.data``/``query_params``
    come from the request-augmentation middleware).
    """
    http_method_names = ["GET"] if http_method_names is None else http_method_names
    allowed = [m.lower() for m in http_method_names]

    def decorator(func: Callable[..., Any]) -> Callable[..., HttpResponseBase]:
        fn = cast("_ActionMethod", func)

        class WrappedAPIView(APIView):
            pass

        def handler(
            self: APIView, request: HttpRequest, *args: Any, **kwargs: Any
        ) -> Any:
            return func(request, *args, **kwargs)

        for method in allowed:
            setattr(WrappedAPIView, method, handler)

        # @permission_classes([...]) (below) may override this.
        WrappedAPIView.permission_classes = getattr(
            func, "permission_classes", APIView.permission_classes
        )
        WrappedAPIView.__name__ = fn.__name__
        WrappedAPIView.__doc__ = func.__doc__
        return WrappedAPIView.as_view()

    return decorator


def permission_classes(
    permission_classes: list[type[BasePermission]],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """``@permission_classes([...])`` for ``@api_view`` functions. Apply it
    *above* ``@api_view`` (DRF order); it stashes the classes the wrapper reads.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cast("_ActionMethod", func).permission_classes = permission_classes
        return func

    return decorator


# ---------------------------------------------------------------------------
# LimitOffsetPagination (ports view_utils.APIResultPagination's base).
# ---------------------------------------------------------------------------


class LimitOffsetPagination:
    """Limit/offset pagination over the request query params.

    ``view_utils.APIResultPagination`` subclasses this and overrides
    ``paginate_queryset``/``get_paginated_response``/the link builders, so this
    base provides the limit/offset extraction and the default
    ``{next, previous, results, limit, offset}`` shape + reverse-based link
    building used there.
    """

    default_limit = 10
    limit_query_param = "limit"
    offset_query_param = "offset"
    max_limit: int | None = None
    limit: int
    offset: int

    def get_limit(self, request: AiravataRequest) -> int | None:
        if self.limit_query_param:
            try:
                raw = request.query_params[self.limit_query_param]
                limit = int(raw)
                if self.max_limit is not None:
                    limit = min(limit, self.max_limit)
                return limit
            except (KeyError, ValueError):
                pass
        return self.default_limit

    def get_offset(self, request: AiravataRequest) -> int:
        try:
            return max(0, int(request.query_params[self.offset_query_param]))
        except (KeyError, ValueError):
            return 0

    def paginate_queryset(
        self, queryset: Any, request: AiravataRequest, view: Any = None
    ) -> list[Any] | None:
        limit = self.get_limit(request)
        if limit is None:
            return None
        self.limit = limit
        self.offset = self.get_offset(request)
        self.request = request
        return list(queryset[self.offset : self.offset + self.limit])

    def get_paginated_response(self, data: Any) -> Response:
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("limit", self.limit),
                    ("offset", self.offset),
                ]
            )
        )

    def get_next_link(self) -> str:
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self) -> str | None:
        if self.offset <= 0:
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)
        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)


# Namespace object so callers can write ``web.permissions.BasePermission`` etc.
# (mirroring ``from rest_framework import permissions``).
class _Permissions:
    BasePermission = BasePermission


permissions = _Permissions()


# ---------------------------------------------------------------------------
# route() — DefaultRouter equivalent (no .json suffix, no api-root, no
# browsable API).
# ---------------------------------------------------------------------------

# The fixed list/detail routes, mirroring DRF SimpleRouter.routes (minus the
# DynamicRoute placeholders, which are expanded per @action below).
_LIST_ROUTE = {
    "url": r"^{prefix}/$",
    "mapping": {"get": "list", "post": "create"},
    "name": "{basename}-list",
    "detail": False,
}
_DETAIL_ROUTE = {
    "url": r"^{prefix}/{lookup}/$",
    "mapping": {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    },
    "name": "{basename}-detail",
    "detail": True,
}


def _get_lookup_regex(viewset: type[ViewSetMixin]) -> str:
    lookup_field = getattr(viewset, "lookup_field", "pk")
    lookup_url_kwarg = getattr(viewset, "lookup_url_kwarg", None) or lookup_field
    # DRF's SimpleRouter default value pattern is '[^/.]+'; our GenericViewSet
    # base overrides it to '[^/]+'. Use the viewset's value, falling back to the
    # DRF default for viewsets that don't declare one.
    lookup_value = getattr(viewset, "lookup_value_regex", "[^/.]+")
    return f"(?P<{lookup_url_kwarg}>{lookup_value})"


def _method_map(viewset: type[ViewSetMixin], mapping: dict[str, str]) -> dict[str, str]:
    """Keep only the http-method→action pairs the viewset actually implements."""
    bound = {}
    for method, action_name in mapping.items():
        if hasattr(viewset, action_name):
            bound[method] = action_name
    return bound


def _extra_actions(viewset: type[ViewSetMixin]) -> list[Any]:
    return [m for _, m in getmembers(viewset, lambda attr: hasattr(attr, "mapping"))]


def route(prefix: str, viewset: type[ViewSetMixin], basename: str) -> list[URLPattern]:
    """Reproduce DRF ``DefaultRouter`` output for ``viewset`` (no ``.json``
    format-suffix variants, no api-root, no browsable API).

    Returns a list of ``django.urls.re_path`` entries: a list route, a detail
    route, and one route per ``@action`` (list-route or detail-route depending
    on ``detail``), each named ``{basename}-{url_name}`` (list/detail use
    ``{basename}-list``/``{basename}-detail``).
    """
    lookup = _get_lookup_regex(viewset)

    extra = _extra_actions(viewset)
    detail_actions = [a for a in extra if a.detail]
    list_actions = [a for a in extra if not a.detail]

    # Build the ordered route specs: list route, list-actions, detail route,
    # detail-actions (mirrors SimpleRouter.routes ordering).
    specs: list[dict[str, Any]] = []
    specs.append(dict(_LIST_ROUTE))
    for a in list_actions:
        specs.append(
            {
                "url": r"^{prefix}/" + _escape(a.url_path) + r"/$",
                "mapping": dict(a.mapping),
                "name": "{basename}-" + a.url_name,
                "detail": False,
            }
        )
    specs.append(dict(_DETAIL_ROUTE))
    for a in detail_actions:
        specs.append(
            {
                "url": r"^{prefix}/{lookup}/" + _escape(a.url_path) + r"/$",
                "mapping": dict(a.mapping),
                "name": "{basename}-" + a.url_name,
                "detail": True,
            }
        )

    urls: list[URLPattern] = []
    for spec in specs:
        mapping = _method_map(viewset, spec["mapping"])
        if not mapping:
            continue
        regex = spec["url"].format(
            prefix=prefix, lookup=lookup
        )  # heterogeneous spec dict: "url" is always a str
        view = viewset.as_view(mapping, basename=basename, detail=spec["detail"])
        name = spec["name"].format(
            basename=basename
        )  # heterogeneous spec dict: "name" is always a str
        urls.append(re_path(regex, view, name=name))
    return urls


def _escape(url_path: str) -> str:
    return url_path.replace("{", "{{").replace("}", "}}")
