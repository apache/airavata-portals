"""Adapters from the Thrift-shaped objects the DRF serializers produce to the
gRPC protobuf request messages the facade expects.

Track D (D3 writes): the ``apps/api`` serializers were generated from the Thrift
models, so ``serializer.save()`` yields a Thrift model instance (Thrift attribute
names: ``projectID``, ``gatewayId``, ...). These adapters convert that instance
into the corresponding protobuf message (``project_id``, ``gateway_id``, ...) so
the gRPC facade can send it. They are the write-direction mirror of
``grpc_adapters`` and are removed once the serializers are made protobuf-native.

proto3 scalar fields cannot hold ``None``, so optional Thrift values that may be
``None`` are coerced to the proto default (``''``/``0``/``[]``).
"""

import importlib


def _workspace_pb2():
    return importlib.import_module(
        "airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2")


def project(t):
    """Thrift ``Project`` -> proto ``Project`` request message."""
    return _workspace_pb2().Project(
        project_id=t.projectID or '',
        owner=t.owner or '',
        gateway_id=t.gatewayId or '',
        name=t.name or '',
        description=t.description or '',
        creation_time=t.creationTime or 0,
        shared_users=list(t.sharedUsers or []),
        shared_groups=list(t.sharedGroups or []),
    )
