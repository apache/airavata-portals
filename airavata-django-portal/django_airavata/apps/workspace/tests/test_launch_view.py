from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.test import TestCase

# Fake authz token returned by the patched get_authz_token so that
# authz_token_middleware doesn't log out the test user.
_FAKE_AUTHZ_TOKEN = {
    "accessToken": "test.eyJ1c2VybmFtZSI6ImFsaWNlIn0.sig",
    "gatewayID": "test-gateway",
    "userName": "alice",
}


class LaunchViewTest(TestCase):
    def setUp(self):
        # Disconnect portal signal handlers that require request.authz_token,
        # which is not present on plain Django test requests.
        user_logged_in.disconnect(dispatch_uid="auth_initialize_user_profile")
        user_logged_in.disconnect(dispatch_uid="auth_project_auto_provisioning")

        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        self.client.force_login(self.user)

        # authz_token_middleware calls get_authz_token and logs out the user if
        # it returns None (because there's no real Keycloak session in tests).
        # Patch it to return a fake token so the test user stays logged in.
        self._authz_patcher = patch(
            "django_airavata.apps.auth.middleware.utils.get_authz_token",
            return_value=_FAKE_AUTHZ_TOKEN,
        )
        self._authz_patcher.start()

        # {% vite_asset %} requires a built manifest entry for js/entry-launch.ts,
        # which won't exist until Task 9 builds it. Patch the tag to return an
        # empty string so template rendering doesn't error out in unit tests.
        self._vite_patcher = patch(
            "django_vite.templatetags.django_vite.DjangoViteAssetLoader.instance",
            return_value=_FakeViteLoader(),
        )
        self._vite_patcher.start()

    def tearDown(self):
        self._authz_patcher.stop()
        self._vite_patcher.stop()

        # Re-connect the signal handlers so other test suites are not affected.
        from django_airavata.apps.auth.signals import initialize_user_profile, provision_user_projects

        user_logged_in.connect(
            initialize_user_profile,
            dispatch_uid="auth_initialize_user_profile",
        )
        user_logged_in.connect(
            provision_user_projects,
            dispatch_uid="auth_project_auto_provisioning",
        )

    def test_launch_renders_for_authenticated_user(self):
        resp = self.client.get("/workspace/launch")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="launch-app"')

    def test_old_create_experiment_url_redirects_to_launch(self):
        resp = self.client.get("/workspace/applications/anything/create_experiment", follow=False)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "/workspace/launch")

    def test_old_applications_url_redirects_to_launch(self):
        resp = self.client.get("/workspace/applications", follow=False)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "/workspace/launch")

    def test_launch_requires_auth(self):
        self.client.logout()
        self._authz_patcher.stop()
        self._authz_patcher = patch(
            "django_airavata.apps.auth.middleware.utils.get_authz_token",
            return_value=None,
        )
        self._authz_patcher.start()
        resp = self.client.get("/workspace/launch", follow=False)
        # Login redirect — exact path depends on AUTH_LOGIN_URL but we check redirect or 401
        self.assertIn(resp.status_code, (302, 401))


class _FakeViteLoader:
    """Minimal stub for DjangoViteAssetLoader used in tests only."""

    def generate_vite_asset(self, path, app=None, **kwargs):
        return ""

    def generate_vite_asset_url(self, path, app=None, **kwargs):
        return ""
