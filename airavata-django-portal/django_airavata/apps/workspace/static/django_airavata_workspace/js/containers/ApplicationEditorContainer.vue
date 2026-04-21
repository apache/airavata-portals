<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">{{ title }}</h1>
        <p v-if="appModuleId" class="text-muted mb-0">{{ appModuleId }}</p>
      </div>
      <div v-if="appModuleId" class="col-auto">
        <a v-if="hasInterface && hasDeployments" :href="launchUrl" class="btn btn-success btn-sm">
          <i class="fa fa-play me-1"></i>Launch Experiment
        </a>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading application...
    </div>

    <template v-if="!loading">
      <!-- Tabs -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
          <a
            class="nav-link"
            :class="{ active: activeTab === 'details' }"
            href="#"
            @click.prevent="activeTab = 'details'"
            >Details</a
          >
        </li>
        <li class="nav-item">
          <a
            class="nav-link"
            :class="{ active: activeTab === 'execution', disabled: !appModuleId }"
            href="#"
            @click.prevent="appModuleId && (activeTab = 'execution')"
            >Execution</a
          >
        </li>
      </ul>

      <!-- DETAILS TAB -->
      <div v-show="activeTab === 'details'" class="card">
        <div class="card-body">
          <div class="mb-3">
            <label class="form-label">Application Name <span class="text-danger">*</span></label>
            <input
              v-model="appModule.app_module_name"
              type="text"
              class="form-control"
              :disabled="readonly"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Version</label>
            <input
              v-model="appModule.app_module_version"
              type="text"
              class="form-control"
              :disabled="readonly"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Description</label>
            <textarea
              v-model="appModule.app_module_description"
              class="form-control"
              rows="3"
              :disabled="readonly"
            ></textarea>
          </div>

          <template v-if="appInterface">
            <div class="d-flex align-items-center mt-4 mb-2">
              <h6 class="mb-0 me-auto">Input Fields</h6>
              <button class="btn btn-sm btn-outline-primary" :disabled="readonly" @click="addInput">
                <i class="fa fa-plus me-1"></i>Add Input
              </button>
            </div>
            <table
              v-if="appInterface.application_inputs && appInterface.application_inputs.length > 0"
              class="table table-sm table-borderless align-middle"
            >
              <thead>
                <tr>
                  <th style="width: 25%">Name</th>
                  <th style="width: 15%">Type</th>
                  <th style="width: 20%">Default Value</th>
                  <th
                    style="width: 20%"
                    :title="'Flag or prefix to pass to the bash script. Leave empty to NOT pass this field as a CLI argument.'"
                  >
                    CLI Argument
                  </th>
                  <th style="width: 10%" class="text-center">Required</th>
                  <th style="width: 10%" class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(input, i) in appInterface.application_inputs" :key="input.key || i">
                  <td>
                    <input
                      v-model="input.name"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                    />
                  </td>
                  <td>
                    <select
                      v-model="input.type"
                      class="form-select form-select-sm"
                      :disabled="readonly"
                    >
                      <option v-for="dt in inputDataTypes" :key="dt.name" :value="dt">
                        {{ dt.name }}
                      </option>
                    </select>
                  </td>
                  <td>
                    <input
                      v-model="input.value"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                    />
                  </td>
                  <td>
                    <input
                      v-model="input.application_argument"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                      placeholder="e.g., --input or -o (leave empty to skip)"
                      title="Flag or prefix to pass to the bash script. Leave empty to NOT pass this field as a CLI argument."
                    />
                  </td>
                  <td class="text-center">
                    <input
                      v-model="input.is_required"
                      type="checkbox"
                      class="form-check-input"
                      :disabled="readonly"
                    />
                  </td>
                  <td class="text-end">
                    <button
                      class="btn btn-sm btn-outline-danger"
                      :disabled="readonly"
                      title="Remove"
                      @click="removeInput(i)"
                    >
                      <i class="fa fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="text-muted small mb-0">No input fields defined.</p>

            <div class="d-flex align-items-center mt-4 mb-2">
              <h6 class="mb-0 me-auto">Output Fields</h6>
              <button
                class="btn btn-sm btn-outline-primary"
                :disabled="readonly"
                @click="addOutput"
              >
                <i class="fa fa-plus me-1"></i>Add Output
              </button>
            </div>
            <table
              v-if="appInterface.application_outputs && appInterface.application_outputs.length > 0"
              class="table table-sm table-borderless align-middle"
            >
              <thead>
                <tr>
                  <th style="width: 25%">Name</th>
                  <th style="width: 15%">Type</th>
                  <th style="width: 20%">Value</th>
                  <th
                    style="width: 20%"
                    :title="'Flag or prefix to pass to the bash script. Leave empty to NOT pass this field as a CLI argument.'"
                  >
                    CLI Argument
                  </th>
                  <th style="width: 10%" class="text-center">Required</th>
                  <th style="width: 10%" class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(output, i) in appInterface.application_outputs" :key="output.key || i">
                  <td>
                    <input
                      v-model="output.name"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                    />
                  </td>
                  <td>
                    <select
                      v-model="output.type"
                      class="form-select form-select-sm"
                      :disabled="readonly"
                    >
                      <option v-for="dt in outputDataTypes" :key="dt.name" :value="dt">
                        {{ dt.name }}
                      </option>
                    </select>
                  </td>
                  <td>
                    <input
                      v-model="output.value"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                    />
                  </td>
                  <td>
                    <input
                      v-model="output.application_argument"
                      type="text"
                      class="form-control form-control-sm"
                      :disabled="readonly"
                      placeholder="e.g., --input or -o (leave empty to skip)"
                      title="Flag or prefix to pass to the bash script. Leave empty to NOT pass this field as a CLI argument."
                    />
                  </td>
                  <td class="text-center">
                    <input
                      v-model="output.is_required"
                      type="checkbox"
                      class="form-check-input"
                      :disabled="readonly"
                    />
                  </td>
                  <td class="text-end">
                    <button
                      class="btn btn-sm btn-outline-danger"
                      :disabled="readonly"
                      title="Remove"
                      @click="removeOutput(i)"
                    >
                      <i class="fa fa-trash"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="text-muted small mb-0">No output fields defined.</p>

            <h5 class="mt-4">Options</h5>
            <div class="card mb-3">
              <div class="card-body">
                <div class="form-check mb-3">
                  <input
                    id="archive-wd"
                    v-model="appInterface.archive_working_directory"
                    class="form-check-input"
                    type="checkbox"
                    :disabled="readonly"
                  />
                  <label class="form-check-label fw-bold" for="archive-wd"
                    >Archive Working Directory</label
                  >
                  <p class="text-muted small mb-0">
                    After the experiment runs, compress and save the entire working directory as an
                    output. Useful when you want access to all files produced during execution, not
                    just the declared outputs.
                  </p>
                </div>
                <div class="form-check">
                  <input
                    id="show-queue"
                    v-model="appInterface.show_queue_settings"
                    class="form-check-input"
                    type="checkbox"
                    :disabled="readonly"
                  />
                  <label class="form-check-label fw-bold" for="show-queue"
                    >Show Queue Settings</label
                  >
                  <p class="text-muted small mb-0">
                    Display HPC resource configuration (queue, node count, CPU count, walltime,
                    memory) on the experiment launch page. Enable when users need to override
                    defaults per experiment. Disable for fire-and-forget apps that should always run
                    with deployment defaults.
                  </p>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- EXECUTION TAB -->
      <div v-show="activeTab === 'execution'">
        <!-- Existing deployments -->
        <div class="card mb-3">
          <div class="card-body">
            <div v-if="appDeployments.length === 0" class="text-muted text-center py-3">
              No deployments configured. Add one below.
            </div>
            <table v-if="appDeployments.length > 0" class="table table-hover mb-0">
              <thead>
                <tr>
                  <th>Compute Resource</th>
                  <th>Executable Path</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="dep in appDeployments"
                  :key="dep.app_deployment_id || dep.compute_host_id"
                >
                  <td>{{ getComputeResourceName(dep.compute_host_id) }}</td>
                  <td>
                    <code>{{ dep.executable_path || "-" }}</code>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-link p-0 me-2" @click="editDeployment(dep)">
                      <i class="fa fa-edit"></i> Edit
                    </button>
                    <button
                      class="btn btn-sm btn-link text-danger p-0"
                      :disabled="readonly"
                      @click="confirmDeleteDeployment(dep)"
                    >
                      <i class="fa fa-trash"></i> Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Add new deployment -->
        <div v-if="!editingDeployment" class="card mb-3">
          <div class="card-header">Add Deployment</div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Compute Resource</label>
              <select v-model="newDeploymentComputeHostId" class="form-select" :disabled="readonly">
                <option :value="null">Select a compute resource...</option>
                <option
                  v-for="cr in availableComputeResources"
                  :key="cr.host_id"
                  :value="cr.host_id"
                >
                  {{ cr.host }}
                </option>
              </select>
            </div>
            <button
              class="btn btn-primary btn-sm"
              :disabled="!newDeploymentComputeHostId || readonly"
              @click="addDeployment"
            >
              <i class="fa fa-plus me-1"></i>Add Deployment
            </button>
          </div>
        </div>

        <!-- Edit deployment detail -->
        <div v-if="editingDeployment" class="card mb-3">
          <div class="card-header d-flex align-items-center">
            <span class="me-auto">{{
              getComputeResourceName(editingDeployment.compute_host_id)
            }}</span>
            <button class="btn btn-sm btn-link p-0" @click="editingDeployment = null">Close</button>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Executable Path <span class="text-danger">*</span></label>
              <input
                v-model="editingDeployment.executable_path"
                type="text"
                class="form-control"
                :disabled="readonly"
                placeholder="/usr/local/bin/myapp or a bash script path"
              />
              <div class="form-text">
                Path to the executable on the compute resource. For a bash script, use the path
                where the script will be located (e.g., <code>/home/user/run.sh</code>).
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea
                v-model="editingDeployment.app_deployment_description"
                class="form-control"
                rows="2"
                :disabled="readonly"
              ></textarea>
            </div>

            <h6 class="mt-3 mb-2">Pre Job Commands</h6>
            <p class="text-muted" style="font-size: 0.8125rem">
              Commands to run before the application executable (e.g., module loads, environment
              setup). Paste a bash script here line by line.
            </p>
            <div
              v-for="(cmd, idx) in editingDeployment.pre_job_commands"
              :key="'pre-' + idx"
              class="input-group input-group-sm mb-1"
            >
              <input
                v-model="cmd.command"
                type="text"
                class="form-control font-monospace"
                :disabled="readonly"
              />
              <button
                class="btn btn-outline-danger"
                :disabled="readonly"
                @click="editingDeployment.pre_job_commands.splice(idx, 1)"
              >
                <i class="fa fa-times"></i>
              </button>
            </div>
            <button
              class="btn btn-outline-secondary btn-sm mt-1"
              :disabled="readonly"
              @click="addPreJobCommand"
            >
              <i class="fa fa-plus me-1"></i>Add Command
            </button>

            <h6 class="mt-3 mb-2">Post Job Commands</h6>
            <div
              v-for="(cmd, idx) in editingDeployment.post_job_commands"
              :key="'post-' + idx"
              class="input-group input-group-sm mb-1"
            >
              <input
                v-model="cmd.command"
                type="text"
                class="form-control font-monospace"
                :disabled="readonly"
              />
              <button
                class="btn btn-outline-danger"
                :disabled="readonly"
                @click="editingDeployment.post_job_commands.splice(idx, 1)"
              >
                <i class="fa fa-times"></i>
              </button>
            </div>
            <button
              class="btn btn-outline-secondary btn-sm mt-1"
              :disabled="readonly"
              @click="addPostJobCommand"
            >
              <i class="fa fa-plus me-1"></i>Add Command
            </button>

            <h6 class="mt-3 mb-2">Module Load Commands</h6>
            <div
              v-for="(cmd, idx) in editingDeployment.module_load_cmds"
              :key="'mod-' + idx"
              class="input-group input-group-sm mb-1"
            >
              <input
                v-model="cmd.command"
                type="text"
                class="form-control font-monospace"
                :disabled="readonly"
              />
              <button
                class="btn btn-outline-danger"
                :disabled="readonly"
                @click="editingDeployment.module_load_cmds.splice(idx, 1)"
              >
                <i class="fa fa-times"></i>
              </button>
            </div>
            <button
              class="btn btn-outline-secondary btn-sm mt-1"
              :disabled="readonly"
              @click="addModuleLoadCommand"
            >
              <i class="fa fa-plus me-1"></i>Add Command
            </button>

            <h6 class="mt-3 mb-2">Environment Variables</h6>
            <div
              v-for="(env, idx) in editingDeployment.set_environment"
              :key="'env-' + idx"
              class="input-group input-group-sm mb-1"
            >
              <input
                v-model="env.name"
                type="text"
                class="form-control"
                placeholder="NAME"
                :disabled="readonly"
                style="max-width: 200px"
              />
              <span class="input-group-text">=</span>
              <input
                v-model="env.value"
                type="text"
                class="form-control"
                placeholder="value"
                :disabled="readonly"
              />
              <button
                class="btn btn-outline-danger"
                :disabled="readonly"
                @click="editingDeployment.set_environment.splice(idx, 1)"
              >
                <i class="fa fa-times"></i>
              </button>
            </div>
            <button
              class="btn btn-outline-secondary btn-sm mt-1"
              :disabled="readonly"
              @click="addEnvVar"
            >
              <i class="fa fa-plus me-1"></i>Add Variable
            </button>

            <hr />
            <h6 class="mb-2">Queue Defaults</h6>
            <div class="row g-2">
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default Queue</label>
                <select
                  v-model="editingDeployment.default_queue_name"
                  class="form-select form-select-sm"
                  :disabled="readonly"
                >
                  <option :value="null">Select queue...</option>
                  <option
                    v-for="q in editingDeploymentQueues"
                    :key="q.queue_name"
                    :value="q.queue_name"
                  >
                    {{ q.queue_name }}
                  </option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default Node Count</label>
                <input
                  v-model.number="editingDeployment.default_node_count"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !editingDeployment.default_queue_name"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default CPU Count</label>
                <input
                  v-model.number="editingDeployment.default_cpu_count"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !editingDeployment.default_queue_name"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default Walltime (min)</label>
                <input
                  v-model.number="editingDeployment.default_walltime"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !editingDeployment.default_queue_name"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="d-flex gap-2 mt-3 mb-4">
        <button class="btn btn-primary btn-sm" :disabled="saving || readonly" @click="saveAll">
          <i v-if="saving" class="fa fa-spinner fa-spin me-1"></i>Save
        </button>
        <button class="btn btn-secondary btn-sm" @click="cancel">Cancel</button>
        <button
          v-if="appModuleId"
          class="btn btn-danger btn-sm ms-auto"
          :disabled="readonly"
          @click="confirmDeleteApp"
        >
          <i class="fa fa-trash me-1"></i>Delete Application
        </button>
      </div>

      <!-- Save feedback -->
      <div
        v-if="saveMessage"
        class="alert"
        :class="saveMessageClass"
        role="alert"
        style="font-size: 0.875rem"
      >
        {{ saveMessage }}
      </div>
      <div v-if="saveError" class="alert alert-danger" role="alert" style="font-size: 0.875rem">
        {{ saveError }}
      </div>
    </template>

    <!-- Delete deployment confirmation modal -->
    <div
      v-if="deleteDeploymentTarget"
      class="modal d-block"
      tabindex="-1"
      style="background: rgba(0, 0, 0, 0.4)"
    >
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Deployment</h5>
            <button type="button" class="btn-close" @click="deleteDeploymentTarget = null"></button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to delete the deployment for
              <strong>{{ getComputeResourceName(deleteDeploymentTarget.compute_host_id) }}</strong
              >?
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-sm btn-secondary" @click="deleteDeploymentTarget = null">
              Cancel
            </button>
            <button class="btn btn-sm btn-danger" @click="deleteDeployment">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete application confirmation modal -->
    <div
      v-if="showDeleteAppModal"
      class="modal d-block"
      tabindex="-1"
      style="background: rgba(0, 0, 0, 0.4)"
    >
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Application</h5>
            <button type="button" class="btn-close" @click="showDeleteAppModal = false"></button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to delete <strong>{{ appModule.app_module_name }}</strong
              >?
            </p>
            <p class="text-muted mb-0" style="font-size: 0.8125rem">
              This will also remove its interface and all deployments.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-sm btn-secondary" @click="showDeleteAppModal = false">
              Cancel
            </button>
            <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteApp">
              <i v-if="deleting" class="fa fa-spinner fa-spin me-1"></i>Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { models, services, session } from "django-airavata-api";

export default {
  name: "ApplicationEditorContainer",
  props: {
    appModuleId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
      saving: false,
      deleting: false,
      activeTab: "details",
      appModule: new models.ApplicationModule({ user_has_write_access: true }),
      appInterface: null,
      appDeployments: [],
      computeResourceNames: {},
      groupResourceProfiles: [],
      editingDeployment: null,
      editingDeploymentComputeResource: null,
      newDeploymentComputeHostId: null,
      deleteDeploymentTarget: null,
      showDeleteAppModal: false,
      saveMessage: null,
      saveMessageClass: "alert-success",
      saveError: null,
    };
  },
  computed: {
    isGatewayAdmin() {
      return session.Session.is_gateway_admin;
    },
    title() {
      if (this.appModuleId && this.appModule.app_module_name) {
        return this.appModule.app_module_name;
      }
      return "Create Application";
    },
    readonly() {
      return this.appModule && this.appModule.user_has_write_access === false;
    },
    hasInterface() {
      return this.appInterface && this.appInterface.application_interface_id;
    },
    hasDeployments() {
      return this.appDeployments.length > 0;
    },
    launchUrl() {
      return "/workspace/applications/" + this.appModuleId + "/create_experiment";
    },
    inputDataTypes() {
      return models.InputDataObjectType.VALID_DATA_TYPES;
    },
    outputDataTypes() {
      return models.DataType.values;
    },
    availableComputeResources() {
      // Build list of compute resources from group resource profiles
      const grpCompResources = {};
      for (const grp of this.groupResourceProfiles) {
        if (grp.compute_preferences) {
          for (const pref of grp.compute_preferences) {
            grpCompResources[pref.compute_resource_id] = true;
          }
        }
      }
      const result = [];
      const existingHostIds = this.appDeployments.map((d) => d.compute_host_id);
      const hasGrpRestriction = Object.keys(grpCompResources).length > 0;
      for (const [hostId, name] of Object.entries(this.computeResourceNames || {})) {
        if (existingHostIds.includes(hostId)) continue;
        // If the user has group resource profiles, restrict to those compute
        // resources; otherwise fall back to showing all compute resources.
        if (hasGrpRestriction && !grpCompResources[hostId]) continue;
        result.push({ host_id: hostId, host: name });
      }
      return result.sort((a, b) => a.host.localeCompare(b.host));
    },
    editingDeploymentQueues() {
      if (
        this.editingDeploymentComputeResource &&
        this.editingDeploymentComputeResource.batch_queues
      ) {
        return this.editingDeploymentComputeResource.batch_queues;
      }
      return [];
    },
  },
  created() {
    if (this.appModuleId) {
      this.loading = true;
      Promise.all([
        this.loadModule(),
        this.loadInterface(),
        this.loadDeployments(),
        this.loadComputeResourceNames(),
        this.loadGroupResourceProfiles(),
      ]).finally(() => {
        this.loading = false;
      });
    } else {
      Promise.all([this.loadComputeResourceNames(), this.loadGroupResourceProfiles()]);
      // Create a default interface with stdout/stderr
      const iface = new models.ApplicationInterfaceDefinition({
        user_has_write_access: true,
      });
      iface.addStandardOutAndStandardErrorOutputs();
      this.appInterface = iface;
    }
  },
  methods: {
    // --- Data loading ---
    loadModule() {
      return services.ApplicationModuleService.retrieve({
        lookup: this.appModuleId,
      }).then((m) => (this.appModule = m));
    },
    loadInterface() {
      return services.ApplicationModuleService.getApplicationInterface(
        { lookup: this.appModuleId },
        { ignoreErrors: true },
      )
        .then((iface) => {
          this.appInterface = iface;
        })
        .catch((error) => {
          if (error.details && error.details.status === 404) {
            const iface = new models.ApplicationInterfaceDefinition({
              user_has_write_access: true,
            });
            iface.addStandardOutAndStandardErrorOutputs();
            this.appInterface = iface;
          }
        });
    },
    loadDeployments() {
      return services.ApplicationModuleService.getApplicationDeployments({
        lookup: this.appModuleId,
      }).then((deps) => (this.appDeployments = deps));
    },
    loadComputeResourceNames() {
      return services.ComputeResourceService.names().then(
        (names) => (this.computeResourceNames = names),
      );
    },
    loadGroupResourceProfiles() {
      return services.ProjectResourceProfileService.list().then(
        (profiles) => (this.groupResourceProfiles = profiles),
      );
    },
    getComputeResourceName(hostId) {
      if (this.computeResourceNames && hostId in this.computeResourceNames) {
        return this.computeResourceNames[hostId];
      }
      return hostId ? hostId.substring(0, 20) + "..." : "";
    },

    // --- Interface editing ---
    addInput() {
      const input = new models.InputDataObjectType();
      // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
      if (input.application_argument == null) {
        input.application_argument = "";
      }
      this.appInterface.application_inputs.push(input);
    },
    removeInput(idx) {
      this.appInterface.application_inputs.splice(idx, 1);
    },
    addOutput() {
      const output = new models.OutputDataObjectType();
      // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
      if (output.application_argument == null) {
        output.application_argument = "";
      }
      this.appInterface.application_outputs.push(output);
    },
    removeOutput(idx) {
      this.appInterface.application_outputs.splice(idx, 1);
    },

    // --- Deployment editing ---
    editDeployment(dep) {
      this.editingDeployment = dep;
      this.editingDeploymentComputeResource = null;
      if (dep.compute_host_id) {
        services.ComputeResourceService.retrieve({
          lookup: dep.compute_host_id,
        }).then((cr) => (this.editingDeploymentComputeResource = cr));
      }
    },
    addDeployment() {
      if (!this.newDeploymentComputeHostId) return;
      const dep = new models.ApplicationDeploymentDescription({
        user_has_write_access: true,
      });
      dep.app_module_id = this.appModuleId;
      dep.compute_host_id = this.newDeploymentComputeHostId;
      this.appDeployments.push(dep);
      this.newDeploymentComputeHostId = null;
      this.editDeployment(dep);
    },
    addPreJobCommand() {
      if (!this.editingDeployment.pre_job_commands) {
        this.editingDeployment.pre_job_commands = [];
      }
      this.editingDeployment.pre_job_commands.push(new models.CommandObject({ command: "" }));
    },
    addPostJobCommand() {
      if (!this.editingDeployment.post_job_commands) {
        this.editingDeployment.post_job_commands = [];
      }
      this.editingDeployment.post_job_commands.push(new models.CommandObject({ command: "" }));
    },
    addModuleLoadCommand() {
      if (!this.editingDeployment.module_load_cmds) {
        this.editingDeployment.module_load_cmds = [];
      }
      this.editingDeployment.module_load_cmds.push(new models.CommandObject({ command: "" }));
    },
    addEnvVar() {
      if (!this.editingDeployment.set_environment) {
        this.editingDeployment.set_environment = [];
      }
      this.editingDeployment.set_environment.push(new models.SetEnvPaths({ name: "", value: "" }));
    },
    confirmDeleteDeployment(dep) {
      this.deleteDeploymentTarget = dep;
    },
    deleteDeployment() {
      const dep = this.deleteDeploymentTarget;
      this.deleteDeploymentTarget = null;
      if (dep.app_deployment_id) {
        services.ApplicationDeploymentService.delete({
          lookup: dep.app_deployment_id,
        }).then(() => {
          this.appDeployments = this.appDeployments.filter(
            (d) => d.compute_host_id !== dep.compute_host_id,
          );
          if (
            this.editingDeployment &&
            this.editingDeployment.compute_host_id === dep.compute_host_id
          ) {
            this.editingDeployment = null;
          }
        });
      } else {
        this.appDeployments = this.appDeployments.filter(
          (d) => d.compute_host_id !== dep.compute_host_id,
        );
        if (
          this.editingDeployment &&
          this.editingDeployment.compute_host_id === dep.compute_host_id
        ) {
          this.editingDeployment = null;
        }
      }
    },

    // --- Save all ---
    async saveAll() {
      this.saving = true;
      this.saveMessage = null;
      this.saveError = null;

      try {
        // 1. Save module
        let moduleId = this.appModuleId;
        if (moduleId) {
          await services.ApplicationModuleService.update({
            lookup: moduleId,
            data: this.appModule,
          });
        } else {
          const created = await services.ApplicationModuleService.create({
            data: this.appModule,
          });
          this.appModule = created;
          moduleId = created.app_module_id;
        }

        // 2. Save interface — ALWAYS ensure an interface exists for the
        // module with at least the auto-generated stdout/stderr outputs, so
        // experiment launch can find an interface for the module id.
        if (!this.appInterface) {
          const iface = new models.ApplicationInterfaceDefinition({
            user_has_write_access: true,
          });
          iface.addStandardOutAndStandardErrorOutputs();
          this.appInterface = iface;
        } else {
          // If somehow the interface has no outputs at all, inject the
          // standard stdout/stderr so the experiment launch has what it needs.
          if (
            !this.appInterface.application_outputs ||
            this.appInterface.application_outputs.length === 0
          ) {
            this.appInterface.addStandardOutAndStandardErrorOutputs();
          }
        }
        this.appInterface.application_name = this.appModule.app_module_name;
        this.appInterface.application_modules = [moduleId];
        if (this.appInterface.application_interface_id) {
          this.appInterface = await services.ApplicationInterfaceService.update({
            lookup: this.appInterface.application_interface_id,
            data: this.appInterface,
          });
        } else {
          this.appInterface = await services.ApplicationInterfaceService.create({
            data: this.appInterface,
          });
        }

        // 3. Save deployments
        for (const dep of this.appDeployments) {
          dep.app_module_id = moduleId;
          if (dep.app_deployment_id) {
            await services.ApplicationDeploymentService.update({
              lookup: dep.app_deployment_id,
              data: dep,
            });
          } else {
            const created = await services.ApplicationDeploymentService.create({
              data: dep,
            });
            // Update in place
            Object.assign(dep, created);
          }
        }

        this.saveMessage = "Application saved successfully.";
        this.saveMessageClass = "alert-success";

        // If this was a new application, navigate to the edit URL
        if (!this.appModuleId && moduleId) {
          window.location.href = "/workspace/applications/" + moduleId + "/";
        }
      } catch (error) {
        const detail = error.details
          ? error.details.message || JSON.stringify(error.details.response || error.details)
          : error.message || "An error occurred while saving.";
        this.saveError = detail;
      } finally {
        this.saving = false;
      }
    },

    // --- Delete application ---
    confirmDeleteApp() {
      this.showDeleteAppModal = true;
    },
    async deleteApp() {
      this.deleting = true;
      try {
        // 1. Delete deployments in parallel. Guard against entries that
        //    exist only locally (no server-side id yet) and against any
        //    entries that somehow carry a differently-named id field, so a
        //    missing id never bubbles up as `Error: id` inside Promise.all.
        const deploymentDeletes = (this.appDeployments || [])
          .map((dep) => {
            if (!dep) return null;
            const id = dep.app_deployment_id || dep.application_deployment_id || null;
            if (!id) return null;
            return services.ApplicationDeploymentService.delete({ lookup: id });
          })
          .filter((p) => p !== null);
        await Promise.all(deploymentDeletes);

        // 2. Delete interface (if one was ever persisted).
        const interfaceId =
          this.appInterface &&
          (this.appInterface.application_interface_id ||
            this.appInterface.applicationInterfaceId ||
            null);
        if (interfaceId) {
          await services.ApplicationInterfaceService.delete({
            lookup: interfaceId,
          });
        }

        // 3. Delete module.
        if (this.appModuleId) {
          await services.ApplicationModuleService.delete({
            lookup: this.appModuleId,
          });
        }
        window.location.href = "/workspace/applications";
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Failed to delete application", error);
        this.saveError =
          "Failed to delete application: " +
          (error && (error.message || error.details || "unknown error"));
        this.showDeleteAppModal = false;
      } finally {
        this.deleting = false;
      }
    },

    cancel() {
      window.location.href = "/workspace/applications";
    },
  },
};
</script>
