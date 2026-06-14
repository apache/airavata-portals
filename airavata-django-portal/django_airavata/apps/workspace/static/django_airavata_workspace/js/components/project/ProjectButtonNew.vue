<template>
  <div>
    <Button variant="default" @click="open = true">
      <slot> New Project <Plus class="size-4" aria-hidden="true" /> </slot>
    </Button>
    <Dialog v-model:open="open">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
        </DialogHeader>
        <project-editor
          v-model="newProject"
          ref="projectEditor"
          @save="onCreateProject"
          @valid="valid = true"
          @invalid="valid = false"
        />
        <DialogFooter>
          <Button variant="outline" @click="onCancelNewProject">Cancel</Button>
          <Button
            variant="default"
            :disabled="okDisabled"
            @click="onCreateProject"
            >OK</Button
          >
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script>
import { Plus } from "@lucide/vue";
import { models, services } from "django-airavata-api";
import ProjectEditor from "./ProjectEditor.vue";

export default {
  name: "project-button-new",
  data() {
    return {
      open: false,
      valid: false,
      newProject: new models.Project(),
    };
  },
  components: {
    Plus,
    ProjectEditor,
  },
  methods: {
    onCreateProject: function () {
      services.ProjectService.create({ data: this.newProject }).then(
        (result) => {
          this.open = false;
          this.$emit("new-project", result);
          // Reset state
          this.newProject = new models.Project();
          this.$refs.projectEditor.reset();
        },
      );
    },
    onCancelNewProject() {
      this.open = false;
      this.newProject = new models.Project();
      this.$refs.projectEditor.reset();
    },
  },
  computed: {
    okDisabled: function () {
      return !this.valid;
    },
  },
};
</script>
