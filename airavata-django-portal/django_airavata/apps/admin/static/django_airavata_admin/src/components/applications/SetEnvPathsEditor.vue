<template>
  <div class="card" :title="title" title-tag="h5">
    <div
      v-for="setEnvPath in data"
      :key="setEnvPath.key"
      class="input-group mb-1 align-items-center"
    >
      <input
        ref="nameInputs"
        v-model="setEnvPath.name"
        class="form-control"
        type="text"
        required
        placeholder="NAME"
        :disabled="readonly"
      />
      <i class="fa fa-equals mx-1"></i>
      <input
        v-model="setEnvPath.value"
        class="form-control"
        type="text"
        required
        placeholder="VALUE"
        :disabled="readonly"
      />
      <span class="input-group-text">
        <button class="btn btn-secondary btn-sm" @click="deleteEnvPath(setEnvPath)">
          <i class="fa fa-trash"></i>
          <span class="visually-hidden">Delete</span>
        </button>
      </span>
    </div>
    <button v-if="!readonly" class="btn btn-secondary btn-sm" @click="addEnvPath">
      {{ addButtonLabel }}
    </button>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "SetEnvPathsEditor",
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: Array,
    },
    title: {
      type: String,
      required: true,
    },
    addButtonLabel: {
      type: String,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    addEnvPath() {
      if (!this.data) {
        this.data = [];
      }
      this.data.push(new models.SetEnvPaths());
      this.$nextTick(() => this.$refs.nameInputs[this.$refs.nameInputs.length - 1].focus());
    },
    deleteEnvPath(setEnvPath) {
      const index = this.data.findIndex((env) => env.key === setEnvPath.key);
      this.data.splice(index, 1);
    },
  },
};
</script>
