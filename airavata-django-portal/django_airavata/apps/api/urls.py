import logging

from django.urls import re_path
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import launcher_views
from . import views
from . import views_ssh

logger = logging.getLogger(__name__)

router = routers.DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="project")
router.register(r"experiments", views.ExperimentViewSet, basename="experiment")
router.register(r"full-experiments", views.FullExperimentViewSet, basename="full-experiment")
router.register(r"experiment-search", views.ExperimentSearchViewSet, basename="experiment-search")
router.register(r"groups", views.GroupViewSet, basename="group")
router.register(r"application-interfaces", views.ApplicationInterfaceViewSet, basename="application-interface")
router.register(r"applications", views.ApplicationModuleViewSet, basename="application")
router.register(r"application-deployments", views.ApplicationDeploymentViewSet, basename="application-deployment")
router.register(r"user-profiles", views.UserProfileViewSet, basename="user-profile")
router.register(
    r"project-resource-profiles", views.ProjectResourceProfileViewSet, basename="project-resource-profile"
)
router.register(r"shared-entities", views.SharedEntityViewSet, basename="shared-entity")
router.register(r"compute-resources", views.ComputeResourceViewSet, basename="compute-resource")
router.register(r"storage-resources", views.StorageResourceViewSet, basename="storage-resource")
router.register(r"credential-summaries", views.CredentialSummaryViewSet, basename="credential-summary")
router.register(r"storage-preferences", views.StoragePreferenceViewSet, basename="storage-preference")
router.register(r"parsers", views.ParserViewSet, basename="parser")
router.register(r"manage-notifications", views.ManageNotificationViewSet, basename="manage-notifications")
router.register(r"iam-user-profiles", views.IAMUserViewSet, basename="iam-user-profile")
router.register(r"unverified-email-users", views.UnverifiedEmailUserViewSet, basename="unverified-email-user-profile")
router.register(
    r"queue-settings-calculators", views.QueueSettingsCalculatorViewSet, basename="queue-settings-calculator"
)

app_name = "django_airavata_api"
urlpatterns = [
    re_path(r"^upload$", views.upload_input_file, name="upload_input_file"),
    re_path(r"^tus-upload-finish$", views.tus_upload_finish, name="tus_upload_finish"),
    re_path(r"^download", views.download_file, name="download_file"),
    re_path(r"^delete-file$", views.delete_file, name="delete_file"),
    re_path(r"^data-products", views.DataProductView.as_view(), name="data-products-detail"),
    re_path(r"^job/submission/local", views.LocalJobSubmissionView.as_view(), name="local_job_submission"),
    re_path(r"^job/submission/cloud", views.CloudJobSubmissionView.as_view(), name="cloud_job_submission"),
    re_path(r"^job/submission/globus", views.GlobusJobSubmissionView.as_view(), name="globus_job_submission"),
    re_path(r"^job/submission/ssh", views.SshJobSubmissionView.as_view(), name="ssh_job_submission"),
    re_path(r"^job/submission/unicore", views.UnicoreJobSubmissionView.as_view(), name="unicore_job_submission"),
    re_path(r"^data/movement/gridftp", views.GridFtpDataMovementView.as_view(), name="grid_ftp_data_movement"),
    re_path(r"^data/movement/local", views.LocalDataMovementView.as_view(), name="local_ftp_data_movement"),
    re_path(r"^data/movement/unicore", views.UnicoreDataMovementView.as_view(), name="unicore_ftp_data_movement"),
    re_path(r"^data/movement/scp", views.ScpDataMovementView.as_view(), name="scp_ftp_data_movement"),
    re_path(
        r"^gateway-resource-profile",
        views.CurrentGatewayResourceProfile.as_view(),
        name="current_gateway_resource_profile",
    ),
    re_path(r"^workspace-preferences", views.WorkspacePreferencesView.as_view(), name="workspace-preferences"),
    re_path(r"^user-storage/~/(?P<path>.*)$", views.UserStoragePathView.as_view(), name="user-storage-items"),
    re_path(
        r"^experiment-storage/(?P<experiment_id>[^/]+)/(?P<path>.*)$",
        views.ExperimentStoragePathView.as_view(),
        name="experiment-storage-items",
    ),
    re_path(r"^experiment-statistics", views.ExperimentStatisticsView.as_view(), name="experiment-statistics"),
    re_path(r"ack-notifications/<slug:id>/", views.AckNotificationViewSet.as_view(), name="ack-notifications"),
    re_path(r"ack-notifications/", views.AckNotificationViewSet.as_view(), name="ack-notifications"),
    re_path(r"^log", views.LogRecordConsumer.as_view(), name="log"),
    re_path(r"^settings/local/?$", views.LocalSettingsFileView.as_view(), name="settings-local"),
    re_path(r"^settings", views.SettingsAPIView.as_view(), name="settings"),
    re_path(r"^api-status-check/", views.APIServerStatusCheckView.as_view(), name="api-status-check"),
    re_path(r"^notebook-output", views.notebook_output_view, name="notebook-output"),
    re_path(r"^html-output", views.html_output_view, name="html-output"),
    re_path(r"^image-output", views.image_output_view, name="image-output"),
    re_path(r"^link-output", views.link_output_view, name="link-output"),
    re_path(
        r"^experiment-archives/(?P<experiment_id>[^/]+)/",
        views.ExperimentArchiveView.as_view(),
        name="experiment-archives",
    ),
    # SSE and SSH proxy endpoints
    re_path(r"^events/$", views_ssh.sse_events, name="sse-events"),
    re_path(r"^ssh/test/$", views_ssh.ssh_test, name="ssh-test"),
    re_path(r"^ssh/respond/$", views_ssh.ssh_respond, name="ssh-respond"),
    re_path(r"^ssh/run/$", views_ssh.ssh_run, name="ssh-run"),
    re_path(r"^ssh/run-info/$", views_ssh.ssh_run_info, name="ssh-run-info"),
    re_path(r"^ssh/close/$", views_ssh.ssh_close, name="ssh-close"),
    re_path(r"^ssh/sync-slurm-accounting/$", views_ssh.sync_slurm_accounting, name="sync_slurm_accounting"),
]

urlpatterns = router.urls + format_suffix_patterns(urlpatterns)

# Launcher endpoints — thin proxies over launcher_client.
# The parameterized project route must be listed before the bare projects list
# so Django's regex matcher resolves it first.
urlpatterns += [
    re_path(r"^launcher/applications/$", launcher_views.applications_list, name="launcher_applications_list"),
    re_path(
        r"^launcher/applications/(?P<app_id>[^/]+)/$",
        launcher_views.application_detail,
        name="launcher_application_detail",
    ),
    re_path(
        r"^launcher/projects/(?P<project_id>[^/]+)/resource-profile/$",
        launcher_views.project_resource_profile,
        name="launcher_project_resource_profile",
    ),
    re_path(r"^launcher/storages/$", launcher_views.user_storages, name="launcher_user_storages"),
    re_path(r"^launcher/projects/$", launcher_views.projects_list, name="launcher_projects_list"),
]

if logger.isEnabledFor(logging.DEBUG):
    for router_url in router.urls:
        logger.debug(f"router url: {router_url}")
