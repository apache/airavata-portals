<template>
  <div>
    <div class="d-flex">
      <slot name="title">
        <h1 class="h4 mb-4 me-auto">Edit Project</h1>
      </slot>
      <slot name="buttons"> </slot>
    </div>
    <form @submit="onSubmit" @input="onUserInput" novalidate>
      <form-group
        label="Project Name"
        label-for="project-name"
        :feedback="nameFeedback"
        :state="nameState"
      >
        <input class="form-control"
          id="project-name"
          type="text"
          v-model="data.name"
          required
          placeholder="Project name"
          :state="nameState"
        ></input>
      </div>
      <div class="mb-3" label="Project Description" label-for="project-description">
        <textarea class="form-control"
          id="project-description"
          type="text"
          v-model="data.description"
          placeholder="(Optional) Project description"
          :rows="3"
        ></textarea>
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
    this.$on("input", this.validate);
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
  },
};
</script>
