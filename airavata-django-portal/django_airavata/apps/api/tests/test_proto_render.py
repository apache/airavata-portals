"""The single home for the proto-direct serialization invariants.

Every migrated read path renders through ``proto_render.to_jsonable``. The
contract it guarantees — and that the family snapshot tests
(``test_group_resource_profiles_contract`` for a oneof,
``test_per_protocol_job_submission_contract`` for enum-keyed maps,
``test_full_experiment_contract`` for a deep composed tree) lean on rather than
re-prove — is exercised here directly against ``to_jsonable`` / ``proto_to_dict``:

* keys are proto snake_case verbatim (no lowerCamelCase, no ``ID`` acronyms);
* enums render as the member NAME string;
* int64 / uint64 render as decimal STRINGS;
* every singular scalar is present even at its default (stable shape);
* ``WithAccess`` / ``WithGroupAccess`` merge their access scalars onto the
  flattened proto;
* lists/dicts recurse; a composed pydantic model recurses field-by-field so a
  proto carried wholesale inside it flows through the SAME renderer.
"""

from dataclasses import dataclass

from django.test import SimpleTestCase
from pydantic import BaseModel

from airavata_sdk.generated.org.apache.airavata.model.group import (
    group_manager_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.workspace import (
    workspace_pb2,
)
from airavata_sdk.helpers._envelope import WithAccess, WithGroupAccess
from django_airavata.apps.api.proto_render import proto_to_dict, to_jsonable


def _project(**overrides):
    fields = dict(
        project_id="p1", owner="alice", gateway_id="default", name="P",
        description="d", creation_time=1705320000000)
    fields.update(overrides)
    return workspace_pb2.Project(**fields)


class SnakeCaseKeysTest(SimpleTestCase):
    def test_keys_are_proto_snake_case(self):
        rendered = proto_to_dict(_project())
        for key in rendered:
            self.assertEqual(key, key.lower())
            self.assertNotIn("ID", key)

    def test_no_lower_camel_case_aliases(self):
        rendered = proto_to_dict(_project())
        for camel in ("projectId", "gatewayId", "creationTime"):
            self.assertNotIn(camel, rendered)


class EnumRendersAsNameTest(SimpleTestCase):
    def test_enum_value_is_member_name_string(self):
        # NotificationPriority.HIGH (int 3) must render as "HIGH", not 3.
        notification = workspace_pb2.Notification(
            notification_id="n1",
            priority=workspace_pb2.NotificationPriority.HIGH)
        rendered = proto_to_dict(notification)
        self.assertEqual(rendered["priority"], "HIGH")


class Int64RendersAsStringTest(SimpleTestCase):
    def test_int64_is_decimal_string(self):
        rendered = proto_to_dict(_project(creation_time=1705320000000))
        self.assertIsInstance(rendered["creation_time"], str)
        self.assertEqual(rendered["creation_time"], "1705320000000")

    def test_unset_int64_is_string_zero_not_absent(self):
        rendered = proto_to_dict(_project(creation_time=0))
        self.assertEqual(rendered["creation_time"], "0")


class StableShapeTest(SimpleTestCase):
    """always_print_fields_with_no_presence keeps every singular scalar present
    even at its default; repeated/message presence is unaffected."""

    def test_default_scalars_present(self):
        rendered = proto_to_dict(workspace_pb2.Project(project_id="p", owner="a"))
        self.assertEqual(rendered["description"], "")
        self.assertEqual(rendered["creation_time"], "0")

    def test_empty_repeated_is_empty_list(self):
        rendered = proto_to_dict(workspace_pb2.Project(project_id="p", owner="a"))
        self.assertEqual(rendered["shared_users"], [])


class WithAccessMergeTest(SimpleTestCase):
    def test_scalars_merged_onto_flattened_proto(self):
        rendered = to_jsonable(
            WithAccess(_project(), is_owner=True, user_has_write_access=False))
        self.assertEqual(rendered["project_id"], "p1")
        self.assertIs(rendered["is_owner"], True)
        self.assertIs(rendered["user_has_write_access"], False)


class WithGroupAccessMergeTest(SimpleTestCase):
    def test_six_group_flags_merged(self):
        group = group_manager_pb2.GroupModel(
            id="g1", name="G", owner_id="o", members=["a"])
        rendered = to_jsonable(WithGroupAccess(
            group, is_admin=True, is_owner=False, is_member=True,
            is_gateway_admins_group=False,
            is_read_only_gateway_admins_group=False,
            is_default_gateway_users_group=True))
        self.assertEqual(rendered["id"], "g1")
        self.assertEqual(
            {k: rendered[k] for k in (
                "is_admin", "is_owner", "is_member",
                "is_gateway_admins_group", "is_read_only_gateway_admins_group",
                "is_default_gateway_users_group")},
            {"is_admin": True, "is_owner": False, "is_member": True,
             "is_gateway_admins_group": False,
             "is_read_only_gateway_admins_group": False,
             "is_default_gateway_users_group": True})


class RecursionTest(SimpleTestCase):
    def test_list_of_protos_recurses(self):
        rendered = to_jsonable([_project(project_id="a"), _project(project_id="b")])
        self.assertEqual([r["project_id"] for r in rendered], ["a", "b"])

    def test_dict_recurses_values_keys_unchanged(self):
        rendered = to_jsonable({"by_id": _project(project_id="a")})
        self.assertEqual(rendered["by_id"]["project_id"], "a")

    def test_pydantic_model_recurses_field_by_field(self):
        # A composed model carries a proto and a WithAccess envelope wholesale;
        # each must flow through the SAME renderer, not model_dump().
        class _Composed(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            plain: str
            proto: object
            wrapped: object

        rendered = to_jsonable(_Composed(
            plain="x",
            proto=_project(project_id="bare"),
            wrapped=WithAccess(
                _project(project_id="env"), is_owner=True,
                user_has_write_access=True)))
        self.assertEqual(rendered["plain"], "x")
        self.assertEqual(rendered["proto"]["project_id"], "bare")
        self.assertEqual(rendered["wrapped"]["project_id"], "env")
        self.assertIs(rendered["wrapped"]["is_owner"], True)

    def test_scalars_pass_through(self):
        self.assertEqual(to_jsonable("s"), "s")
        self.assertEqual(to_jsonable(7), 7)
        self.assertIsNone(to_jsonable(None))
