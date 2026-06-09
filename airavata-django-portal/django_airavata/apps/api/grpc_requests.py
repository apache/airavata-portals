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

_GEN = "airavata_sdk.generated.org.apache.airavata.model"


def _pb2(path):
    return importlib.import_module(f"{_GEN}.{path}")


def password_credential(gateway_id, portal_user_name, login_user_name,
                         password, description):
    """Build a proto ``PasswordCredential`` from the create-password request."""
    return _pb2("credential.store.credential_store_pb2").PasswordCredential(
        gateway_id=gateway_id or '',
        portal_user_name=portal_user_name or '',
        login_user_name=login_user_name or '',
        password=password or '',
        description=description or '',
    )


def data_product_for_upload(*, gateway_id, owner_name, product_name, file_path,
                            storage_resource_id, content_type=None, product_size=0):
    """Build a proto ``DataProductModel`` to register for a freshly uploaded file.

    The gRPC ``storage.upload_file`` only transfers the bytes and returns a
    minimal ``DataProductModel``; the portal registers the full data product via
    ``research.register_data_product`` so the file gets a canonical product URI.
    Mirrors the legacy ``user_storage._create_data_product`` shape: a single
    GATEWAY_DATA_STORE / TRANSIENT replica pointing at ``file_path``, with the
    content type recorded under ``mime-type`` metadata.
    """
    rc = _pb2("data.replica.replica_catalog_pb2")
    product_metadata = {"mime-type": content_type} if content_type else {}
    return rc.DataProductModel(
        gateway_id=gateway_id,
        owner_name=owner_name,
        product_name=product_name,
        data_product_type=rc.DataProductType.FILE,
        product_size=product_size or 0,
        product_metadata=product_metadata,
        replica_locations=[rc.DataReplicaLocationModel(
            replica_name="{} gateway data store copy".format(product_name),
            replica_location_category=rc.ReplicaLocationCategory.GATEWAY_DATA_STORE,
            replica_persistent_type=rc.ReplicaPersistentType.TRANSIENT,
            storage_resource_id=storage_resource_id or '',
            file_path=file_path,
        )],
    )
