"""Adapters from gRPC protobuf messages to the attribute shape the existing
DRF serializers read.

Track D: while ``apps/api`` views are repointed from the Thrift API to the gRPC
facade (``request.airavata``), the portal keeps its REST contract with the Vue
frontend unchanged by reusing the existing serializers. Those serializers were
generated from the Thrift models, so they read Thrift attribute names
(``projectID``, ``creationTime``, ...). These adapters expose the corresponding
protobuf fields (``project_id``, ``creation_time``, ...) under those Thrift names,
so serializer output is identical by construction. They are removed once the
serializers are made protobuf-native.
"""

from types import SimpleNamespace


def project(pb):
    """gRPC ``Project`` protobuf -> ``ProjectSerializer`` (Thrift ``Project``) shape."""
    return SimpleNamespace(
        projectID=pb.project_id,
        owner=pb.owner,
        gatewayId=pb.gateway_id,
        name=pb.name,
        description=pb.description,
        # int64 epoch millis, like the Thrift field; 0 (unset) -> None for the
        # serializer's allow_null creationTime.
        creationTime=pb.creation_time or None,
        sharedUsers=list(pb.shared_users),
        sharedGroups=list(pb.shared_groups),
    )


def application_module(pb):
    """gRPC ``ApplicationModule`` protobuf -> ``ApplicationModuleSerializer`` shape."""
    return SimpleNamespace(
        appModuleId=pb.app_module_id,
        appModuleName=pb.app_module_name,
        appModuleVersion=pb.app_module_version,
        appModuleDescription=pb.app_module_description,
    )
