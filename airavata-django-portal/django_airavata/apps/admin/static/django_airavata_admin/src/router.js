import ApplicationDeploymentEditor from "./components/applications/ApplicationDeploymentEditor.vue";
import ApplicationDeploymentsList from "./components/applications/ApplicationDeploymentsList.vue";
import ApplicationEditorContainer from "./components/applications/ApplicationEditorContainer.vue";
import ApplicationInterfaceEditor from "./components/applications/ApplicationInterfaceEditor.vue";
import ApplicationModuleEditor from "./components/applications/ApplicationModuleEditor.vue";
import ApplicationsDashboard from "./components/dashboards/ApplicationsDashboard.vue";
import CredentialStoreDashboard from "./components/dashboards/CredentialStoreDashboard";
import DevelopersContainer from "./components/developers//DevelopersContainer.vue";
import ExperimentStatisticsContainer from "./components/statistics/ExperimentStatisticsContainer";
import ExtendedUserProfileContainer from "./components/users/ExtendedUserProfileContainer";
import GatewayResourceProfileEditorContainer from "./components/gatewayprofile/GatewayResourceProfileEditorContainer.vue";
import IdentityServiceUserManagementContainer from "./components/users/IdentityServiceUserManagementContainer.vue";
import UnverifiedEmailUserManagementContainer from "./components/users/UnverifiedEmailUserManagementContainer.vue";
import UserManagementContainer from "./components/users/UserManagementContainer.vue";
import NoticesManagementContainer from "./components/notices/NoticesManagementContainer.vue";
export const routes = [
  {
    path: "/applications/new",
    component: ApplicationEditorContainer,
    name: "new_application",
    children: [
      // Only the module route for a new application, save it and then replace
      // the URL with the module id
      {
        path: "",
        components: {
          module: ApplicationModuleEditor,
        },
        name: "new_application_module",
      },
    ],
  },
  {
    path: "/applications/:id",
    component: ApplicationEditorContainer,
    name: "application",
    props: true,
    children: [
      {
        path: "",
        components: {
          module: ApplicationModuleEditor,
        },
        name: "application_module",
      },
      {
        path: "interface",
        components: {
          interface: ApplicationInterfaceEditor,
        },
        name: "application_interface",
      },
      {
        path: "deployments",
        components: {
          deployments: ApplicationDeploymentsList,
        },
        name: "application_deployments",
        props: {
          deployments: true,
        },
      },
      {
        path: "deployments/new/:hostId",
        components: {
          deployment: ApplicationDeploymentEditor,
        },
        name: "new_application_deployment",
      },
      {
        path: "deployments/:deploymentId",
        components: {
          deployment: ApplicationDeploymentEditor,
        },
        name: "application_deployment",
        props: {
          deployment: true,
        },
      },
    ],
  },
  { path: "/applications", component: ApplicationsDashboard },
  {
    path: "/credentials",
    component: CredentialStoreDashboard,
    name: "credential_store",
  },
  {
    path: "/gateway-resource-profile",
    component: GatewayResourceProfileEditorContainer,
    name: "gateway-resource-profile",
  },
  {
    path: "/users",
    component: UserManagementContainer,
    name: "users",
    children: [
      {
        path: "",
        component: IdentityServiceUserManagementContainer,
        name: "identity-service-users",
      },
      {
        path: "unverified-email",
        component: UnverifiedEmailUserManagementContainer,
        name: "unverified-email-users",
      },
    ],
  },
  {
    path: "/extended-user-profile",
    component: ExtendedUserProfileContainer,
    name: "extended-user-profile",
  },
  {
    path: "/notices",
    component: NoticesManagementContainer,
    name: "notices",
  },
  {
    path: "/experiment-statistics",
    component: ExperimentStatisticsContainer,
    name: "experiment-statistics",
  },
  {
    path: "/developers",
    component: DevelopersContainer,
    name: "developers",
  },
];
export default routes;
