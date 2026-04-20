import base64
import json
import logging

from airavata_sdk import AiravataClient  # ty: ignore[unresolved-import]
from django.conf import settings

log = logging.getLogger(__name__)


def _decode_jwt_payload(token: str) -> dict:
    """Decode the JWT payload segment WITHOUT validating the signature.

    The Airavata server validates the token independently; here we just want to
    propagate `realm_access` and `groups` claims into the `x-claims` gRPC header
    so the server's GrpcAuthInterceptor can populate UserContext.groups/roles.
    """
    if not token or token.count(".") < 2:
        return {}
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload).decode())
    except Exception as e:  # noqa: BLE001 — intentional broad catch
        log.debug(f"Failed to decode JWT payload for claims propagation: {e}")
        return {}


def create_airavata_client(access_token: str, gateway_id: str, username: str = "") -> AiravataClient:
    """Create an AiravataClient instance for the given auth token."""
    claims: dict[str, str] = {"gatewayID": gateway_id, "userName": username}
    # Propagate realm_access + groups so the server's UserContext (and thus the
    # project-membership-aware resolvers) sees the caller's group memberships.
    # x-claims flattens every value to a JSON string — match the format the
    # GrpcAuthInterceptor expects (it re-parses these specific claims).
    payload = _decode_jwt_payload(access_token)
    if "realm_access" in payload:
        claims["realm_access"] = json.dumps(payload["realm_access"])
    if "groups" in payload:
        claims["groups"] = json.dumps(payload["groups"])
    return AiravataClient(
        host=settings.AIRAVATA_API_HOST,
        port=settings.AIRAVATA_API_PORT,
        token=access_token,
        gateway_id=gateway_id,
        secure=getattr(settings, "AIRAVATA_API_SECURE", False),
        claims=claims,
    )
