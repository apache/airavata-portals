import logging
import os
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.http.request import QueryDict

from django_airavata.apps.api import web
from django_airavata.apps.api.web import (
    Response,
    remove_query_param,
    replace_query_param,
    reverse,
)

logger = logging.getLogger(__name__)


class GenericAPIBackedViewSet(web.GenericViewSet):
    # Make lookup_value_regex to any set of non-forward-slash characters. Many
    # Airavata ids contains period ('.') which the default lookup_value_regex
    # in DRF doesn't allow.
    lookup_value_regex = "[^/]+"

    def get_list(self):
        """
        Subclasses must implement.
        """
        raise NotImplementedError()

    def get_instance(self, lookup_value):
        """
        Subclasses must implement.
        """
        raise NotImplementedError()

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        inst = self.get_instance(lookup_value)
        if inst is None:
            raise Http404
        self.check_object_permissions(self.request, inst)
        return inst

    @property
    def username(self):
        return self.request.user.username

    @property
    def gateway_id(self):
        return settings.GATEWAY_ID


class APIBackedViewSet(
    web.mixins.CreateModelMixin,
    web.mixins.RetrieveModelMixin,
    web.mixins.UpdateModelMixin,
    web.mixins.DestroyModelMixin,
    web.mixins.ListModelMixin,
    GenericAPIBackedViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.

    Subclasses must implement the following:
    * get_list(self)
    * get_instance(self, lookup_value)
    * perform_create(self, serializer) - should return instance with id populated
    * perform_update(self, serializer)
    * perform_destroy(self, instance)
    """

    pass


class SdkResourceViewSet(
    web.mixins.CreateModelMixin,
    web.mixins.RetrieveModelMixin,
    web.mixins.UpdateModelMixin,
    web.mixins.ListModelMixin,
    GenericAPIBackedViewSet,
):
    """CRUD over an SDK ``*_resources`` helper that returns proto-direct values
    (protos / ``WithAccess`` envelopes), rendered by the global ``ProtoJSONRenderer``.

    A subclass declares the helper module via ``sdk()`` and the helper function
    names (``list_fn`` / ``get_fn`` / ``create_fn`` / ``update_fn``). Each action
    calls ``sdk().<fn>(client, *args, **extra_kwargs)`` where ``extra_kwargs``
    comes from :meth:`extra_kwargs` (the per-request ``has_write`` /
    ``is_gateway_admin`` flag families thread through it) and the positional args
    come from the overridable ``*_args`` builders (deviating families — e.g. a
    ``GATEWAY_ID``-threaded one — override only the builder they need).

    No ``destroy`` here: delete signatures vary too much (some take the lookup id,
    some the fetched instance, some thread ``GATEWAY_ID``), so a family that
    supports delete mixes in ``DestroyModelMixin`` and declares its own.

    Set ``paginate = True`` to page ``list`` through ``APIResultPagination``
    (the helper must accept ``limit`` / ``offset``).
    """

    list_fn = None
    get_fn = None
    create_fn = None
    update_fn = None

    paginate = False

    @staticmethod
    def sdk():
        raise NotImplementedError

    # Extra keyword args threaded into the get/create/update helper calls (e.g.
    # has_write). The gateway-catalog / sharing families override this.
    def extra_kwargs(self):
        return {}

    # List-only keyword args; defaults to extra_kwargs() so the common
    # has_write flag flows through. Override to add list-specific kwargs.
    def list_kwargs(self):
        return self.extra_kwargs()

    # Per-request render hook; identity by default (ProtoJSONRenderer flattens
    # protos / envelopes). Families that merge a portal-only field override it.
    def render(self, obj):
        return obj

    def _render_list(self, results):
        return [self.render(r) for r in results]

    # Positional arg builders (after the client). Override only when a family's
    # helper signature deviates from the (lookup_value,) / (data,) defaults.
    def list_args(self):
        return ()

    def get_args(self, lookup_value):
        return (lookup_value,)

    def create_args(self, data):
        return (data,)

    def update_args(self, lookup_value, data):
        return (lookup_value, data)

    def _body(self):
        return self.request.data if isinstance(self.request.data, dict) else {}

    def get_instance(self, lookup_value):
        return getattr(self.sdk(), self.get_fn)(  # ty: ignore[invalid-argument-type]  # get_fn set by subclass
            self.request.airavata, *self.get_args(lookup_value), **self.extra_kwargs()
        )

    def _list_results(self, limit=-1, offset=0):
        kwargs = dict(self.list_kwargs())
        if self.paginate:
            kwargs.update(limit=limit, offset=offset)
        return getattr(self.sdk(), self.list_fn)(  # ty: ignore[invalid-argument-type]  # list_fn set by subclass
            self.request.airavata, *self.list_args(), **kwargs
        )

    def list(self, request, *args, **kwargs):
        if self.paginate:
            view = self

            class _Iterator(APIResultIterator):
                def get_results(self, limit=-1, offset=0):
                    return view._list_results(limit=limit, offset=offset)

            queryset = _Iterator()
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(self._render_list(page))
            return Response(self._render_list(queryset.get_results()))
        return Response(self._render_list(self._list_results()))

    def retrieve(self, request, *args, **kwargs):
        return Response(self.render(self.get_object()))

    def create(self, request, *args, **kwargs):
        result = getattr(self.sdk(), self.create_fn)(  # ty: ignore[invalid-argument-type]  # create_fn set by subclass
            request.airavata, *self.create_args(self._body()), **self.extra_kwargs()
        )
        return Response(self.render(result), status=201)

    def update(self, request, *args, **kwargs):
        lookup_value = self.kwargs[self.lookup_field or "pk"]
        result = getattr(self.sdk(), self.update_fn)(  # ty: ignore[invalid-argument-type]  # update_fn set by subclass
            request.airavata,
            *self.update_args(lookup_value, self._body()),
            **self.extra_kwargs(),
        )
        return Response(self.render(result))

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class APIResultIterator:
    """
    Iterable container over API results which allow limit/offset style slicing.
    """

    limit = -1
    offset = 0

    def __init__(self, query_params=None):
        self.query_params = query_params if query_params is not None else QueryDict()

    def get_results(self, limit=-1, offset=0):
        raise NotImplementedError("Subclasses must implement get_results")

    def __iter__(self):
        results = self.get_results(self.limit, self.offset)
        yield from results

    def __getitem__(self, key):
        if isinstance(key, slice):
            self.limit = key.stop - key.start
            self.offset = key.start
            return iter(self)
        else:
            return self.get_results(1, key)


class APIResultPagination(web.LimitOffsetPagination):
    """
    Based on DRF's LimitOffsetPagination; Airavata API pagination results don't
    have a known count, so it isn't always possible to know how many pages there
    are.
    """

    default_limit = 10

    def paginate_queryset(self, queryset, request, view=None):
        assert isinstance(queryset, APIResultIterator), (
            f"queryset is not an APIResultIterator: {queryset}"
        )
        self.query_params = queryset.query_params.copy()
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request

        # When a paged view is called from another view (for example, to get the
        # initial data to display), this pagination class needs to know the name
        # of the view being paginated.
        if view and hasattr(view, "pagination_viewname"):
            self.viewname = view.pagination_viewname

        return list(queryset[self.offset : self.offset + self.limit])

    def get_limit(self, request):
        # If limit <= 0 then don't paginate
        if (
            self.limit_query_param in request.query_params
            and int(request.query_params[self.limit_query_param]) <= 0
        ):
            return None
        return super().get_limit(request)

    def get_paginated_response(self, data):
        has_next_link = len(data) >= self.limit
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link() if has_next_link else None),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                    ("limit", self.limit),
                    ("offset", self.offset),
                ]
            )
        )

    def get_next_link(self):
        url = self.get_base_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self):
        if self.offset <= 0:
            return None

        url = self.get_base_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)

        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_base_url(self):
        if hasattr(self, "viewname"):
            base_url = self.request.build_absolute_uri(reverse(self.viewname))
            if len(self.query_params) > 0:
                base_url += f"?{self.query_params.urlencode()}"
            return base_url
        else:
            return self.request.build_absolute_uri()


def convert_utc_iso8601_to_date(iso8601_utc_string):
    # This is meant to convert a JavaScript `new Date().toJSON()` into a
    # datetime instance
    timestamp = datetime.strptime(iso8601_utc_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = timestamp.replace(tzinfo=UTC)
    logger.debug(f"convert_utc_iso8601_to_date({iso8601_utc_string})={timestamp}")
    return timestamp


class IsInAdminsGroupPermission(web.permissions.BasePermission):
    message = "User must be member of the Admins or Read Only Admins groups."

    def has_permission(self, request, view):
        # Read Only Admins can make GET requests only
        if request.method in web.SAFE_METHODS:
            return request.is_gateway_admin or request.is_read_only_gateway_admin
        else:
            return request.is_gateway_admin


def _storage_root_relative(path):
    """Reduce a storage path to its form relative to the storage filesystem root so
    it can be compared uniformly against the configured shared-directory names.

    The server now resolves paths against the storage root, so the same logical
    location may arrive as a bare-relative ("Proj/Exp"), home ("~/Proj/Exp") or
    absolute ("/storage/Proj/Exp") path. Previously an absolute path was treated as
    "not shared" outright, which silently bypassed the admin-only write gate on
    gateway-shared directories. Normalize all three forms here instead.
    """
    if not path:
        return ""
    if path == "~":
        return ""
    if path.startswith("~/"):
        return path[2:]
    if os.path.isabs(path):
        root = getattr(settings, "GATEWAY_DATA_STORAGE_ROOT", None)
        if root:
            root = root.rstrip("/") + "/"
            if path.startswith(root):
                return path[len(root):]
        return path.lstrip("/")
    return path


def is_shared_dir(path):
    shared_dirs: dict = getattr(settings, "GATEWAY_DATA_SHARED_DIRECTORIES", {})
    rel = _storage_root_relative(path)
    return any(Path(_storage_root_relative(n)) == Path(rel) for n in shared_dirs)


def is_shared_path(path):
    shared_dirs: dict = getattr(settings, "GATEWAY_DATA_SHARED_DIRECTORIES", {})
    rel = _storage_root_relative(path)
    if not rel:
        return False
    # check if path starts with a shared directory (compared root-relative)
    return any(
        os.path.commonpath((_storage_root_relative(n), rel)) == _storage_root_relative(n)
        for n in shared_dirs
    )


class BaseSharedDirPermission(web.permissions.BasePermission):
    def get_path(self, request, view) -> str:
        raise NotImplementedError()

    def has_permission(self, request, view):
        if request.method in web.SAFE_METHODS:
            return True

        path = self.get_path(request, view)

        # check if path starts with a shared directory
        shared_path = is_shared_path(path)
        shared_dir = is_shared_dir(path)
        if shared_path:
            # No user can delete a shared directory
            if shared_dir and request.method == "DELETE":
                return False
            # Only admins can create/update/delete files/directories in a shared directory
            return request.is_gateway_admin

        return True


def data_product_file_path(data_product):
    """First replica's ``file_path`` from a proto ``DataProductModel``, or None.

    The gRPC ``storage`` facade expects the FULL FILE PATH, absolute or
    ``~/``-prefixed (a bare relative path NPEs server-side, as ``resolvePath``
    expands ``~/`` to the storage root). Replica file paths are typically
    absolute (e.g. ``/storage/tmp/<file>``); a relative one is ``~/``-prefixed.
    """
    replicas = data_product.replica_locations
    if not replicas:
        return None
    file_path = replicas[0].file_path
    if not file_path:
        return None
    if not (file_path.startswith("/") or file_path.startswith("~/")):
        file_path = "~/" + file_path
    return file_path


class DataProductSharedDirPermission(BaseSharedDirPermission):
    def get_path(self, request, view) -> str:
        data_product_uri = request.query_params.get(
            "data-product-uri", request.query_params.get("product-uri", "")
        )
        data_product = request.airavata.research.get_data_product(data_product_uri)
        file_path = data_product_file_path(data_product)
        return file_path or ""


class UserStorageSharedDirPermission(BaseSharedDirPermission):
    def get_path(self, request, view):
        # 'path' can be a url path parameter, query parameter or in the request body (data)
        return request.query_params.get(
            "path", request.data.get("path", view.kwargs.get("path"))
        )
