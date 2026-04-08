<template>
  <div class="card" :title="title" title-tag="h5">
    <div class="input-group"
      v-for="commandObject in data"
      :key="commandObject.key"
      class="mb-1"
    >
      <input class="form-control"
        type="text"
        v-model="commandObject.command"
        required
        ref="commandObjectInputs"
        :disabled="readonly"
      />
      <div class="input-group"-append v-if="!readonly">
        <button class="btn"
          variant="secondary"
          @click="deleteCommandObject(commandObject)"
        >
          <i class="fa fa-trash"></i>
          <span class="visually-hidden">Delete</span>
        </button>
      </span>
    </div>
    <button class="btn" v-if="!readonly" variant="secondary" @click="addCommandObject">{{
      addButtonLabel
    }}</button>
  </div></div>
</template>

<script>
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "command-objects-editor",
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
        this.$refs.commandObjectInputs[
          this.$refs.commandObjectInputs.length - 1
        ].focus()
      );
    },
    deleteCommandObject(commandObject) {
      const index = this.data.findIndex((cmd) => cmd.key === commandObject.key);
      this.data.splice(index, 1);
    },
  },
};
</script>
