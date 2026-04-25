from unittest import TestCase

from django.test import override_settings

from django_airavata.apps.api import launcher_client


class StubLauncherClientTest(TestCase):
    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_applications_returns_at_least_one_app(self):
        client = launcher_client.get_client(user_token="ignored")
        apps = client.list_applications(category=None, search=None)
        self.assertTrue(len(apps) >= 1)
        first = apps[0]
        self.assertIn("app_id", first)
        self.assertIn("name", first)
        self.assertIn("content", first)
        self.assertIn("interfaces", first)
        self.assertIsInstance(first["interfaces"], list)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_get_resource_profile_returns_partitions(self):
        client = launcher_client.get_client(user_token="ignored")
        profile = client.get_project_resource_profile(project_id="proj-stub")
        self.assertIn("compute_resources", profile)
        self.assertIn("allocation_id", profile)
        self.assertTrue(len(profile["compute_resources"]) >= 1)
        self.assertIn("partitions", profile["compute_resources"][0])

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_generate_preview_returns_script_and_command(self):
        client = launcher_client.get_client(user_token="ignored")
        preview = client.generate_preview({
            "name": "x",
            "project_id": "proj-stub",
            "app_id": "app-stub",
            "interface_name": "run",
            "inputs": {},
            "outputs": {},
            "runtime": {
                "compute_resource_id": "cr-stub",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 8,
            },
        })
        self.assertIn("invocation_command", preview)
        self.assertIn("script_contents", preview)
        self.assertIn("warnings", preview)
        self.assertIsInstance(preview["warnings"], list)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_projects_returns_at_least_one(self):
        client = launcher_client.get_client(user_token="ignored")
        projects = client.list_projects()
        self.assertTrue(len(projects) >= 1)
        self.assertIn("project_id", projects[0])
        self.assertIn("name", projects[0])

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_generate_preview_emits_slurm_script_for_bridges(self):
        client = launcher_client.get_client(user_token="ignored")
        draft = {
            "name": "x",
            "project_id": "proj-stub",
            "app_id": "app-stub",
            "interface_name": "run",
            "inputs": {},
            "outputs": {},
            "runtime": {
                "compute_resource_id": "bridges-2",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 8,
            },
        }
        preview = client.generate_preview(draft)
        self.assertTrue(preview["invocation_command"].startswith("sbatch"))
        self.assertIn("#SBATCH", preview["script_contents"])

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_applications_filters_by_category(self):
        client = launcher_client.get_client(user_token="ignored")
        results = client.list_applications(category="Molecular Dynamics", search=None)
        self.assertTrue(len(results) >= 1)
        self.assertTrue(all(a["category"] == "Molecular Dynamics" for a in results))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_applications_filters_by_search(self):
        client = launcher_client.get_client(user_token="ignored")
        results = client.list_applications(category=None, search="namd")
        self.assertTrue(any("NAMD" in a["name"] for a in results))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_applications_search_returns_empty_when_no_match(self):
        client = launcher_client.get_client(user_token="ignored")
        self.assertEqual(client.list_applications(category=None, search="nonexistent-app"), [])
