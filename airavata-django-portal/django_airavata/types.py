"""Type definitions for the Airavata Django Portal."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.http import HttpRequest

if TYPE_CHECKING:
    from airavata_sdk.client import AiravataClient  # ty: ignore[unresolved-import]


class AiravataRequest(HttpRequest):
    """Extended HttpRequest with Airavata client attached by middleware."""

    airavata_client: AiravataClient
    authz_token: dict[str, Any] | None
    is_gateway_admin: bool
    is_read_only_gateway_admin: bool
    active_nav_item: str
