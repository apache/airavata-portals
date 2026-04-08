"""Compatibility layer for proto/Thrift types used throughout the portal.

These were previously imported from airavata.model.*.ttypes (Thrift-generated).
Now they come from the SDK's generated proto stubs. This module provides a
single import point so that downstream code doesn't need to know the origin.

For types that are only used as plain data containers (constructed with **kwargs
and read via attribute access), simple Python classes with __init__(**kwargs)
suffice since the SDK's gRPC facade returns these objects already.
"""

import enum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DataType(enum.IntEnum):
    STRING = 0
    INTEGER = 1
    FLOAT = 2
    URI = 3
    URI_COLLECTION = 4
    STDOUT = 5
    STDERR = 6


class ExperimentState(enum.IntEnum):
    CREATED = 0
    VALIDATED = 1
    SCHEDULED = 2
    LAUNCHED = 3
    EXECUTING = 4
    CANCELING = 5
    CANCELED = 6
    COMPLETED = 7
    FAILED = 8


class ExperimentType(enum.IntEnum):
    SINGLE_APPLICATION = 0
    WORKFLOW = 1


class ExperimentSearchFields(enum.IntEnum):
    EXPERIMENT_NAME = 0
    EXPERIMENT_DESC = 1
    APPLICATION_ID = 2
    STATUS = 3
    CREATION_TIME = 4
    PROJECT_ID = 5
    JOB_ID = 6


class SummaryType(enum.IntEnum):
    SSH = 0
    PASSWD = 1
    CERT = 2


class ResourcePermissionType(enum.IntEnum):
    WRITE = 0
    READ = 1
    MANAGE_SHARING = 2


class ResourceType(enum.IntEnum):
    SLURM = 0
    AWS = 1


class ApplicationParallelismType(enum.IntEnum):
    SERIAL = 0
    MPI = 1
    OPENMP = 2
    OPENMP_MPI = 3
    CCM = 4
    CRAY_MPI = 5


class NotificationPriority(enum.IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class Status(enum.IntEnum):
    ACTIVE = 0
    CONFIRMED = 1
    APPROVED = 2
    DELETED = 3
    DUPLICATE = 4
    GRACE_PERIOD = 5
    INVITED = 6
    DENIED = 7
    PENDING = 8
    PENDING_APPROVAL = 9
    PENDING_CONFIRMATION = 10
    SUSPENDED = 11
    DECLINED = 12
    EXPIRED = 13


# ---------------------------------------------------------------------------
# Data classes -- simple attribute-bag objects that mirror Thrift struct
# constructors.  The SDK facade returns proto objects that behave the same
# way (attribute access), so these are used mainly for *creating* new
# instances in serializers.
# ---------------------------------------------------------------------------


class _ThriftLikeBase:
    """Base that accepts **kwargs and sets them as attributes, with a
    thrift_spec class variable for backward compat with the serializer
    introspection in thrift_utils.py (now proto_utils.py)."""

    # Subclasses should define thrift_spec as a class variable.
    thrift_spec = ()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


# -- Application IO --


class InputDataObjectType(_ThriftLikeBase):
    pass


class OutputDataObjectType(_ThriftLikeBase):
    pass


# -- App Catalog: deployment --


class ApplicationDeploymentDescription(_ThriftLikeBase):
    pass


class ApplicationModule(_ThriftLikeBase):
    pass


class CommandObject(_ThriftLikeBase):
    pass


class SetEnvPaths(_ThriftLikeBase):
    pass


# -- App Catalog: interface --


class ApplicationInterfaceDescription(_ThriftLikeBase):
    pass


# -- App Catalog: compute resource --


class ComputeResourceDescription(_ThriftLikeBase):
    pass


class BatchQueue(_ThriftLikeBase):
    pass


class CloudJobSubmission(_ThriftLikeBase):
    pass


class GlobusJobSubmission(_ThriftLikeBase):
    pass


class LOCALSubmission(_ThriftLikeBase):
    pass


class SSHJobSubmission(_ThriftLikeBase):
    pass


class UnicoreJobSubmission(_ThriftLikeBase):
    pass


# -- App Catalog: gateway profile --


class GatewayResourceProfile(_ThriftLikeBase):
    pass


class StoragePreference(_ThriftLikeBase):
    pass


# -- App Catalog: group resource profile --


class ComputeResourceReservation(_ThriftLikeBase):
    pass


class GroupComputeResourcePreference(_ThriftLikeBase):
    pass


class GroupResourceProfile(_ThriftLikeBase):
    pass


class ComputeResourcePolicy(_ThriftLikeBase):
    pass


class BatchQueueResourcePolicy(_ThriftLikeBase):
    pass


class EnvironmentSpecificPreferences(_ThriftLikeBase):
    pass


class SlurmComputeResourcePreference(_ThriftLikeBase):
    pass


class AwsComputeResourcePreference(_ThriftLikeBase):
    pass


class GroupAccountSSHProvisionerConfig(_ThriftLikeBase):
    pass


# -- App Catalog: parser --


class Parser(_ThriftLikeBase):
    pass


# -- App Catalog: storage resource --


class StorageResourceDescription(_ThriftLikeBase):
    pass


# -- Credential store --


class CredentialSummary(_ThriftLikeBase):
    pass


# -- Data replica --


class DataProductModel(_ThriftLikeBase):
    pass


class DataReplicaLocationModel(_ThriftLikeBase):
    pass


# -- Data movement --


class GridFTPDataMovement(_ThriftLikeBase):
    pass


class LOCALDataMovement(_ThriftLikeBase):
    pass


class SCPDataMovement(_ThriftLikeBase):
    pass


class UnicoreDataMovement(_ThriftLikeBase):
    pass


# -- Experiment --


class ExperimentModel(_ThriftLikeBase):
    pass


class ExperimentStatistics(_ThriftLikeBase):
    pass


class ExperimentSummaryModel(_ThriftLikeBase):
    pass


# -- Group --


class GroupModel(_ThriftLikeBase):
    pass


# -- Job --


class JobModel(_ThriftLikeBase):
    pass


# -- Status --


class ExperimentStatus(_ThriftLikeBase):
    pass


class ProcessStatus(_ThriftLikeBase):
    pass


# -- User --


class UserProfile(_ThriftLikeBase):
    pass


# -- Workspace --


class Notification(_ThriftLikeBase):
    pass


class Project(_ThriftLikeBase):
    pass


# -- Gateway groups --


class GatewayGroups(_ThriftLikeBase):
    pass
