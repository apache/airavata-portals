"""Unit tests for the notifications context processor rewired off the SDK
facade (request.airavata.research.get_all_notifications) onto the raw
NotificationService stub over request.airavata_channel."""

import json
from unittest.mock import MagicMock, patch

from airavata.model.workspace import workspace_pb2
from airavata.services import notification_service_pb2
from django.test import RequestFactory, SimpleTestCase, override_settings

from django_airavata import context_processors

GATEWAY_ID = "test-gateway"

# Far-future expiration / past publish (epoch millis) so the notification is
# currently valid in get_notifications' window check.
_FAR_FUTURE_MS = 99999999999999
_PAST_MS = 1


@override_settings(GATEWAY_ID=GATEWAY_ID)
class GetNotificationsStubTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=True, username="alice")
        request.authz_token = object()
        request.airavata_channel = object()
        return request

    def _patch_stub(self, stub):
        return patch(
            "airavata.services.notification_service_pb2_grpc.NotificationServiceStub",
            return_value=stub,
        )

    def test_calls_get_all_notifications_and_counts_unread(self):
        notif = workspace_pb2.Notification(
            notification_id="n1",
            gateway_id=GATEWAY_ID,
            title="t",
            notification_message="m",
            published_time=_PAST_MS,
            expiration_time=_FAR_FUTURE_MS,
            priority=workspace_pb2.NotificationPriority.NORMAL,
        )
        stub = MagicMock()
        stub.GetAllNotifications.return_value = (
            notification_service_pb2.GetAllNotificationsResponse(notifications=[notif])
        )
        request = self._request()
        with (
            self._patch_stub(stub),
            patch.object(
                context_processors, "notification_read_state", return_value={}
            ),
        ):
            result = context_processors.get_notifications(request)
        sent = stub.GetAllNotifications.call_args.args[0]
        self.assertEqual(sent.gateway_id, GATEWAY_ID)
        self.assertEqual(result["unread_notifications"], 1)
        self.assertIn("n1", json.loads(result["notifications"])[0]["notificationId"])

    def test_stub_error_swallowed_to_empty(self):
        stub = MagicMock()
        stub.GetAllNotifications.side_effect = RuntimeError("boom")
        request = self._request()
        with self._patch_stub(stub):
            result = context_processors.get_notifications(request)
        self.assertEqual(result["unread_notifications"], 0)
        self.assertEqual(json.loads(result["notifications"]), [])

    def test_unauthenticated_returns_empty_without_calling_stub(self):
        stub = MagicMock()
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        request.airavata_channel = object()
        with self._patch_stub(stub):
            result = context_processors.get_notifications(request)
        stub.GetAllNotifications.assert_not_called()
        self.assertEqual(json.loads(result["notifications"]), [])
