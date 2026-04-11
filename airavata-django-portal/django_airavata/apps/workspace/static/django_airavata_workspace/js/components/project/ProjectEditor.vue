<template>
  <div>
    <div class="d-flex">
      <slot name="title">
        <h1 class="h4 mb-4 me-auto">Edit Project</h1>
      </slot>
      <slot name="buttons"> </slot>
    </div>
    <form @submit.prevent="onSubmit" @input="onUserInput" novalidate>
      <div class="mb-3">
        <label for="project-name" class="form-label">Project Name <span class="text-danger">*</span></label>
        <input class="form-control" :class="{ 'is-invalid': userBeginsInput && nameState === false }"
          id="project-name" type="text" v-model="data.name" required placeholder="Project name" />
        <div v-if="userBeginsInput && nameFeedback" class="invalid-feedback">{{ nameFeedback }}</div>
      </div>
      <div class="mb-3">
        <label for="project-description" class="form-label">Description</label>
        <textarea class="form-control" id="project-description" v-model="data.description"
          placeholder="Optional description" rows="3"></textarea>
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
    modelValue: {
      type: models.Project,
      required: true,
    },
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
      }
      return null;
    },
    nameState() {
      if (this.validation.name) {
        return this.userBeginsInput ? false : null;
      }
      return true;
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
    onSubmit() {
      this.$emit("save");
    },
    reset() {
      this.userBeginsInput = false;
    },
  },
  watch: {
    data: {
      handler() {
        this.validate();
      },
      deep: true,
    },
    modelValue() {
      this.validate();
    },
  },
  mounted() {
    this.validate();
  },
};
</script>
