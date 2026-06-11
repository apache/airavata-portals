from django.urls import re_path

from django_airavata.apps.api import web

from . import views

# (prefix, viewset, basename) — reproduced via web.route() (DefaultRouter
# equivalent: list/detail/@action routes, no .json suffix, no api-root, no
# browsable API). Router routes come BEFORE the explicit re_paths (DRF order).
_viewsets = [
    (r'projects', views.ProjectViewSet, 'project'),
    (r'experiments', views.ExperimentViewSet, 'experiment'),
    (r'full-experiments', views.FullExperimentViewSet, 'full-experiment'),
    (r'experiment-search', views.ExperimentSearchViewSet, 'experiment-search'),
    (r'groups', views.GroupViewSet, 'group'),
    (r'application-interfaces', views.ApplicationInterfaceViewSet,
     'application-interface'),
    (r'applications', views.ApplicationModuleViewSet, 'application'),
    (r'application-deployments', views.ApplicationDeploymentViewSet,
     'application-deployment'),
    (r'user-profiles', views.UserProfileViewSet, 'user-profile'),
    (r'group-resource-profiles', views.GroupResourceProfileViewSet,
     'group-resource-profile'),
    (r'shared-entities', views.SharedEntityViewSet, 'shared-entity'),
    (r'compute-resources', views.ComputeResourceViewSet, 'compute-resource'),
    (r'storage-resources', views.StorageResourceViewSet, 'storage-resource'),
    (r'credential-summaries', views.CredentialSummaryViewSet,
     'credential-summary'),
    (r'storage-preferences', views.StoragePreferenceViewSet,
     'storage-preference'),
    (r'parsers', views.ParserViewSet, 'parser'),
    (r'manage-notifications', views.ManageNotificationViewSet,
     'manage-notifications'),
    (r'iam-user-profiles', views.IAMUserViewSet, 'iam-user-profile'),
    (r'unverified-email-users', views.UnverifiedEmailUserViewSet,
     'unverified-email-user-profile'),
    (r'queue-settings-calculators', views.QueueSettingsCalculatorViewSet,
     'queue-settings-calculator'),
]

_router_urlpatterns = [
    url
    for prefix, viewset, basename in _viewsets
    for url in web.route(prefix, viewset, basename)
]

app_name = 'django_airavata_api'
urlpatterns = [
    *_router_urlpatterns,
    re_path(r'^upload$', views.upload_input_file, name='upload_input_file'),
    re_path(r'^tus-upload-finish$', views.tus_upload_finish,
            name='tus_upload_finish'),
    re_path(r'^download-file$', views.download, name='download-file'),
    re_path(r'^download', views.download_file, name='download_file'),
    re_path(r'^delete-file$', views.delete_file, name='delete_file'),
    re_path(r'^data-products', views.DataProductView.as_view(),
            name='data-products-detail'),
    re_path(r'^job/submission/local', views.LocalJobSubmissionView.as_view(),
            name="local_job_submission"),
    re_path(r'^job/submission/cloud', views.CloudJobSubmissionView.as_view(),
            name="cloud_job_submission"),
    re_path(r'^job/submission/ssh', views.SshJobSubmissionView.as_view(),
            name="ssh_job_submission"),
    re_path(r'^job/submission/unicore', views.UnicoreJobSubmissionView.as_view(),
            name="unicore_job_submission"),
    re_path(r'^data/movement/gridftp', views.GridFtpDataMovementView.as_view(),
            name="grid_ftp_data_movement"),
    re_path(r'^data/movement/local', views.LocalDataMovementView.as_view(),
            name="local_ftp_data_movement"),
    re_path(r'^data/movement/scp', views.ScpDataMovementView.as_view(),
            name="scp_ftp_data_movement"),
    re_path(r'^gateway-resource-profile',
            views.CurrentGatewayResourceProfile.as_view(),
            name="current_gateway_resource_profile"),
    re_path(r'^workspace-preferences',
            views.WorkspacePreferencesView.as_view(),
            name="workspace-preferences"),
    re_path(r'^user-storage/~/(?P<path>.*)$',
            views.UserStoragePathView.as_view(),
            name="user-storage-items"),
    re_path(r'^experiment-storage/(?P<experiment_id>[^/]+)/(?P<path>.*)$',
            views.ExperimentStoragePathView.as_view(),
            name="experiment-storage-items"),
    re_path(r'^experiment-statistics',
            views.ExperimentStatisticsView.as_view(),
            name="experiment-statistics"),
    re_path(r'ack-notifications/<slug:id>/',
            views.AckNotificationViewSet.as_view(), name="ack-notifications"),
    re_path(r'ack-notifications/', views.AckNotificationViewSet.as_view(),
            name="ack-notifications"),
    re_path(r'^log', views.LogRecordConsumer.as_view(), name='log'),
    re_path(r'^settings', views.SettingsAPIView.as_view(), name='settings'),
    re_path(r'^api-status-check/',
            views.APIServerStatusCheckView.as_view(),
            name='api-status-check'),
    re_path(r'^notebook-output',
            views.notebook_output_view, name="notebook-output"),
    re_path(r'^html-output',
            views.html_output_view, name="html-output"),
    re_path(r'^image-output',
            views.image_output_view, name="image-output"),
    re_path(r'^link-output',
            views.link_output_view, name="link-output"),
    re_path(r'^experiment-archives/(?P<experiment_id>[^/]+)/',
            views.ExperimentArchiveView.as_view(),
            name="experiment-archives"),
]
