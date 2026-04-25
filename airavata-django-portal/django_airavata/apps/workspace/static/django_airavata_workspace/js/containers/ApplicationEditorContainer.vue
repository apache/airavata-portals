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
              v-model="(appModule as Record<string, unknown>).app_module_name"
              type="text"
              class="form-control"
              :disabled="readonly"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Version</label>
            <input
              v-model="(appModule as Record<string, unknown>).app_module_version"
              type="text"
              class="form-control"
              :disabled="readonly"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">Description</label>
            <textarea
              v-model="(appModule as Record<string, string>).app_module_description"
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
              v-if="(appInterface as Record<string, unknown>).application_inputs && ((appInterface as Record<string, unknown>).application_inputs as unknown[]).length > 0"
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
                <tr v-for="(input, i) in ((appInterface as Record<string, unknown>).application_inputs as Array<Record<string, unknown>>)" :key="inputKey(input, i)">
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
                      <option v-for="dt in inputDataTypes" :key="(dt as Record<string, unknown>).name as string" :value="dt">
                        {{ (dt as Record<string, unknown>).name }}
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
              v-if="(appInterface as Record<string, unknown>).application_outputs && ((appInterface as Record<string, unknown>).application_outputs as unknown[]).length > 0"
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
                <tr v-for="(output, i) in ((appInterface as Record<string, unknown>).application_outputs as Array<Record<string, unknown>>)" :key="inputKey(output, i)">
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
                      <option v-for="dt in outputDataTypes" :key="(dt as Record<string, unknown>).name as string" :value="dt">
                        {{ (dt as Record<string, unknown>).name }}
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
                    v-model="(appInterface as Record<string, unknown>).archive_working_directory"
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
                    v-model="(appInterface as Record<string, unknown>).show_queue_settings"
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
                  :key="(dep as Record<string, unknown>).app_deployment_id as string || (dep as Record<string, unknown>).compute_host_id as string"
                >
                  <td>{{ getComputeResourceName((dep as Record<string, unknown>).compute_host_id as string) }}</td>
                  <td>
                    <code>{{ (dep as Record<string, unknown>).executable_path || "-" }}</code>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-link p-0 me-2" @click="editDeployment(dep as Record<string, unknown>)">
                      <i class="fa fa-edit"></i> Edit
                    </button>
                    <button
                      class="btn btn-sm btn-link text-danger p-0"
                      :disabled="readonly"
                      @click="confirmDeleteDeployment(dep as Record<string, unknown>)"
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
              getComputeResourceName((editingDeployment as Record<string, unknown>).compute_host_id as string)
            }}</span>
            <button class="btn btn-sm btn-link p-0" @click="editingDeployment = null">Close</button>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Executable Path <span class="text-danger">*</span></label>
              <input
                v-model="(editingDeployment as Record<string, unknown>).executable_path"
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
                v-model="(editingDeployment as Record<string, string>).app_deployment_description"
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
              v-for="(cmd, idx) in ((editingDeployment as Record<string, unknown>).pre_job_commands as Array<Record<string, unknown>>)"
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
                @click="((editingDeployment as Record<string, unknown>).pre_job_commands as Array<unknown>).splice(idx, 1)"
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
              v-for="(cmd, idx) in ((editingDeployment as Record<string, unknown>).post_job_commands as Array<Record<string, unknown>>)"
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
                @click="((editingDeployment as Record<string, unknown>).post_job_commands as Array<unknown>).splice(idx, 1)"
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
              v-for="(cmd, idx) in ((editingDeployment as Record<string, unknown>).module_load_cmds as Array<Record<string, unknown>>)"
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
                @click="((editingDeployment as Record<string, unknown>).module_load_cmds as Array<unknown>).splice(idx, 1)"
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
              v-for="(env, idx) in ((editingDeployment as Record<string, unknown>).set_environment as Array<Record<string, unknown>>)"
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
                @click="((editingDeployment as Record<string, unknown>).set_environment as Array<unknown>).splice(idx, 1)"
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
                  v-model="(editingDeployment as Record<string, unknown>).default_queue_name"
                  class="form-select form-select-sm"
                  :disabled="readonly"
                >
                  <option :value="null">Select queue...</option>
                  <option
                    v-for="q in editingDeploymentQueues"
                    :key="(q as Record<string, unknown>).queue_name as string"
                    :value="(q as Record<string, unknown>).queue_name"
                  >
                    {{ (q as Record<string, unknown>).queue_name }}
                  </option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default Node Count</label>
                <input
                  v-model.number="(editingDeployment as Record<string, unknown>).default_node_count"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !(editingDeployment as Record<string, unknown>).default_queue_name"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default CPU Count</label>
                <input
                  v-model.number="(editingDeployment as Record<string, unknown>).default_cpu_count"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !(editingDeployment as Record<string, unknown>).default_queue_name"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label form-label-sm">Default Walltime (min)</label>
                <input
                  v-model.number="(editingDeployment as Record<string, unknown>).default_walltime"
                  type="number"
                  class="form-control form-control-sm"
                  min="0"
                  :disabled="readonly || !(editingDeployment as Record<string, unknown>).default_queue_name"
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
              <strong>{{ getComputeResourceName((deleteDeploymentTarget as Record<string, unknown>).compute_host_id as string) }}</strong
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
              Are you sure you want to delete <strong>{{ (appModule as Record<string, unknown>).app_module_name }}</strong
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

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { models, services } from "django-airavata-api";

const props = withDefaults(defineProps<{
  appModuleId?: string | null;
}>(), {
  appModuleId: null,
});

const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);
const activeTab = ref("details");
const appModule = ref<unknown>(new models.ApplicationModule({ user_has_write_access: true }));
const appInterface = ref<unknown>(null);
const appDeployments = ref<unknown[]>([]);
const computeResourceNames = ref<Record<string, string>>({});
const groupResourceProfiles = ref<unknown[]>([]);
const editingDeployment = ref<unknown>(null);
const editingDeploymentComputeResource = ref<unknown>(null);
const newDeploymentComputeHostId = ref<string | null>(null);
const deleteDeploymentTarget = ref<unknown>(null);
const showDeleteAppModal = ref(false);
const saveMessage = ref<string | null>(null);
const saveMessageClass = ref("alert-success");
const saveError = ref<string | null>(null);

const title = computed(() => {
  const mod = appModule.value as Record<string, unknown>;
  if (props.appModuleId && mod.app_module_name) {
    return mod.app_module_name as string;
  }
  return "Create Application";
});

const readonly = computed(() => {
  const mod = appModule.value as Record<string, unknown>;
  return mod && mod.user_has_write_access === false;
});

const hasInterface = computed(() => {
  const iface = appInterface.value as Record<string, unknown> | null;
  return iface && iface.application_interface_id;
});

const hasDeployments = computed(() => appDeployments.value.length > 0);

const launchUrl = computed(() => "/workspace/launch");

const inputDataTypes = computed(() => (models.InputDataObjectType as unknown as Record<string, unknown>).VALID_DATA_TYPES as unknown[]);

const outputDataTypes = computed(() => (models.DataType as unknown as Record<string, unknown>).values as unknown[]);

const availableComputeResources = computed(() => {
  const grpCompResources: Record<string, boolean> = {};
  for (const grp of groupResourceProfiles.value as Array<Record<string, unknown>>) {
    const prefs = grp.compute_preferences as Array<Record<string, unknown>> | undefined;
    if (prefs) {
      for (const pref of prefs) {
        grpCompResources[pref.compute_resource_id as string] = true;
      }
    }
  }
  const result: Array<{ host_id: string; host: string }> = [];
  const existingHostIds = (appDeployments.value as Array<Record<string, unknown>>).map((d) => d.compute_host_id as string);
  const hasGrpRestriction = Object.keys(grpCompResources).length > 0;
  for (const [hostId, name] of Object.entries(computeResourceNames.value || {})) {
    if (existingHostIds.includes(hostId)) continue;
    if (hasGrpRestriction && !grpCompResources[hostId]) continue;
    result.push({ host_id: hostId, host: name });
  }
  return result.sort((a, b) => a.host.localeCompare(b.host));
});

const editingDeploymentQueues = computed(() => {
  const cr = editingDeploymentComputeResource.value as Record<string, unknown> | null;
  if (cr && cr.batch_queues) {
    return cr.batch_queues as unknown[];
  }
  return [];
});

// --- Data loading ---
function loadModule(): Promise<void> {
  return services.ApplicationModuleService.retrieve({
    lookup: props.appModuleId,
  }).then((m: unknown) => { appModule.value = m; });
}

function loadInterface(): Promise<void> {
  return services.ApplicationModuleService.getApplicationInterface(
    { lookup: props.appModuleId },
    { ignoreErrors: true },
  )
    .then((iface: unknown) => {
      appInterface.value = iface;
    })
    .catch((error: unknown) => {
      const err = error as { details?: { status?: number } };
      if (err.details && err.details.status === 404) {
        const iface = new models.ApplicationInterfaceDefinition({ user_has_write_access: true });
        (iface as unknown as { addStandardOutAndStandardErrorOutputs(): void }).addStandardOutAndStandardErrorOutputs();
        appInterface.value = iface;
      }
    });
}

function loadDeployments(): Promise<void> {
  return services.ApplicationModuleService.getApplicationDeployments({
    lookup: props.appModuleId,
  }).then((deps: unknown[]) => { appDeployments.value = deps; });
}

function loadComputeResourceNames(): Promise<void> {
  return services.ComputeResourceService.names().then(
    (names: Record<string, string>) => { computeResourceNames.value = names; },
  );
}

function loadGroupResourceProfiles(): Promise<void> {
  return services.ProjectResourceProfileService.list().then(
    (profiles: unknown[]) => { groupResourceProfiles.value = profiles; },
  );
}

function getComputeResourceName(hostId: string): string {
  if (computeResourceNames.value && hostId in computeResourceNames.value) {
    return computeResourceNames.value[hostId];
  }
  return hostId ? hostId.substring(0, 20) + "..." : "";
}

function inputKey(field: Record<string, unknown>, idx: number): string | number {
  return (field.key as string) || idx;
}

// --- Interface editing ---
function addInput(): void {
  const input = new models.InputDataObjectType();
  const inp = input as unknown as Record<string, unknown>;
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  if (inp.application_argument == null) {
    inp.application_argument = "";
  }
  const iface = appInterface.value as Record<string, unknown>;
  (iface.application_inputs as Array<unknown>).push(input);
}

function removeInput(idx: number): void {
  const iface = appInterface.value as Record<string, unknown>;
  (iface.application_inputs as Array<unknown>).splice(idx, 1);
}

function addOutput(): void {
  const output = new models.OutputDataObjectType();
  const out = output as unknown as Record<string, unknown>;
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  if (out.application_argument == null) {
    out.application_argument = "";
  }
  const iface = appInterface.value as Record<string, unknown>;
  (iface.application_outputs as Array<unknown>).push(output);
}

function removeOutput(idx: number): void {
  const iface = appInterface.value as Record<string, unknown>;
  (iface.application_outputs as Array<unknown>).splice(idx, 1);
}

// --- Deployment editing ---
function editDeployment(dep: Record<string, unknown>): void {
  editingDeployment.value = dep;
  editingDeploymentComputeResource.value = null;
  if (dep.compute_host_id) {
    services.ComputeResourceService.retrieve({
      lookup: dep.compute_host_id,
    }).then((cr: unknown) => { editingDeploymentComputeResource.value = cr; });
  }
}

function addDeployment(): void {
  if (!newDeploymentComputeHostId.value) return;
  const dep = new models.ApplicationDeploymentDescription({ user_has_write_access: true });
  const d = dep as unknown as Record<string, unknown>;
  d.app_module_id = props.appModuleId;
  d.compute_host_id = newDeploymentComputeHostId.value;
  appDeployments.value.push(dep);
  newDeploymentComputeHostId.value = null;
  editDeployment(d);
}

function addPreJobCommand(): void {
  const dep = editingDeployment.value as Record<string, unknown>;
  if (!dep.pre_job_commands) dep.pre_job_commands = [];
  (dep.pre_job_commands as Array<unknown>).push(new models.CommandObject({ command: "" }));
}

function addPostJobCommand(): void {
  const dep = editingDeployment.value as Record<string, unknown>;
  if (!dep.post_job_commands) dep.post_job_commands = [];
  (dep.post_job_commands as Array<unknown>).push(new models.CommandObject({ command: "" }));
}

function addModuleLoadCommand(): void {
  const dep = editingDeployment.value as Record<string, unknown>;
  if (!dep.module_load_cmds) dep.module_load_cmds = [];
  (dep.module_load_cmds as Array<unknown>).push(new models.CommandObject({ command: "" }));
}

function addEnvVar(): void {
  const dep = editingDeployment.value as Record<string, unknown>;
  if (!dep.set_environment) dep.set_environment = [];
  (dep.set_environment as Array<unknown>).push(new models.SetEnvPaths({ name: "", value: "" }));
}

function confirmDeleteDeployment(dep: Record<string, unknown>): void {
  deleteDeploymentTarget.value = dep;
}

function deleteDeployment(): void {
  const dep = deleteDeploymentTarget.value as Record<string, unknown>;
  deleteDeploymentTarget.value = null;
  if (dep.app_deployment_id) {
    services.ApplicationDeploymentService.delete({
      lookup: dep.app_deployment_id,
    }).then(() => {
      appDeployments.value = (appDeployments.value as Array<Record<string, unknown>>).filter(
        (d) => d.compute_host_id !== dep.compute_host_id,
      );
      const ed = editingDeployment.value as Record<string, unknown> | null;
      if (ed && ed.compute_host_id === dep.compute_host_id) {
        editingDeployment.value = null;
      }
    });
  } else {
    appDeployments.value = (appDeployments.value as Array<Record<string, unknown>>).filter(
      (d) => d.compute_host_id !== dep.compute_host_id,
    );
    const ed = editingDeployment.value as Record<string, unknown> | null;
    if (ed && ed.compute_host_id === dep.compute_host_id) {
      editingDeployment.value = null;
    }
  }
}

// --- Save all ---
async function saveAll(): Promise<void> {
  saving.value = true;
  saveMessage.value = null;
  saveError.value = null;

  try {
    // 1. Save module
    let moduleId = props.appModuleId;
    if (moduleId) {
      await services.ApplicationModuleService.update({
        lookup: moduleId,
        data: appModule.value,
      });
    } else {
      const created = await services.ApplicationModuleService.create({
        data: appModule.value,
      });
      appModule.value = created;
      moduleId = (created as Record<string, unknown>).app_module_id as string;
    }

    // 2. Save interface — ALWAYS ensure an interface exists for the
    // module with at least the auto-generated stdout/stderr outputs.
    if (!appInterface.value) {
      const iface = new models.ApplicationInterfaceDefinition({ user_has_write_access: true });
      (iface as unknown as { addStandardOutAndStandardErrorOutputs(): void }).addStandardOutAndStandardErrorOutputs();
      appInterface.value = iface;
    } else {
      const iface = appInterface.value as Record<string, unknown>;
      if (
        !iface.application_outputs ||
        (iface.application_outputs as Array<unknown>).length === 0
      ) {
        (appInterface.value as unknown as { addStandardOutAndStandardErrorOutputs(): void }).addStandardOutAndStandardErrorOutputs();
      }
    }
    const ifaceObj = appInterface.value as Record<string, unknown>;
    const mod = appModule.value as Record<string, unknown>;
    ifaceObj.application_name = mod.app_module_name;
    ifaceObj.application_modules = [moduleId];
    if (ifaceObj.application_interface_id) {
      appInterface.value = await services.ApplicationInterfaceService.update({
        lookup: ifaceObj.application_interface_id,
        data: appInterface.value,
      });
    } else {
      appInterface.value = await services.ApplicationInterfaceService.create({
        data: appInterface.value,
      });
    }

    // 3. Save deployments
    for (const dep of appDeployments.value as Array<Record<string, unknown>>) {
      dep.app_module_id = moduleId;
      if (dep.app_deployment_id) {
        await services.ApplicationDeploymentService.update({
          lookup: dep.app_deployment_id,
          data: dep,
        });
      } else {
        const created = await services.ApplicationDeploymentService.create({ data: dep });
        Object.assign(dep, created);
      }
    }

    saveMessage.value = "Application saved successfully.";
    saveMessageClass.value = "alert-success";

    // If this was a new application, navigate to the edit URL
    if (!props.appModuleId && moduleId) {
      window.location.href = "/workspace/applications/" + moduleId + "/";
    }
  } catch (error) {
    const err = error as { details?: { message?: string; response?: unknown }; message?: string };
    const detail = err.details
      ? err.details.message || JSON.stringify(err.details.response || err.details)
      : err.message || "An error occurred while saving.";
    saveError.value = detail;
  } finally {
    saving.value = false;
  }
}

// --- Delete application ---
function confirmDeleteApp(): void {
  showDeleteAppModal.value = true;
}

async function deleteApp(): Promise<void> {
  deleting.value = true;
  try {
    const deploymentDeletes = (appDeployments.value || [])
      .map((dep) => {
        if (!dep) return null;
        const d = dep as Record<string, unknown>;
        const id = (d.app_deployment_id || d.application_deployment_id || null) as string | null;
        if (!id) return null;
        return services.ApplicationDeploymentService.delete({ lookup: id });
      })
      .filter((p): p is Promise<unknown> => p !== null);
    await Promise.all(deploymentDeletes);

    const iface = appInterface.value as Record<string, unknown> | null;
    const interfaceId = iface &&
      ((iface.application_interface_id || iface.applicationInterfaceId) as string | null || null);
    if (interfaceId) {
      await services.ApplicationInterfaceService.delete({ lookup: interfaceId });
    }

    if (props.appModuleId) {
      await services.ApplicationModuleService.delete({ lookup: props.appModuleId });
    }
    window.location.href = "/workspace/applications";
  } catch (error) {
    console.error("Failed to delete application", error);
    const err = error as { message?: string; details?: unknown };
    saveError.value =
      "Failed to delete application: " +
      (err && (err.message || err.details || "unknown error"));
    showDeleteAppModal.value = false;
  } finally {
    deleting.value = false;
  }
}

function cancel(): void {
  window.location.href = "/workspace/applications";
}

onMounted(() => {
  if (props.appModuleId) {
    loading.value = true;
    Promise.all([
      loadModule(),
      loadInterface(),
      loadDeployments(),
      loadComputeResourceNames(),
      loadGroupResourceProfiles(),
    ]).finally(() => {
      loading.value = false;
    });
  } else {
    Promise.all([loadComputeResourceNames(), loadGroupResourceProfiles()]);
    // Create a default interface with stdout/stderr
    const iface = new models.ApplicationInterfaceDefinition({ user_has_write_access: true });
    (iface as unknown as { addStandardOutAndStandardErrorOutputs(): void }).addStandardOutAndStandardErrorOutputs();
    appInterface.value = iface;
  }
});
</script>
