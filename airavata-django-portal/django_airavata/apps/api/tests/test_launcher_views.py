from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase


class LauncherListingViewsTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        # Use DRF force_authenticate: bypasses session/CSRF and directly sets
        # request._force_auth_user so the view sees an authenticated user.
        # We don't need a real session for these thin-proxy views because the
        # ACCESS_TOKEN is only read by _client() to construct the LauncherClient,
        # and the stub client ignores the token entirely.
        self.client.force_authenticate(user=self.user)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_applications_list_default(self):
        resp = self.client.get("/api/launcher/applications/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(len(body["results"]) >= 1)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_applications_list_filters_by_search(self):
        resp = self.client.get("/api/launcher/applications/?search=namd")
        self.assertEqual(resp.status_code, 200)
        names = [a["name"] for a in resp.json()["results"]]
        self.assertIn("NAMD", names)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_application_detail(self):
        resp = self.client.get("/api/launcher/applications/namd/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["app_id"], "namd")

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_application_detail_not_found(self):
        resp = self.client.get("/api/launcher/applications/does-not-exist/")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("detail", resp.json())

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_resource_profile_for_project(self):
        resp = self.client.get("/api/launcher/projects/proj-1/resource-profile/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("compute_resources", body)
        self.assertIn("allocation_id", body)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_user_storages(self):
        resp = self.client.get("/api/launcher/storages/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(any(s.get("is_primary") for s in body["results"]))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_projects_list(self):
        resp = self.client.get("/api/launcher/projects/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(len(body["results"]) >= 1)
        self.assertIn("project_id", body["results"][0])
        self.assertIn("name", body["results"][0])

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_endpoints_require_auth(self):
        # Clear the forced authentication so the requests are anonymous.
        self.client.force_authenticate(user=None)
        for url in [
            "/api/launcher/applications/",
            "/api/launcher/applications/namd/",
            "/api/launcher/projects/proj-1/resource-profile/",
            "/api/launcher/storages/",
            "/api/launcher/projects/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 403)
