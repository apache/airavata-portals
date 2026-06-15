import { utils } from "django-airavata-common-ui";

export default {
  editExperiment(experiment) {
    return (
      "/workspace/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/edit"
    );
  },
  navigateToEditExperiment(experiment) {
    utils.navigateTo(this.editExperiment(experiment));
  },
  experimentsList() {
    return "/workspace/experiments";
  },
  navigateToExperimentsList() {
    utils.navigateTo(this.experimentsList());
  },
  viewExperiment(experiment, { launching = false } = {}) {
    return (
      "/workspace/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/" +
      (launching ? "?launching=true" : "")
    );
  },
  navigateToViewExperiment(experiment, { launching = false } = {}) {
    utils.navigateTo(
      this.viewExperiment(experiment, { launching: launching }),
    );
  },
  createExperiment(appModule) {
    return (
      "/workspace/applications/" +
      encodeURIComponent(appModule.app_module_id) +
      "/create_experiment"
    );
  },
  navigateToCreateExperiment(appModule) {
    utils.navigateTo(this.createExperiment(appModule));
  },
  editProject(project) {
    return (
      "/workspace/projects/" + encodeURIComponent(project.project_id) + "/"
    );
  },
  projectsList() {
    return "/workspace/projects";
  },
  navigateToProjectsList() {
    utils.navigateTo(this.projectsList());
  },
  viewGroupResourceProfile(groupResourceProfile) {
    return `/admin/group-resource-profiles/${encodeURIComponent(
      groupResourceProfile.group_resource_profile_id,
    )}`;
  },
};
