<template>
  <div class="card" :title="title" title-tag="h5">
    <div v-for="commandObject in data" :key="commandObject.key" class="input-group mb-1">
      <input
        ref="commandObjectInputs"
        v-model="commandObject.command"
        class="form-control"
        type="text"
        required
        :disabled="readonly"
      />
      <span class="input-group-text">
        <button class="btn btn-secondary btn-sm" @click="deleteCommandObject(commandObject)">
          <i class="fa fa-trash"></i>
          <span class="visually-hidden">Delete</span>
        </button>
      </span>
    </div>
    <button v-if="!readonly" class="btn btn-secondary btn-sm" @click="addCommandObject">
      {{ addButtonLabel }}
    </button>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "CommandObjectsEditor",
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
    addCommandObject() {
      if (!this.data) {
        this.data = [];
      }
      this.data.push(new models.CommandObject());
      this.$nextTick(() =>
        this.$refs.commandObjectInputs[this.$refs.commandObjectInputs.length - 1].focus(),
      );
    },
    deleteCommandObject(commandObject) {
      const index = this.data.findIndex((cmd) => cmd.key === commandObject.key);
      this.data.splice(index, 1);
    },
  },
};
</script>
