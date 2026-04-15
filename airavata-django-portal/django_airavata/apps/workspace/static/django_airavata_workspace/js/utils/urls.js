export default {
  editExperiment(projectId, experiment) {
    return (
      "/workspace/projects/" +
      encodeURIComponent(projectId) +
      "/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/edit"
    );
  },
  navigateToEditExperiment(projectId, experiment) {
    window.location.assign(this.editExperiment(projectId, experiment));
  },
  experimentsList(projectId) {
    return "/workspace/projects/" + encodeURIComponent(projectId) + "/experiments";
  },
  navigateToExperimentsList(projectId) {
    window.location.assign(this.experimentsList(projectId));
  },
  viewExperiment(projectId, experiment, { launching = false } = {}) {
    return (
      "/workspace/projects/" +
      encodeURIComponent(projectId) +
      "/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/" +
      (launching ? "?launching=true" : "")
    );
  },
  navigateToViewExperiment(projectId, experiment, { launching = false } = {}) {
    window.location.assign(
      this.viewExperiment(projectId, experiment, { launching })
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
  projectOverview(project) {
    return "/workspace/projects/" + encodeURIComponent(project.project_id) + "/";
  },
  navigateToProjectOverview(project) {
    window.location.assign(this.projectOverview(project));
  },
  editProject(project) {
    return "/workspace/projects/" + encodeURIComponent(project.project_id) + "/edit";
  },
  projectsList() {
    return "/workspace/projects";
  },
  navigateToProjectsList() {
    window.location.assign(this.projectsList());
  },
  artifactsList(projectId) {
    return "/workspace/projects/" + encodeURIComponent(projectId) + "/artifacts";
  },
};
