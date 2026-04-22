<template>
  <form v-if="experiment" @submit.prevent="onSubmit">
    <div ref="experimentName" @input="updateExperimentName">
      <!-- programmatically define slot for experiment-name as native slot
            (not Vue slots), see #mounted() -->
    </div>
    <div ref="projectSelector" @input="updateProjectId">
      <!-- programmatically define slot for experiment-project as native slot
           (not Vue slots), see #mounted() -->
    </div>
    <template v-for="input in (experiment as any).experiment_inputs" :key="(input as any).name">
      <div
        :ref="(el) => { if (el) inputRefs[(input as any).name] = el as HTMLElement; }"
        @input="updateInputValue((input as any).name, $event)"
      >
        <!-- programmatically define slots as native slots (not Vue slots), see #mounted() -->
      </div>
    </template>
    <div ref="groupResourceProfileSelector">
      <!-- programmatically define slot for adpf-group-resource-profile-selector -->
    </div>
    <div ref="computeResourceSelector">
      <!-- programmatically define slot for adpf-experiment-compute-resource-selector -->
    </div>
    <div ref="queueSettingsEditor">
      <!-- programmatically define slot for adpf-queue-settings-editor -->
    </div>
    <div ref="experimentButtons">
      <!-- programmatically define slot for experiment-buttons as
          native slot (not Vue slots), see #mounted() -->
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, getCurrentInstance } from "vue";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

const props = defineProps<{
  applicationId: string;
  experimentId?: string;
}>();

const emit = defineEmits<{
  loaded: [experiment: unknown];
}>();

const webComponentsStore = useWebComponentsStore();

const experimentName = ref<HTMLElement | null>(null);
const projectSelector = ref<HTMLElement | null>(null);
const groupResourceProfileSelector = ref<HTMLElement | null>(null);
const computeResourceSelector = ref<HTMLElement | null>(null);
const queueSettingsEditor = ref<HTMLElement | null>(null);
const experimentButtons = ref<HTMLElement | null>(null);
// Dynamic input refs keyed by input name
const inputRefs: Record<string, HTMLElement> = {};

const experiment = computed(() => webComponentsStore.experiment);
const groupResourceProfileId = computed(() => webComponentsStore.groupResourceProfileId);

function updateExperimentName(event: Event) {
  webComponentsStore.updateExperimentName({
    name: (event.target as HTMLInputElement).value,
  });
}

function updateInputValue(inputName: string, event: Event) {
  const customEvent = event as CustomEvent;
  const value = Array.isArray(customEvent.detail)
    ? customEvent.detail[0]
    : (event.target as HTMLInputElement | null)
      ? (event.target as HTMLInputElement).value
      : event;
  webComponentsStore.updateExperimentInputValue({ inputName, value });
}

function updateProjectId(event: Event) {
  const [projectId] = (event as CustomEvent).detail as [string];
  webComponentsStore.updateProjectId({ projectId });
}

function createSlot(name: string, ...children: Node[]) {
  const slot = document.createElement("slot");
  slot.setAttribute("name", name);
  slot.append(...children);
  return slot;
}

function navigateToExperimentsList() {
  window.location.assign("/workspace/experiments");
}

function navigateToViewExperiment(exp: unknown) {
  const e = exp as { experiment_id?: string; project_id?: string } | null;
  if (e?.project_id && e?.experiment_id) {
    window.location.assign(
      "/workspace/projects/" +
        encodeURIComponent(e.project_id) +
        "/experiments/" +
        encodeURIComponent(e.experiment_id) +
        "/?launching=true",
    );
  } else {
    navigateToExperimentsList();
  }
}

async function onSubmit(event: SubmitEvent) {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  const saveEvent = new CustomEvent("save", {
    detail: [experiment.value],
    cancelable: true,
    composed: true,
  });
  el?.dispatchEvent(saveEvent);
  if (saveEvent.defaultPrevented) {
    return;
  }
  if ((event.submitter as HTMLButtonElement | null)?.name === "save-experiment-button") {
    await webComponentsStore.saveExperiment();
    postSave();
    return;
  } else {
    await webComponentsStore.saveExperiment();
    await webComponentsStore.launchExperiment();
    postSaveAndLaunch(experiment.value);
    return;
  }
}

function postSave() {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  const savedEvent = new CustomEvent("saved", {
    detail: [experiment.value],
    cancelable: true,
    composed: true,
  });
  el?.dispatchEvent(savedEvent);
  if (savedEvent.defaultPrevented) {
    return;
  }
  navigateToExperimentsList();
}

function postSaveAndLaunch(exp: unknown) {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  const savedAndLaunchedEvent = new CustomEvent("saved-and-launched", {
    detail: [experiment.value],
    cancelable: true,
    composed: true,
  });
  el?.dispatchEvent(savedAndLaunchedEvent);
  if (savedAndLaunchedEvent.defaultPrevented) {
    return;
  }
  navigateToViewExperiment(exp);
}

onMounted(async () => {
  if (props.experimentId) {
    await webComponentsStore.loadExperiment({
      experimentId: props.experimentId,
    });
  } else {
    await webComponentsStore.loadNewExperiment({
      applicationId: props.applicationId,
    });
  }
  emit("loaded", experiment.value);

  await nextTick();

  const exp = experiment.value as unknown as {
    experiment_inputs: Array<{ name: string; type: { name: string }; value: string | null }>;
    experiment_name: string;
    project_id: string | null;
  } | null;

  if (!exp) return;

  for (const input of exp.experiment_inputs) {
    const slot = document.createElement("slot");
    slot.setAttribute("name", input.name);
    const refEl = inputRefs[input.name];
    if (["STRING", "INTEGER", "FLOAT"].includes(input.type.name)) {
      slot.textContent = `${input.name} `;
      const textInput = document.createElement("adpf-string-input-editor");
      textInput.setAttribute("value", input.value !== null ? input.value : "");
      textInput.setAttribute("name", input.name);
      slot.appendChild(textInput);
      if (refEl) refEl.append(slot);
    } else if (input.type.name === "URI") {
      slot.textContent = `${input.name} `;
      const fileInputEditor = document.createElement("adpf-file-input-editor");
      fileInputEditor.setAttribute("value", input.value !== null ? input.value : "");
      fileInputEditor.setAttribute("name", input.name);
      slot.appendChild(fileInputEditor);
      if (refEl) refEl.append(slot);
    } else if (input.type.name === "URI_COLLECTION") {
      slot.textContent = `${input.name} `;
      const multiFileInputEditor = document.createElement("adpf-multi-file-input-editor");
      multiFileInputEditor.setAttribute("value", input.value !== null ? input.value : "");
      multiFileInputEditor.setAttribute("name", input.name);
      slot.appendChild(multiFileInputEditor);
      if (refEl) refEl.append(slot);
    }
  }

  // Experiment Name native slot
  const experimentNameGroupEl = document.createElement("div");
  experimentNameGroupEl.classList.add("form-group");
  const experimentNameLabelEl = document.createElement("label");
  experimentNameLabelEl.setAttribute("for", "experiment-name-input");
  experimentNameLabelEl.textContent = "Experiment Name";
  const experimentNameInputEl = document.createElement("input");
  experimentNameInputEl.classList.add("form-control");
  experimentNameInputEl.setAttribute("id", "experiment-name-input");
  experimentNameInputEl.setAttribute("type", "text");
  experimentNameInputEl.setAttribute("name", "experiment-name");
  experimentNameInputEl.setAttribute("value", exp.experiment_name);
  experimentNameInputEl.setAttribute("required", "required");
  experimentNameGroupEl.append(experimentNameLabelEl, experimentNameInputEl);
  experimentName.value?.append(createSlot("experiment-name", experimentNameGroupEl));

  const projectSelectorEl = document.createElement("adpf-project-selector");
  if (exp.project_id) {
    projectSelectorEl.setAttribute("value", exp.project_id);
  }
  projectSelector.value?.append(createSlot("experiment-project", projectSelectorEl));

  const groupResourceProfileSelectorEl = document.createElement(
    "adpf-group-resource-profile-selector",
  );
  if (groupResourceProfileId.value) {
    groupResourceProfileSelectorEl.setAttribute("value", groupResourceProfileId.value as string);
  }
  groupResourceProfileSelector.value?.append(
    createSlot("experiment-group-resource-profile", groupResourceProfileSelectorEl),
  );

  const computeResourceSelectorEl = document.createElement(
    "adpf-experiment-compute-resource-selector",
  );
  computeResourceSelectorEl.setAttribute("application-module-id", props.applicationId);
  computeResourceSelector.value?.append(
    createSlot("experiment-compute-resource", computeResourceSelectorEl),
  );

  const queueSettingsEditorEl = document.createElement("adpf-queue-settings-editor");
  queueSettingsEditor.value?.append(
    createSlot("experiment-queue-settings", queueSettingsEditorEl),
  );

  // Experiment Buttons native slot
  const buttonsRowEl = document.createElement("div");
  buttonsRowEl.classList.add("d-flex", "justify-content-end");
  const saveAndLaunchButtonEl = document.createElement("button");
  saveAndLaunchButtonEl.setAttribute("type", "submit");
  saveAndLaunchButtonEl.setAttribute("name", "save-and-launch-experiment-button");
  saveAndLaunchButtonEl.classList.add("btn", "btn-success", "me-2");
  saveAndLaunchButtonEl.textContent = "Save and Launch";
  const saveButtonEl = document.createElement("button");
  saveButtonEl.setAttribute("type", "submit");
  saveButtonEl.setAttribute("name", "save-experiment-button");
  saveButtonEl.classList.add("btn", "btn-primary");
  saveButtonEl.textContent = "Save";
  buttonsRowEl.append(saveAndLaunchButtonEl, saveButtonEl);
  experimentButtons.value?.append(createSlot("experiment-buttons", buttonsRowEl));
});
</script>

<style lang="scss">
@import "./styles";

:host {
  display: block;
  margin-bottom: 1em;
}
</style>
