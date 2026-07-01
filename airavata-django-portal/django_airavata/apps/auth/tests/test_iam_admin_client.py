"""The IAM-admin (Keycloak service-account) operations on the raw IamAdminService
stub: each builds a Bearer-authenticated channel from the service-account token and
calls the RPC directly (no SDK facade client)."""

from unittest.mock import MagicMock, patch

from airavata.model.user.user_profile_pb2 import (
    UserProfile,
)
from airavata.services import iam_admin_service_pb2
from django.test import SimpleTestCase

from django_airavata.apps.auth import iam_admin_client


class IamAdminClientStubTests(SimpleTestCase):
    def _run(self, stub, call):
        patches = [
            patch.object(
                iam_admin_client, "build_airavata_channel", return_value=MagicMock()
            ),
            patch(
                "airavata.services.iam_admin_service_pb2_grpc.IamAdminServiceStub",
                return_value=stub,
            ),
            patch.object(
                iam_admin_client.utils,
                "get_service_account_authz_token",
                return_value=MagicMock(accessToken="svc-token"),
            ),
        ]
        for p in patches:
            p.start()
        try:
            return call()
        finally:
            for p in reversed(patches):
                p.stop()

    def test_get_user_calls_get_user(self):
        stub = MagicMock()
        stub.GetUser.return_value = UserProfile(user_id="u1")
        result = self._run(stub, lambda: iam_admin_client.get_user("u1"))
        self.assertEqual(stub.GetUser.call_args.args[0].username, "u1")
        self.assertEqual(result.user_id, "u1")

    def test_get_users_returns_list(self):
        stub = MagicMock()
        stub.GetUsers.return_value = iam_admin_service_pb2.GetIamUsersResponse(
            users=[UserProfile(user_id="u1"), UserProfile(user_id="u2")]
        )
        result = self._run(stub, lambda: iam_admin_client.get_users(0, 10, "x"))
        sent = stub.GetUsers.call_args.args[0]
        self.assertEqual((sent.offset, sent.limit, sent.search), (0, 10, "x"))
        self.assertEqual([u.user_id for u in result], ["u1", "u2"])

    def test_is_username_available_returns_bool(self):
        stub = MagicMock()
        stub.IsUsernameAvailable.return_value = (
            iam_admin_service_pb2.IsUsernameAvailableResponse(available=True)
        )
        result = self._run(stub, lambda: iam_admin_client.is_username_available("u1"))
        self.assertEqual(stub.IsUsernameAvailable.call_args.args[0].username, "u1")
        self.assertTrue(result)

    def test_delete_user_calls_delete(self):
        stub = MagicMock()
        self._run(stub, lambda: iam_admin_client.delete_user("u1"))
        self.assertEqual(stub.DeleteUser.call_args.args[0].username, "u1")
