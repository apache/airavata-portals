<template>
  <form-group v-if="isEditing" label="Experiment Description" label-for="experiment-description">
    <textarea
      id="experiment-description"
      ref="description"
      v-model="data"
      class="form-control"
      rows="3"
      maxlength="255"
    ></textarea>
    <div class="mt-1">
      <button class="btn btn-success btn-sm" @click="toggleEditing">Save description</button>
      <a title="Cancel editing" class="text-secondary ms-3" @click="cancelEditing">
        <i class="fas fa-times"></i>
        <span class="visually-hidden">Cancel editing</span>
      </a>
    </div>
  </form-group>
  <div v-else class="mb-3">
    <a class="d-inline-block text-body mb-1" @click="startEditing">
      <i class="fas fa-align-left"></i>
      <span v-if="data"> Edit the description</span>
      <span v-else> Add a description</span>
    </a>
    <div v-if="data" class="ms-3">
      {{ data }}
    </div>
  </div>
</template>

<script>
import { mixins } from "django-airavata-common-ui";

export default {
  name: "ExperimentDescriptionEditor",
  mixins: [mixins.VModelMixin],
  data() {
    return {
      isEditing: false,
      originalValue: this.value,
    };
  },
  methods: {
    toggleEditing() {
      this.isEditing = !this.isEditing;
    },
    startEditing() {
      this.originalValue = this.data;
      this.isEditing = true;
      this.$nextTick(() => this.$refs.description.focus());
    },
    cancelEditing() {
      this.data = this.originalValue;
      this.isEditing = false;
    },
  },
};
</script>
