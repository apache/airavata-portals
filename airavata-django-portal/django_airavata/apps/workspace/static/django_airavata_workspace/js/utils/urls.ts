interface Experiment {
  experiment_id: string;
}

interface AppModule {
  app_module_id: string;
}

interface Project {
  project_id: string;
}

export default {
  editExperiment(projectId: string, experiment: Experiment): string {
    return (
      "/workspace/projects/" +
      encodeURIComponent(projectId) +
      "/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/edit"
    );
  },
  navigateToEditExperiment(projectId: string, experiment: Experiment): void {
    window.location.assign(this.editExperiment(projectId, experiment));
  },
  experimentsList(projectId: string): string {
    return (
      "/workspace/projects/" + encodeURIComponent(projectId) + "/experiments"
    );
  },
  navigateToExperimentsList(projectId: string): void {
    window.location.assign(this.experimentsList(projectId));
  },
  viewExperiment(
    projectId: string,
    experiment: Experiment,
    { launching = false }: { launching?: boolean } = {}
  ): string {
    return (
      "/workspace/projects/" +
      encodeURIComponent(projectId) +
      "/experiments/" +
      encodeURIComponent(experiment.experiment_id) +
      "/" +
      (launching ? "?launching=true" : "")
    );
  },
  navigateToViewExperiment(
    projectId: string,
    experiment: Experiment,
    { launching = false }: { launching?: boolean } = {}
  ): void {
    window.location.assign(
      this.viewExperiment(projectId, experiment, { launching })
    );
  },
  createExperiment(appModule: AppModule): string {
    return (
      "/workspace/applications/" +
      encodeURIComponent(appModule.app_module_id) +
      "/create_experiment"
    );
  },
  navigateToCreateExperiment(appModule: AppModule): void {
    window.location.assign(this.createExperiment(appModule));
  },
  projectOverview(project: Project): string {
    return (
      "/workspace/projects/" + encodeURIComponent(project.project_id) + "/"
    );
  },
  navigateToProjectOverview(project: Project): void {
    window.location.assign(this.projectOverview(project));
  },
  editProject(project: Project): string {
    return (
      "/workspace/projects/" +
      encodeURIComponent(project.project_id) +
      "/edit"
    );
  },
  projectsList(): string {
    return "/workspace/projects";
  },
  navigateToProjectsList(): void {
    window.location.assign(this.projectsList());
  },
  artifactsList(projectId: string): string {
    return (
      "/workspace/projects/" + encodeURIComponent(projectId) + "/artifacts"
    );
  },
};
