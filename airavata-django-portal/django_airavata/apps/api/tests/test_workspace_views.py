"""Regression + rewiring guards for the workspace create_experiment view.

create_experiment reads the application_interface action's proto-direct
ApplicationInterfaceWithAccess via .application_interface (was the retired
_envelope .message), and resolves airavata-dp:// URI inputs via the raw
DataProductService + UserStorageService stubs (was request.airavata.research /
request.airavata.storage).
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from airavata.model.appcatalog.appinterface import (
    app_interface_pb2,
)
from airavata.model.application.io import (
    application_io_pb2 as io,
)
from airavata.model.commons import commons_pb2
from airavata.model.data.replica import (
    replica_catalog_pb2,
)
from airavata.services import application_catalog_service_pb2
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from django_airavata.apps.workspace import views as workspace_views

GATEWAY_ID = "test-gateway"


@override_settings(GATEWAY_ID=GATEWAY_ID, PORTAL_APPLICATION_TEMPLATES={})
class CreateExperimentInterfaceProtoTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _iface_response(self, inputs):
        proto = application_catalog_service_pb2.ApplicationInterfaceWithAccess(
            application_interface=app_interface_pb2.ApplicationInterfaceDescription(
                application_interface_id="i1", application_inputs=inputs
            ),
            access=commons_pb2.AccessFlags(),
        )
        return SimpleNamespace(status_code=200, data=proto)

    def _run(self, inputs, query, extra_patches=()):
        request = self.factory.get(f"/workspace/applications/m1/create?{query}")
        request.user = MagicMock(is_authenticated=True, username="alice")
        request.airavata_channel = object()
        captured = {}

        def fake_render(req, template, context):
            captured.update(context)
            return HttpResponse("ok")

        patches = [
            patch.object(
                workspace_views.ApplicationModuleViewSet,
                "as_view",
                return_value=lambda *a, **k: self._iface_response(inputs),
            ),
            patch.object(workspace_views, "render", side_effect=fake_render),
            *extra_patches,
        ]
        for p in patches:
            p.start()
        try:
            response = workspace_views.create_experiment(request, app_module_id="m1")
        finally:
            for p in reversed(patches):
                p.stop()
        return response, captured

    def test_reads_application_interface_proto_and_collects_string_input(self):
        inputs = [io.InputDataObjectType(name="foo", type=io.DataType.STRING)]
        response, captured = self._run(inputs, "foo=bar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(captured["user_input_values"]), {"foo": "bar"})

    def test_uri_input_kept_when_data_product_file_exists(self):
        inputs = [io.InputDataObjectType(name="inp", type=io.DataType.URI)]
        dp_stub = SimpleNamespace(
            GetDataProduct=lambda req: replica_catalog_pb2.DataProductModel(
                replica_locations=[
                    replica_catalog_pb2.DataReplicaLocationModel(file_path="/storage/x")
                ]
            )
        )
        fs_stub = SimpleNamespace(FileExists=lambda req: SimpleNamespace(exists=True))
        extra = (
            patch(
                "airavata.services."
                "data_product_service_pb2_grpc.DataProductServiceStub",
                return_value=dp_stub,
            ),
            patch(
                "airavata.services.file_service_pb2_grpc.UserStorageServiceStub",
                return_value=fs_stub,
            ),
        )
        _response, captured = self._run(
            inputs, "inp=airavata-dp://x", extra_patches=extra
        )
        self.assertEqual(
            json.loads(captured["user_input_values"]), {"inp": "airavata-dp://x"}
        )

    def test_uri_input_dropped_when_file_missing(self):
        inputs = [io.InputDataObjectType(name="inp", type=io.DataType.URI)]
        dp_stub = SimpleNamespace(
            GetDataProduct=lambda req: replica_catalog_pb2.DataProductModel(
                replica_locations=[
                    replica_catalog_pb2.DataReplicaLocationModel(file_path="/storage/x")
                ]
            )
        )
        fs_stub = SimpleNamespace(FileExists=lambda req: SimpleNamespace(exists=False))
        extra = (
            patch(
                "airavata.services."
                "data_product_service_pb2_grpc.DataProductServiceStub",
                return_value=dp_stub,
            ),
            patch(
                "airavata.services.file_service_pb2_grpc.UserStorageServiceStub",
                return_value=fs_stub,
            ),
        )
        _response, captured = self._run(
            inputs, "inp=airavata-dp://x", extra_patches=extra
        )
        self.assertEqual(json.loads(captured["user_input_values"]), {})
