import { services } from "../index";

const createExperiment = async function ({
  applicationName, // name of the application interface (usually the same as the application module)
  applicationId, // the id of the application module
  applicationInterfaceId, // the id of the application interface
  computeResourceName,
  experimentName,
  experimentInputs,
} = {}) {
  let applicationInterface;
  if (applicationInterfaceId) {
    applicationInterface = await loadApplicationInterfaceById(
      applicationInterfaceId
    );
  } else if (applicationId) {
    applicationInterface = await loadApplicationInterfaceByApplicationModuleId(
      applicationId
    );
  } else if (applicationName) {
    applicationInterface = await loadApplicationInterfaceByName(
      applicationName
    );
  } else {
    throw new Error(
      "Either applicationInterfaceId or applicationId or applicationName is required"
    );
  }
  const applicationModuleId = applicationInterface.applicationModuleId;
  let computeResourceId = null;
  if (computeResourceName) {
    computeResourceId = await loadComputeResourceIdByName(computeResourceName);
  } else {
    throw new Error("computeResourceName is required");
  }
  let groupResourceProfile = await loadGroupResourceProfile(computeResourceId);
  let deployments = await loadApplicationDeployments(
    applicationModuleId,
    groupResourceProfile
  );
  const deployment = deployments.find(
    (d) => d.compute_host_id === computeResourceId
  );
  if (!deployment) {
    throw new Error(
      `Couldn't find a deployment for compute resource ${computeResourceId}`
    );
  }
  let queueDescription = await loadQueue(deployment);
  let workspacePreferences = await loadWorkspacePreferences();
  const projectId = workspacePreferences.most_recent_project_id;

  const experiment = applicationInterface.createExperiment();
  if (experimentName) {
    experiment.experiment_name = experimentName;
  } else {
    experiment.experiment_name = `${
      applicationInterface.application_name
    } on ${new Date().toLocaleString([], {
      dateStyle: "medium",
      timeStyle: "short",
    })}`;
  }
  experiment.project_id = projectId;
  const scheduling =
    experiment.user_configuration_data.computational_resource_scheduling;
  experiment.user_configuration_data.group_resource_profile_id =
    groupResourceProfile.group_resource_profile_id;
  scheduling.resource_host_id = computeResourceId;
  scheduling.total_cpu_count = queueDescription.default_cpu_count;
  scheduling.node_count = queueDescription.default_node_count;
  scheduling.wall_time_limit = queueDescription.default_walltime;
  scheduling.queue_name = queueDescription.queue_name;

  if (experimentInputs) {
    for (let input of experiment.experiment_inputs) {
      if (input.name in experimentInputs) {
        input.value = experimentInputs[input.name];
      }
    }
  }
  return experiment;
};

const loadApplicationInterfaceByName = async function (applicationName) {
  const applicationInterfaces = await services.ApplicationInterfaceService.list();
  const applicationInterface = applicationInterfaces.find(
    (ai) => ai.application_name === applicationName
  );
  if (!applicationInterface) {
    throw new Error(
      `Could not find application interface named ${applicationName}`
    );
  }
  return applicationInterface;
};

const loadApplicationInterfaceById = async function (applicationInterfaceId) {
  return await services.ApplicationInterfaceService.retrieve({
    lookup: applicationInterfaceId,
  });
};

const loadApplicationInterfaceByApplicationModuleId = async function (
  applicationId
) {
  return await services.ApplicationModuleService.getApplicationInterface({
    lookup: applicationId,
  });
};

const loadComputeResourceIdByName = async function (computeResourceName) {
  const computeResourceNames = await services.ComputeResourceService.names();
  for (const computeResourceId in computeResourceNames) {
    if (
      Object.hasOwn(computeResourceNames, computeResourceId) &&
      computeResourceNames[computeResourceId] === computeResourceName
    ) {
      return computeResourceId;
    }
  }
  throw new Error(
    `Could not find compute resource with name ${computeResourceName}`
  );
};

const loadGroupResourceProfile = async function (computeResourceId) {
  const groupResourceProfiles = await services.GroupResourceProfileService.list();
  const groupResourceProfile = groupResourceProfiles.find((grp) => {
    for (let computePref of grp.compute_preferences) {
      if (computePref.compute_resource_id === computeResourceId) {
        return true;
      }
    }
    return false;
  });
  if (!groupResourceProfile) {
    throw new Error(
      `Couldn't find a group resource profile for compute resource ${computeResourceId}`
    );
  }
  return groupResourceProfile;
};

const loadApplicationDeployments = async function (
  applicationModuleId,
  groupResourceProfile
) {
  // appModuleId/groupResourceProfileId are the service's query-param keys, not
  // model fields, so they stay camelCase; the values are snake_case model reads.
  return await services.ApplicationDeploymentService.list({
    appModuleId: applicationModuleId,
    groupResourceProfileId: groupResourceProfile.group_resource_profile_id,
  });
};

const loadQueue = async function (applicationDeployment) {
  const queues = await services.ApplicationDeploymentService.getQueues({
    lookup: applicationDeployment.app_deployment_id,
  });
  const queue = queues.find((q) => q.is_default_queue);
  if (!queue) {
    throw new Error(
      "Couldn't find a default queue for deployment " +
        applicationDeployment.app_deployment_id
    );
  }
  return queue;
};

const loadWorkspacePreferences = async function () {
  return await services.WorkspacePreferencesService.get();
};

const loadExperiment = async function (experimentId) {
  return await services.ExperimentService.retrieve({ lookup: experimentId });
};

const readDataProduct = async function (
  dataProductURI,
  { bodyType = "text" } = {}
) {
  return await fetch(
    `/sdk/download/?data-product-uri=${encodeURIComponent(dataProductURI)}`,
    {
      credentials: "same-origin",
    }
  ).then((r) => {
    if (r.status === 404) {
      return null;
    }
    if (!r.ok) {
      throw new Error(r.statusText);
    }
    return r[bodyType]();
  });
};

const readExperimentDataObject = async function (
  experimentId,
  name,
  dataType,
  { bodyType = "text" } = {}
) {
  if (dataType !== "input" && dataType !== "output") {
    throw new Error("dataType should be one of 'input' or 'output'");
  }
  const experiment = await loadExperiment(experimentId);
  const dataObjectsField =
    dataType === "input" ? "experiment_inputs" : "experiment_outputs";
  const dataObject = experiment[dataObjectsField].find(
    (dataObj) => dataObj.name === name
  );
  if (dataObject.value && dataObject.type.isFileValueType) {
    const downloads = dataObject.value
      .split(",")
      .map((dp) => readDataProduct(dp, { bodyType }));
    if (downloads.length === 1) {
      return await downloads[0];
    } else {
      return await Promise.all(downloads);
    }
  }
  return null;
};

const readInputFile = async function (
  experimentId,
  inputName,
  { bodyType = "text" } = {}
) {
  return await readExperimentDataObject(experimentId, inputName, "input", {
    bodyType,
  });
};

const readOutputFile = async function (
  experimentId,
  outputName,
  { bodyType = "text" } = {}
) {
  return await readExperimentDataObject(experimentId, outputName, "output", {
    bodyType,
  });
};

export { createExperiment, readInputFile, readOutputFile, readDataProduct };

export default {
  createExperiment,
  readInputFile,
  readOutputFile,
  readDataProduct,
};
