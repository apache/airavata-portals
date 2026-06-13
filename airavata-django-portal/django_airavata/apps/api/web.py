"""Dependency-free replacement for the slice of Django REST Framework the portal
uses.

This module reimplements — over plain Django + stdlib + grpc, with **no**
``rest_framework`` import — the bounded DRF surface the API/auth apps rely on:
``Response``/``status``, permissions (``BasePermission`` with ``|``/``&``/``~``
composition, ``IsAuthenticated``, ``AllowAny``), ``ParseError``/
``ValidationError``, ``APIView``, ``GenericViewSet``/``ViewSet`` + the five model
mixins, the ``@action``/``@api_view`` decorators, ``LimitOffsetPagination``, the
``route()`` router (a byte-for-byte ``DefaultRouter`` equivalent minus the
``.json`` format-suffix variants, the api-root and the browsable API), plus
``reverse`` and the ``remove_query_param``/``replace_query_param`` helpers.

The classes mirror the exact DRF attributes/methods that ``view_utils.py`` and
``views.py`` call (``get_object``/``get_queryset``/``get_serializer``/
``check_object_permissions``/``lookup_field``/``lookup_url_kwarg``/
``lookup_value_regex``/``kwargs``/``request``/``paginate_queryset``/
``get_paginated_response``/``pagination_class``/``pagination_viewname``/
``mixins.*``) so they are drop-in compatible when those modules later rebase onto
this module.
"""

import json
import logging
from collections import OrderedDict
from inspect import getmembers
from urllib import parse

import grpc
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse, HttpResponseBase
from django.urls import re_path, reverse  # noqa: F401  (reverse re-exported)
from django.views import View

from .proto_render import to_jsonable

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

    def __init__(self, data=None, status=200, headers=None, content_type=None):
        # Initialize the HttpResponse with an empty body; do NOT serialize yet.
        super().__init__(content=b"", status=status, content_type=content_type)
        self.data = data
        self._is_rendered = False
        if headers:
            for name, value in headers.items():
                self[name] = value

    @property
    def rendered_content(self):
        """The JSON-encoded body bytes for ``self.data`` (empty for 204/None)."""
        if self.status_code == status.HTTP_204_NO_CONTENT or self.data is None:
            return b""
        self["Content-Type"] = "application/json"
        return json.dumps(to_jsonable(self.data), cls=DjangoJSONEncoder).encode("utf-8")

    def render(self):
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
    def content(self):
        # Lazily render on first read so page views can access ``.data`` first.
        if not self._is_rendered:
            self.render()
        return HttpResponse.content.fget(self)

    @content.setter
    def content(self, value):
        HttpResponse.content.fset(self, value)
        self._is_rendered = True


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised for malformed request input; maps to HTTP 400."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Malformed request."

    def __init__(self, detail=None):
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(self.detail)


class ValidationError(Exception):
    """Validation failure carrying ``.detail`` (dict/list/str), like DRF.

    DRF normalizes any of those into ``.detail``; callers (serializers/views)
    pass a dict of field errors, a list, or a plain string and later read
    ``e.detail``.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid input."

    def __init__(self, detail=None):
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class OperationHolderMixin:
    """Adds DRF-style ``|``/``&``/``~`` composition to permission classes.

    These operate on the permission *class* (DRF composes
    ``IsInAdminsGroupPermission | ReadOnly`` at class-definition / attribute
    level), so the operators return a composed class that the view instantiates.
    """

    def __and__(self, other):
        return AND(self, other)

    def __or__(self, other):
        return OR(self, other)

    def __invert__(self):
        return NOT(self)


class _OperandHolder(OperationHolderMixin):
    """Wraps a (composed) permission class so the operators chain."""

    def __init__(self, operator_class, op1_class, op2_class=None):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class()
        op2 = self.op2_class() if self.op2_class is not None else None
        return self.operator_class(op1, op2)


class BasePermissionMetaclass(OperationHolderMixin, type):
    """Metaclass so the operators work on permission *classes* directly."""

    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """Base permission. Defaults allow; subclasses override the hooks."""

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True

    def __and__(self, other):
        return AND(self, other)

    def __or__(self, other):
        return OR(self, other)

    def __invert__(self):
        return NOT(self)


class AND:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request, view):
        return self.op1.has_permission(request, view) and self.op2.has_permission(
            request, view
        )

    def has_object_permission(self, request, view, obj):
        return self.op1.has_object_permission(
            request, view, obj
        ) and self.op2.has_object_permission(request, view, obj)


class OR:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request, view):
        return self.op1.has_permission(request, view) or self.op2.has_permission(
            request, view
        )

    def has_object_permission(self, request, view, obj):
        # Mirror DRF: an OR short-circuits at the request level — if op1 already
        # granted request-level access, object-level access is also granted.
        return (
            self.op1.has_permission(request, view)
            and self.op1.has_object_permission(request, view, obj)
        ) or (
            self.op2.has_permission(request, view)
            and self.op2.has_object_permission(request, view, obj)
        )


class NOT:
    def __init__(self, op1, op2=None):
        self.op1 = op1

    def has_permission(self, request, view):
        return not self.op1.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return not self.op1.has_object_permission(request, view, obj)


# Make the operators on BasePermission subclasses return _OperandHolder so that
# ``ClassA | ClassB`` (classes, not instances) composes into a callable class.
OperationHolderMixin.__or__ = lambda self, other: _OperandHolder(OR, self, other)  # ty: ignore[invalid-assignment]  # intentional monkeypatch so class-level operators return _OperandHolder
OperationHolderMixin.__and__ = lambda self, other: _OperandHolder(AND, self, other)  # ty: ignore[invalid-assignment]  # intentional monkeypatch so class-level operators return _OperandHolder
OperationHolderMixin.__invert__ = lambda self: _OperandHolder(NOT, self)  # ty: ignore[invalid-assignment]  # intentional monkeypatch so class-level operators return _OperandHolder


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)


class AllowAny(BasePermission):
    def has_permission(self, request, view):
        return True


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


def exception_to_response(exc, request=None):
    """Map an exception to a :class:`Response`, replicating
    ``exceptions.custom_exception_handler`` + ``GRPC_STATUS_TO_HTTP``."""
    if isinstance(exc, grpc.RpcError):
        code = exc.code()
        detail = exc.details() or str(exc)
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

    if isinstance(exc, (ParseError, ValidationError)):
        return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

    # Generic handler
    log.error("API exception", exc_info=exc)
    return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Query-param helpers (ports of DRF's ~10-line impls).
# ---------------------------------------------------------------------------


def replace_query_param(url, key, val):
    """Return ``url`` with the query parameter ``key`` set to ``val``."""
    (scheme, netloc, path, query, fragment) = parse.urlsplit(str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict[str(key)] = [str(val)]
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


def remove_query_param(url, key):
    """Return ``url`` with the query parameter ``key`` removed."""
    (scheme, netloc, path, query, fragment) = parse.urlsplit(str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict.pop(str(key), None)
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


# ---------------------------------------------------------------------------
# Rendering helpers shared by APIView / ViewSet dispatch.
# ---------------------------------------------------------------------------


def _render_response(result):
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


def _instantiate_permissions(permission_classes):
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

    permission_classes = [IsAuthenticated]

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

    def get_permissions(self):
        return _instantiate_permissions(self.permission_classes)

    def permission_denied(self, request, message=None):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            raise NotAuthenticated(message)
        raise PermissionDenied(message)

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request, message=getattr(permission, "message", None)
                )

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, "message", None)
                )

    def initial(self, request, *args, **kwargs):
        self.check_permissions(request)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        try:
            self.initial(request, *args, **kwargs)
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed
            )
            result = handler(request, *args, **kwargs)
            return _render_response(result)
        except Exception as exc:
            return _render_response(exception_to_response(exc, request))

    def http_method_not_allowed(self, request, *args, **kwargs):
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
    def as_view(cls, actions=None, **initkwargs):
        if not actions:
            raise TypeError(
                "The `actions` argument must be provided when calling "
                "`.as_view()` on a ViewSet."
            )

        def view(request, *args, **kwargs):
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

        view.cls = cls  # ty: ignore[unresolved-attribute]  # DRF shim: dynamic function attribute (mirrors DRF as_view)
        view.initkwargs = initkwargs  # ty: ignore[unresolved-attribute]  # DRF shim: dynamic function attribute (mirrors DRF as_view)
        view.actions = actions  # ty: ignore[unresolved-attribute]  # DRF shim: dynamic function attribute (mirrors DRF as_view)
        return view

    def initialize_request(self, request):
        method = request.method.lower()
        if method == "options":
            self.action = "metadata"
        else:
            self.action = self.action_map.get(method)  # ty: ignore[unresolved-attribute]  # DRF shim: action_map set on the instance by as_view()

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.initialize_request(request)
        try:
            self.initial(request, *args, **kwargs)  # ty: ignore[unresolved-attribute]  # mixin: always composed with APIView (ViewSet/GenericViewSet)
            handler = getattr(
                self,
                request.method.lower(),
                self.http_method_not_allowed,  # ty: ignore[unresolved-attribute]  # mixin: always composed with APIView (ViewSet/GenericViewSet)
            )
            result = handler(request, *args, **kwargs)
            return _render_response(result)
        except Exception as exc:
            return _render_response(exception_to_response(exc, request))

    @classmethod
    def get_extra_actions(cls):
        return [
            method
            for _, method in getmembers(cls, lambda attr: hasattr(attr, "mapping"))
        ]


class ViewSet(ViewSetMixin, APIView):
    """A viewset with no default actions (matches DRF ``ViewSet``)."""

    pass


class GenericViewSet(ViewSetMixin, APIView):
    """Generic viewset: object/queryset/serializer/pagination plumbing.

    Mirrors the DRF attributes/methods ``view_utils`` and ``views`` call.
    """

    # Match GenericAPIBackedViewSet's relaxed regex (Airavata ids contain '.').
    lookup_field = "pk"
    lookup_url_kwarg = None
    lookup_value_regex = "[^/]+"

    serializer_class = None
    queryset = None

    pagination_class = None
    _paginator = None

    # -- queryset / object ------------------------------------------------
    def get_queryset(self):
        return self.queryset

    def filter_queryset(self, queryset):
        return queryset

    def get_object(self):
        """Django-ORM-style object lookup for the ORM-backed (auth) viewsets.

        Filters ``get_queryset()`` by ``{lookup_field: kwargs[lookup_url_kwarg]}``
        and raises ``Http404`` on ``DoesNotExist`` (mirrors DRF's
        ``get_object_or_404``), then runs object-level permission checks.
        Overridable — the API ``GenericAPIBackedViewSet`` replaces it with an SDK
        proto-direct lookup.
        """
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        try:
            obj = queryset.get(**{self.lookup_field: lookup_value})
        except (
            ObjectDoesNotExist,
            ValueError,
            TypeError,
            DjangoValidationError,
        ) as err:
            raise Http404(
                f"No {getattr(queryset, 'model', type(self)).__name__} matches "
                "the given query."
            ) from err
        self.check_object_permissions(self.request, obj)
        return obj

    # -- serializer -------------------------------------------------------
    def get_serializer_class(self):
        assert self.serializer_class is not None, (
            f"'{self.__class__.__name__}' should either include a "
            "`serializer_class` attribute, or override the "
            "`get_serializer_class()` method."
        )
        return self.serializer_class

    def get_serializer_context(self):
        return {"request": self.request, "view": self}

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    # -- pagination -------------------------------------------------------
    @property
    def paginator(self):
        if self._paginator is None:
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)


# -- model mixins (DRF default list/retrieve/create/update/destroy) -------


# These mixins are always composed with GenericViewSet, which supplies
# filter_queryset/get_queryset/paginate_queryset/get_serializer/
# get_paginated_response/get_object. ty analyzes each mixin standalone, so those
# attribute accesses read as unresolved here even though they resolve at runtime.
class ListModelMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        page = self.paginate_queryset(queryset)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
            return self.get_paginated_response(serializer.data)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        serializer = self.get_serializer(queryset, many=True)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        return Response(serializer.data)


class RetrieveModelMixin:
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        serializer = self.get_serializer(instance)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        return Response(serializer.data)


class CreateModelMixin:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class UpdateModelMixin:
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        serializer = self.get_serializer(instance, data=request.data, partial=partial)  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin:
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()  # ty: ignore[unresolved-attribute]  # provided by GenericViewSet at composition
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


# -- composed viewsets (DRF ModelViewSet / ReadOnlyModelViewSet) ----------


class ModelViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    """All CRUD actions (matches DRF ``ModelViewSet``)."""

    pass


class ReadOnlyModelViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """``retrieve()`` + ``list()`` only (matches DRF ``ReadOnlyModelViewSet``)."""

    pass


# Namespace object so callers can write ``from . import web`` then ``web.mixins``
# (mirroring ``from rest_framework import mixins``).
class _Mixins:
    ListModelMixin = ListModelMixin
    RetrieveModelMixin = RetrieveModelMixin
    CreateModelMixin = CreateModelMixin
    UpdateModelMixin = UpdateModelMixin
    DestroyModelMixin = DestroyModelMixin


mixins = _Mixins()


# Namespace object so callers can write ``web.viewsets.ModelViewSet`` etc.
# (mirroring ``from rest_framework import viewsets``).
class _Viewsets:
    ViewSet = ViewSet
    GenericViewSet = GenericViewSet
    ModelViewSet = ModelViewSet
    ReadOnlyModelViewSet = ReadOnlyModelViewSet


viewsets = _Viewsets()


# ---------------------------------------------------------------------------
# @action / @api_view decorators
# ---------------------------------------------------------------------------


def action(detail=False, methods=None, url_path=None, url_name=None, **kwargs):
    """Mark a viewset method as a routable extra action.

    Records ``mapping`` (http-method → method-name), ``detail``, ``url_path``
    (default = func name), ``url_name`` (default = func name with ``_``→``-``)
    and preserves extra kwargs (``serializer_class``/``renderer_classes``) as
    attributes, so :func:`route` can route to it (mirrors ``rest_framework``'s
    ``@action``).
    """
    methods = ["get"] if methods is None else methods
    methods = [m.lower() for m in methods]

    def decorator(func):
        func.mapping = dict.fromkeys(methods, func.__name__)
        func.detail = detail
        func.url_path = url_path if url_path else func.__name__
        func.url_name = url_name if url_name else func.__name__.replace("_", "-")
        func.kwargs = kwargs
        return func

    return decorator


def api_view(http_method_names=None):
    """Wrap a plain function as an ``APIView``-equivalent.

    Defaults to GET. Provides the same dispatch (Response rendering, exception
    mapping, ``IsAuthenticated`` by default; ``request.data``/``query_params``
    come from the request-augmentation middleware).
    """
    http_method_names = ["GET"] if http_method_names is None else http_method_names
    allowed = [m.lower() for m in http_method_names]

    def decorator(func):
        class WrappedAPIView(APIView):
            pass

        def handler(self, request, *args, **kwargs):
            return func(request, *args, **kwargs)

        for method in allowed:
            setattr(WrappedAPIView, method, handler)

        # @permission_classes([...]) (below) may override this.
        WrappedAPIView.permission_classes = getattr(
            func, "permission_classes", APIView.permission_classes
        )
        WrappedAPIView.__name__ = func.__name__
        WrappedAPIView.__doc__ = func.__doc__
        WrappedAPIView.func = staticmethod(func)  # ty: ignore[unresolved-attribute]  # dynamic class attribute (mirrors DRF @api_view)
        return WrappedAPIView.as_view()

    return decorator


def permission_classes(permission_classes):
    """``@permission_classes([...])`` for ``@api_view`` functions. Apply it
    *above* ``@api_view`` (DRF order); it stashes the classes the wrapper reads.
    """

    def decorator(func):
        func.permission_classes = permission_classes
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
    max_limit = None

    def get_limit(self, request):
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

    def get_offset(self, request):
        try:
            return max(0, int(request.query_params[self.offset_query_param]))
        except (KeyError, ValueError):
            return 0

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None
        self.offset = self.get_offset(request)
        self.request = request
        return list(queryset[self.offset : self.offset + self.limit])

    def get_paginated_response(self, data):
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

    def get_next_link(self):
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self):
        if self.offset <= 0:
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)
        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)
        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)


# Namespace object so callers can write ``web.pagination.LimitOffsetPagination``
# (mirroring ``from rest_framework import pagination``).
class _Pagination:
    LimitOffsetPagination = LimitOffsetPagination


pagination = _Pagination()


# Namespace object so callers can write ``web.permissions.BasePermission`` etc.
# (mirroring ``from rest_framework import permissions``).
class _Permissions:
    BasePermission = BasePermission
    IsAuthenticated = IsAuthenticated
    AllowAny = AllowAny
    SAFE_METHODS = SAFE_METHODS


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


def _get_lookup_regex(viewset):
    lookup_field = getattr(viewset, "lookup_field", "pk")
    lookup_url_kwarg = getattr(viewset, "lookup_url_kwarg", None) or lookup_field
    # DRF's SimpleRouter default value pattern is '[^/.]+'; our GenericViewSet
    # base overrides it to '[^/]+'. Use the viewset's value, falling back to the
    # DRF default for viewsets that don't declare one.
    lookup_value = getattr(viewset, "lookup_value_regex", "[^/.]+")
    return f"(?P<{lookup_url_kwarg}>{lookup_value})"


def _method_map(viewset, mapping):
    """Keep only the http-method→action pairs the viewset actually implements."""
    bound = {}
    for method, action_name in mapping.items():
        if hasattr(viewset, action_name):
            bound[method] = action_name
    return bound


def _extra_actions(viewset):
    return [m for _, m in getmembers(viewset, lambda attr: hasattr(attr, "mapping"))]


def route(prefix, viewset, basename, lookup_field=None):
    """Reproduce DRF ``DefaultRouter`` output for ``viewset`` (no ``.json``
    format-suffix variants, no api-root, no browsable API).

    Returns a list of ``django.urls.re_path`` entries: a list route, a detail
    route, and one route per ``@action`` (list-route or detail-route depending
    on ``detail``), each named ``{basename}-{url_name}`` (list/detail use
    ``{basename}-list``/``{basename}-detail``).
    """
    # ``lookup_field`` override mirrors how a router could thread a custom field;
    # by default the viewset's own ``lookup_field`` is used.
    if lookup_field is not None:
        # Temporary shadow so the lookup regex uses the override without mutating
        # the viewset class.
        original = getattr(viewset, "lookup_field", "pk")
        viewset.lookup_field = lookup_field
        try:
            lookup = _get_lookup_regex(viewset)
        finally:
            viewset.lookup_field = original
    else:
        lookup = _get_lookup_regex(viewset)

    extra = _extra_actions(viewset)
    detail_actions = [a for a in extra if a.detail]
    list_actions = [a for a in extra if not a.detail]

    # Build the ordered route specs: list route, list-actions, detail route,
    # detail-actions (mirrors SimpleRouter.routes ordering).
    specs = []
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

    urls = []
    for spec in specs:
        mapping = _method_map(viewset, spec["mapping"])
        if not mapping:
            continue
        regex = spec["url"].format(prefix=prefix, lookup=lookup)  # ty: ignore[unresolved-attribute]  # heterogeneous spec dict: "url" is always a str
        view = viewset.as_view(mapping, basename=basename, detail=spec["detail"])
        name = spec["name"].format(basename=basename)  # ty: ignore[unresolved-attribute]  # heterogeneous spec dict: "name" is always a str
        urls.append(re_path(regex, view, name=name))
    return urls


def _escape(url_path):
    return url_path.replace("{", "{{").replace("}", "}}")
