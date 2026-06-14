<template>
  <div>
    <div class="flex">
      <slot name="title">
        <h1 class="mr-auto mb-4 text-xl font-semibold">Edit Project</h1>
      </slot>
      <slot name="buttons"> </slot>
    </div>
    <form @submit="onSubmit" @input="onUserInput" novalidate>
      <div class="mb-4 space-y-1.5">
        <Label for="project-name">Project Name</Label>
        <Input
          id="project-name"
          type="text"
          v-model="data.name"
          required
          placeholder="Project name"
          :aria-invalid="nameState === false"
        />
        <p v-if="nameFeedback" class="text-sm text-destructive">
          {{ nameFeedback }}
        </p>
      </div>
      <div class="mb-4 space-y-1.5">
        <Label for="project-description">Project Description</Label>
        <Textarea
          id="project-description"
          v-model="data.description"
          placeholder="(Optional) Project description"
          :rows="3"
        />
      </div>
    </form>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "project-editor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: models.Project,
      required: true,
    },
  },
  mounted() {
    this.validate();
  },
  data() {
    return {
      userBeginsInput: false,
    };
  },
  computed: {
    nameFeedback() {
      if (this.userBeginsInput && this.validation.name) {
        return this.validation.name.join("; ");
      } else {
        return null;
      }
    },
    nameState() {
      if (this.validation.name) {
        if (this.userBeginsInput) {
          return false;
        } else {
          return null;
        }
      } else {
        return true;
      }
    },
    validation() {
      const v = this.data.validate();
      return v ? v : {};
    },
  },
  methods: {
    validate() {
      if (Object.keys(this.validation).length > 0) {
        this.$emit("invalid");
      } else {
        this.$emit("valid");
      }
    },
    onUserInput() {
      this.userBeginsInput = true;
    },
    onSubmit(event) {
      event.preventDefault();
      this.$emit("save");
    },
    reset() {
      this.userBeginsInput = false;
    },
  },
  watch: {
    value() {
      this.validate();
    },
    // Re-validate on internal edits of the working copy. (Replaces the Vue 2
    // `this.$on("input", ...)` self-listener, which is removed in Vue 3.)
    data: {
      handler() {
        this.validate();
      },
      deep: true,
    },
  },
};
</script>
