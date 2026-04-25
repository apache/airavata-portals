from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from django_airavata.apps.api import launcher_views  # for the patch target


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


class LauncherWriteViewsTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        self.client.force_authenticate(user=self.user)
        self.draft = {
            "name": "test-run",
            "project_id": "proj-1",
            "app_id": "namd",
            "interface_name": "run",
            "inputs": {"steps": 100},
            "outputs": {"trajectory": {"storage_id": "my-home", "path": "/x/out.dcd"}},
            "runtime": {
                "compute_resource_id": "bridges-2",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 64,
            },
        }

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_returns_script_and_command(self):
        resp = self.client.post("/api/launcher/experiment-drafts/preview/", self.draft, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("invocation_command", body)
        self.assertIn("script_contents", body)
        self.assertIn("warnings", body)
        self.assertTrue(body["script_contents"].startswith("#!/bin/bash"))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_rejects_invalid_draft(self):
        bad = dict(self.draft)
        bad["runtime"] = {**bad["runtime"], "walltime": "garbage"}
        resp = self.client.post("/api/launcher/experiment-drafts/preview/", bad, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("runtime", resp.json())

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_returns_502_when_client_unreachable(self):
        with patch.object(launcher_views, "_client") as mock_client:
            mock_client.return_value.generate_preview.side_effect = ConnectionError("airavata down")
            resp = self.client.post("/api/launcher/experiment-drafts/preview/", self.draft, format="json")
        self.assertEqual(resp.status_code, 502)
        self.assertIn("message", resp.json())

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_create_returns_experiment_id(self):
        resp = self.client.post("/api/launcher/experiment-drafts/", self.draft, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIn("experiment_id", resp.json())
