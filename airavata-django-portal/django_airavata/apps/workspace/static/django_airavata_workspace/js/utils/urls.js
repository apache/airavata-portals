export default {
  editExperiment(experiment) {
    return (
      "/workspace/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/edit"
    );
  },
  navigateToEditExperiment(experiment) {
    window.location.assign(this.editExperiment(experiment));
  },
  experimentsList() {
    return "/workspace/experiments";
  },
  navigateToExperimentsList() {
    window.location.assign(this.experimentsList());
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
    window.location.assign(
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
    window.location.assign(this.createExperiment(appModule));
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
    window.location.assign(this.projectsList());
  },
  viewGroupResourceProfile(groupResourceProfile) {
    return `/admin/group-resource-profiles/${encodeURIComponent(
      groupResourceProfile.group_resource_profile_id,
    )}`;
  },
};
