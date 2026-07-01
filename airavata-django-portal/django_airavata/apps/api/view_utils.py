from __future__ import annotations

import builtins
import logging
import os
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, override

from django.conf import settings
from django.http import Http404, HttpRequest
from django.http.request import QueryDict

from django_airavata.apps.api import web
from django_airavata.apps.api.web import (
    Response,
    remove_query_param,
    replace_query_param,
    reverse,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from airavata.model.data.replica.replica_catalog_pb2 import DataProductModel

    from django_airavata.request import AiravataRequest

logger = logging.getLogger(__name__)


class GenericAPIBackedViewSet(web.GenericViewSet):
    # Make lookup_value_regex to any set of non-forward-slash characters. Many
    # Airavata ids contains period ('.') which the default lookup_value_regex
    # in DRF doesn't allow.
    lookup_value_regex = "[^/]+"

    # The middleware-augmented request the dispatch layer assigns; typed here so
    # the viewset bodies read the portal-specific attributes with full typing.
    request: AiravataRequest

    def get_list(self) -> Any:
        """
        Subclasses must implement.
        """
        raise NotImplementedError()

    def get_instance(self, lookup_value: str) -> Any:
        """
        Subclasses must implement.
        """
        raise NotImplementedError()

    def get_object(self) -> Any:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        inst = self.get_instance(lookup_value)
        if inst is None:
            raise Http404
        self.check_object_permissions(self.request, inst)
        return inst

    @property
    def username(self) -> str:
        return self.request.user.username

    @property
    def gateway_id(self) -> str:
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
    """CRUD scaffolding for ViewSets backed by raw generated gRPC stubs.

    Subclasses implement ``get_instance`` / ``_list_results`` / ``create`` /
    ``update`` against their own service stub (built over
    ``request.airavata_channel``) and return proto-direct values (protos / raw
    ``*WithAccess`` protos), which the global ``ProtoJSONRenderer`` flattens. This
    base supplies the ``list`` (with optional pagination), ``retrieve`` and
    ``partial_update`` wiring plus the per-request ``render`` hook — it no longer
    wraps an SDK helper (every family now calls its stub directly).

    No ``destroy`` here: delete signatures vary too much (some take the lookup id,
    some the fetched instance, some thread ``GATEWAY_ID``), so a family that
    supports delete mixes in ``DestroyModelMixin`` and declares its own.

    Set ``paginate = True`` to page ``list`` through ``APIResultPagination`` (the
    subclass ``_list_results`` must accept ``limit`` / ``offset``).
    """

    paginate = False

    # Per-request render hook; identity by default (ProtoJSONRenderer flattens
    # protos). Families that merge a portal-only field override it.
    def render(self, obj: Any) -> Any:
        return obj

    def _list_results(self, limit: int = -1, offset: int = 0) -> builtins.list[Any]:
        """The list-action results (raw protos); subclasses implement against
        their own service stub. ``limit`` / ``offset`` page when ``paginate``."""
        raise NotImplementedError()

    def _render_list(self, results: Any) -> builtins.list[Any]:
        return [self.render(r) for r in results]

    # The (snake_case) request body as a dict; subclass create/update read it to
    # build the proto they submit.
    def _body(self) -> dict[str, Any]:
        return self.request.data if isinstance(self.request.data, dict) else {}

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> Response:
        if self.paginate:
            view = self

            class _Iterator(APIResultIterator):
                @override
                def get_results(self, limit: int = -1, offset: int = 0) -> list[Any]:
                    return view._list_results(limit=limit, offset=offset)

            queryset = _Iterator()
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(self._render_list(page))
            return Response(self._render_list(queryset.get_results()))
        return Response(self._render_list(self._list_results()))

    @override
    def retrieve(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> Response:
        return Response(self.render(self.get_object()))

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> Response:
        return self.update(request, *args, **kwargs)


class APIResultIterator:
    """
    Iterable container over API results which allow limit/offset style slicing.
    """

    limit = -1
    offset = 0

    def __init__(self, query_params: QueryDict | None = None) -> None:
        self.query_params = query_params if query_params is not None else QueryDict()

    def get_results(self, limit: int = -1, offset: int = 0) -> Iterable[Any]:
        raise NotImplementedError("Subclasses must implement get_results")

    def __iter__(self) -> Iterator[Any]:
        results = self.get_results(self.limit, self.offset)
        yield from results

    def __getitem__(self, key: slice | int) -> Any:
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

    @override
    def paginate_queryset(
        self, queryset: Any, request: AiravataRequest, view: Any = None
    ) -> list[Any] | None:
        assert isinstance(queryset, APIResultIterator), (
            f"queryset is not an APIResultIterator: {queryset}"
        )
        self.query_params = queryset.query_params.copy()
        limit = self.get_limit(request)
        if limit is None:
            return None
        self.limit = limit

        self.offset = self.get_offset(request)
        self.request = request

        # When a paged view is called from another view (for example, to get the
        # initial data to display), this pagination class needs to know the name
        # of the view being paginated.
        if view and hasattr(view, "pagination_viewname"):
            self.viewname = view.pagination_viewname

        return list(queryset[self.offset : self.offset + self.limit])

    @override
    def get_limit(self, request: AiravataRequest) -> int | None:
        # If limit <= 0 then don't paginate
        if (
            self.limit_query_param in request.query_params
            and int(request.query_params[self.limit_query_param]) <= 0
        ):
            return None
        return super().get_limit(request)

    @override
    def get_paginated_response(self, data: Any) -> Response:
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

    @override
    def get_next_link(self) -> str:
        url = self.get_base_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    @override
    def get_previous_link(self) -> str | None:
        if self.offset <= 0:
            return None

        url = self.get_base_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)

        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_base_url(self) -> str:
        if hasattr(self, "viewname"):
            base_url = self.request.build_absolute_uri(reverse(self.viewname))
            if len(self.query_params) > 0:
                base_url += f"?{self.query_params.urlencode()}"
            return base_url
        else:
            return self.request.build_absolute_uri()


def convert_utc_iso8601_to_date(iso8601_utc_string: str) -> datetime:
    # This is meant to convert a JavaScript `new Date().toJSON()` into a
    # datetime instance
    timestamp = datetime.strptime(iso8601_utc_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = timestamp.replace(tzinfo=UTC)
    logger.debug(f"convert_utc_iso8601_to_date({iso8601_utc_string})={timestamp}")
    return timestamp


class IsInAdminsGroupPermission(web.permissions.BasePermission):
    message = "User must be member of the Admins or Read Only Admins groups."

    @override
    def has_permission(self, request: HttpRequest, view: web.APIView) -> bool:
        # Read Only Admins can make GET requests only
        req = cast("AiravataRequest", request)
        if req.method in web.SAFE_METHODS:
            return req.is_gateway_admin or req.is_read_only_gateway_admin
        else:
            return req.is_gateway_admin


def _storage_root_relative(path: str | None) -> str:
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
                return path[len(root) :]
        return path.lstrip("/")
    return path


def is_shared_dir(path: str | None) -> bool:
    shared_dirs: dict[str, Any] = getattr(
        settings, "GATEWAY_DATA_SHARED_DIRECTORIES", {}
    )
    rel = _storage_root_relative(path)
    return any(Path(_storage_root_relative(n)) == Path(rel) for n in shared_dirs)


def is_shared_path(path: str | None) -> bool:
    shared_dirs: dict[str, Any] = getattr(
        settings, "GATEWAY_DATA_SHARED_DIRECTORIES", {}
    )
    rel = _storage_root_relative(path)
    if not rel:
        return False
    # check if path starts with a shared directory (compared root-relative)
    return any(
        os.path.commonpath((_storage_root_relative(n), rel))
        == _storage_root_relative(n)
        for n in shared_dirs
    )


class BaseSharedDirPermission(web.permissions.BasePermission):
    def get_path(self, request: AiravataRequest, view: web.APIView) -> str:
        raise NotImplementedError()

    @override
    def has_permission(self, request: HttpRequest, view: web.APIView) -> bool:
        req = cast("AiravataRequest", request)
        if req.method in web.SAFE_METHODS:
            return True

        path = self.get_path(req, view)

        # check if path starts with a shared directory
        shared_path = is_shared_path(path)
        shared_dir = is_shared_dir(path)
        if shared_path:
            # No user can delete a shared directory
            if shared_dir and req.method == "DELETE":
                return False
            # Only admins can create/update/delete files/directories in a shared directory
            return req.is_gateway_admin

        return True


def data_product_file_path(data_product: DataProductModel) -> str | None:
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
    @override
    def get_path(self, request: AiravataRequest, view: web.APIView) -> str:
        from airavata.services import data_product_service_pb2 as pb2
        from airavata.services.data_product_service_pb2_grpc import (
            DataProductServiceStub,
        )

        data_product_uri = request.query_params.get(
            "data-product-uri", request.query_params.get("product-uri", "")
        )
        data_product = DataProductServiceStub(request.airavata_channel).GetDataProduct(
            pb2.GetDataProductRequest(product_uri=data_product_uri)
        )
        file_path = data_product_file_path(data_product)
        return file_path or ""


class UserStorageSharedDirPermission(BaseSharedDirPermission):
    @override
    def get_path(self, request: AiravataRequest, view: web.APIView) -> str:
        # 'path' can be a url path parameter, query parameter or in the request body (data)
        return request.query_params.get(
            "path", request.data.get("path", view.kwargs.get("path"))
        )
