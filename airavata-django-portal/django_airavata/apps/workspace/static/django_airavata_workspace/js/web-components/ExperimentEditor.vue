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
    <template v-for="input in experiment.experiment_inputs" :key="input.name">
      <div :ref="input.name" @input="updateInputValue(input.name, $event)">
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

<script>
import { mapState } from "pinia";
import { useExperimentStore } from "./store";
import urls from "../utils/urls";

export default {
  props: {
    // TODO: rename to applicationModuleId?
    applicationId: {
      type: String,
      required: true,
    },
    experimentId: {
      type: String,
      required: false,
    },
  },
  async mounted() {
    const store = useExperimentStore();
    if (this.experimentId) {
      await store.loadExperiment({
        experimentId: this.experimentId,
      });
    } else {
      await store.loadNewExperiment({
        applicationId: this.applicationId,
      });
    }
    this.$emit("loaded", this.experiment);
    // vue-web-component-wrapper clones native slots and turns them into Vue
    // slots which means they lose any event listeners and they basically aren't
    // in the DOM any more.  As a workaround, programmatically create native
    // slots. See also https://github.com/vuejs/vue-web-component-wrapper/issues/38
    this.$nextTick(() => {
      for (const input of this.experiment.experiment_inputs) {
        const slot = document.createElement("slot");
        slot.setAttribute("name", input.name);
        if (["STRING", "INTEGER", "FLOAT"].includes(input.type.name)) {
          slot.textContent = `${input.name} `;
          const textInput = document.createElement("adpf-string-input-editor");
          textInput.setAttribute(
            "value",
            input.value !== null ? input.value : "",
          );
          textInput.setAttribute("name", input.name);
          slot.appendChild(textInput);
          this.$refs[input.name][0].append(slot);
        } else if (input.type.name === "URI") {
          slot.textContent = `${input.name} `;
          const fileInputEditor = document.createElement(
            "adpf-file-input-editor",
          );
          fileInputEditor.setAttribute(
            "value",
            input.value !== null ? input.value : "",
          );
          fileInputEditor.setAttribute("name", input.name);
          slot.appendChild(fileInputEditor);
          this.$refs[input.name][0].append(slot);
        } else if (input.type.name === "URI_COLLECTION") {
          slot.textContent = `${input.name} `;
          const multiFileInputEditor = document.createElement(
            "adpf-multi-file-input-editor",
          );
          multiFileInputEditor.setAttribute(
            "value",
            input.value !== null ? input.value : "",
          );
          multiFileInputEditor.setAttribute("name", input.name);
          slot.appendChild(multiFileInputEditor);
          this.$refs[input.name][0].append(slot);
        }
      }
      // this.injectPropsIntoSlottedInputs();

      /*
       * Experiment Name native slot
       */
      // <slot name="experiment-name">
      //   <div class="space-y-1.5">
      //     <Label for="experiment-name">Experiment Name</Label>
      //     <Input
      //       type="text"
      //       name="experiment-name"
      //       :value="experiment.experimentName"
      //       required
      //     />
      //   </div>
      // </slot>
      const experimentNameGroupEl = document.createElement("div");
      experimentNameGroupEl.classList.add("space-y-1.5");
      const experimentNameLabelEl = document.createElement("label");
      experimentNameLabelEl.setAttribute("for", "experiment-name-input");
      experimentNameLabelEl.classList.add(
        "text-sm",
        "leading-none",
        "font-medium",
        "select-none",
      );
      experimentNameLabelEl.textContent = "Experiment Name";
      const experimentNameInputEl = document.createElement("input");
      experimentNameInputEl.classList.add(
        "h-9",
        "w-full",
        "rounded-md",
        "border",
        "border-input",
        "bg-transparent",
        "px-3",
        "py-1",
        "text-sm",
        "shadow-xs",
        "outline-none",
        "focus-visible:border-ring",
        "focus-visible:ring-3",
        "focus-visible:ring-ring/50",
      );
      experimentNameInputEl.setAttribute("id", "experiment-name-input");
      experimentNameInputEl.setAttribute("type", "text");
      experimentNameInputEl.setAttribute("name", "experiment-name");
      experimentNameInputEl.setAttribute(
        "value",
        this.experiment.experiment_name,
      );
      experimentNameInputEl.setAttribute("required", "required");
      experimentNameGroupEl.append(
        experimentNameLabelEl,
        experimentNameInputEl,
      );
      this.$refs.experimentName.append(
        this.createSlot("experiment-name", experimentNameGroupEl),
      );

      const projectSelectorEl = document.createElement("adpf-project-selector");
      if (this.experiment.project_id) {
        projectSelectorEl.setAttribute("value", this.experiment.project_id);
      }
      this.$refs.projectSelector.append(
        this.createSlot("experiment-project", projectSelectorEl),
      );

      const groupResourceProfileSelectorEl = document.createElement(
        "adpf-group-resource-profile-selector",
      );
      if (this.groupResourceProfileId) {
        groupResourceProfileSelectorEl.setAttribute(
          "value",
          this.groupResourceProfileId,
        );
      }
      this.$refs.groupResourceProfileSelector.append(
        this.createSlot(
          "experiment-group-resource-profile",
          groupResourceProfileSelectorEl,
        ),
      );

      const computeResourceSelectorEl = document.createElement(
        "adpf-experiment-compute-resource-selector",
      );
      computeResourceSelectorEl.setAttribute(
        "application-module-id",
        this.applicationId,
      );
      this.$refs.computeResourceSelector.append(
        this.createSlot(
          "experiment-compute-resource",
          computeResourceSelectorEl,
        ),
      );

      const queueSettingsEditorEl = document.createElement(
        "adpf-queue-settings-editor",
      );
      this.$refs.queueSettingsEditor.append(
        this.createSlot("experiment-queue-settings", queueSettingsEditorEl),
      );

      /*
       * Experiment (save/launch) Buttons native slot
       */
      // <slot name="experiment-buttons">
      //   <div class="flex justify-end gap-2">
      //     <Button type="submit" variant="secondary" name="save-experiment-button">
      //       Save
      //     </Button>
      //     <Button
      //       type="submit"
      //       variant="default"
      //       name="save-and-launch-experiment-button"
      //     >
      //       Save and Launch
      //     </Button>
      //   </div>
      // </slot>
      // shadcn-vue components are not globally registered in the standalone
      // web-component build, so the save/launch buttons are built with the same
      // Tailwind utility classes the Button component would emit.
      const buttonBaseClasses = [
        "inline-flex",
        "items-center",
        "justify-center",
        "gap-2",
        "whitespace-nowrap",
        "rounded-md",
        "text-sm",
        "font-medium",
        "h-9",
        "px-4",
        "py-2",
        "transition-all",
      ];
      const buttonsRowEl = document.createElement("div");
      buttonsRowEl.classList.add("flex", "justify-end", "gap-2");
      // Save uses the shadcn "secondary" variant; Save and Launch is the single
      // primary action and uses the "default" variant (no hand-rolled accent).
      const saveButtonEl = document.createElement("button");
      saveButtonEl.setAttribute("type", "submit");
      saveButtonEl.setAttribute("name", "save-experiment-button");
      saveButtonEl.classList.add(
        ...buttonBaseClasses,
        "bg-secondary",
        "text-secondary-foreground",
        "hover:bg-secondary/80",
      );
      saveButtonEl.textContent = "Save";
      const saveAndLaunchButtonEl = document.createElement("button");
      saveAndLaunchButtonEl.setAttribute("type", "submit");
      saveAndLaunchButtonEl.setAttribute(
        "name",
        "save-and-launch-experiment-button",
      );
      saveAndLaunchButtonEl.classList.add(
        ...buttonBaseClasses,
        "bg-primary",
        "text-primary-foreground",
        "hover:bg-primary/90",
      );
      saveAndLaunchButtonEl.textContent = "Save and Launch";
      buttonsRowEl.append(saveButtonEl, saveAndLaunchButtonEl);
      this.$refs.experimentButtons.append(
        this.createSlot("experiment-buttons", buttonsRowEl),
      );
    });
  },
  computed: {
    ...mapState(useExperimentStore, {
      experiment: "experiment",
      groupResourceProfileId: "getGroupResourceProfileId",
    }),
  },
  methods: {
    updateExperimentName(event) {
      useExperimentStore().updateExperimentName({
        name: event.target.value,
      });
    },
    updateInputValue(inputName, event) {
      // web component input events have the current value in a detail array,
      // native input events have the current value in target.value
      const value = Array.isArray(event.detail)
        ? event.detail[0]
        : event.target // Backwards compatibility: second argument changed from the value to the 'event'
          ? event.target.value
          : event;
      useExperimentStore().updateExperimentInputValue({ inputName, value });
    },
    updateProjectId(event) {
      const [projectId] = event.detail;
      useExperimentStore().updateProjectId({ projectId });
    },
    async onSubmit(event) {
      // console.log(event);
      // 'save' event is cancelable. Listener can call .preventDefault() on the event to cancel.
      // composed: true allows the shadow DOM event to bubble up through the shadow root.
      const saveEvent = new CustomEvent("save", {
        detail: [this.experiment],
        cancelable: true,
        composed: true,
      });
      this.$el.dispatchEvent(saveEvent);
      if (saveEvent.defaultPrevented) {
        return;
      }
      const store = useExperimentStore();
      if (event.submitter.name === "save-experiment-button") {
        await store.saveExperiment();
        this.postSave();
        return;
      } else {
        // Default submit button handling is save and launch
        await store.saveExperiment();
        await store.launchExperiment();
        this.postSaveAndLaunch(this.experiment);
        return;
      }
    },
    postSave() {
      // client code can listen for 'saved' and preventDefault() on it to handle
      // it differently. Default action is to navigate to experiments list.
      const savedEvent = new CustomEvent("saved", {
        detail: [this.experiment],
        cancelable: true,
        composed: true,
      });
      this.$el.dispatchEvent(savedEvent);
      if (savedEvent.defaultPrevented) {
        return;
      }
      urls.navigateToExperimentsList();
    },
    postSaveAndLaunch(experiment) {
      // client code can listen for 'saved-and-launched' and preventDefault() on
      // it to handle it differently. Default action is to navigate to
      // the experiment summary page.
      const savedAndLaunchedEvent = new CustomEvent("saved-and-launched", {
        detail: [this.experiment],
        cancelable: true,
        composed: true,
      });
      this.$el.dispatchEvent(savedAndLaunchedEvent);
      if (savedAndLaunchedEvent.defaultPrevented) {
        return;
      }
      urls.navigateToViewExperiment(experiment, { launching: true });
    },
    createSlot(name, ...children) {
      const slot = document.createElement("slot");
      slot.setAttribute("name", name);
      slot.append(...children);
      return slot;
    },
  },
};
</script>

<style lang="scss">
@import "./styles";

:host {
  display: block;
  margin-bottom: 1em;
}
</style>
