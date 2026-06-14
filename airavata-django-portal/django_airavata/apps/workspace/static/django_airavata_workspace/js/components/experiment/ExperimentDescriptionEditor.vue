<template>
  <div v-if="isEditing" class="space-y-1.5">
    <Label for="experiment-description">Experiment Description</Label>
    <Textarea
      id="experiment-description"
      v-model="data"
      rows="3"
      ref="description"
      maxlength="255"
    />
    <div class="mt-1 flex items-center">
      <Button
        size="sm"
        class="bg-success text-success-foreground hover:bg-success/90"
        @click="toggleEditing"
        >Save description</Button
      >
      <a
        href="#"
        @click.prevent="cancelEditing"
        title="Cancel editing"
        class="ml-3 text-muted-foreground"
      >
        <X class="size-4" />
        <span class="sr-only">Cancel editing</span>
      </a>
    </div>
  </div>
  <div v-else class="mb-3">
    <a
      href="#"
      @click.prevent="startEditing"
      class="mb-1 inline-flex items-center gap-1 text-foreground"
    >
      <AlignLeft class="size-4" />
      <span v-if="data"> Edit the description</span>
      <span v-else> Add a description</span>
    </a>
    <div v-if="data" class="ml-3">
      {{ data }}
    </div>
  </div>
</template>

<script>
import { AlignLeft, X } from "@lucide/vue";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "experiment-description-editor",
  components: { AlignLeft, X },
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
      this.$nextTick(() => this.$refs.description.$el.focus());
    },
    cancelEditing() {
      this.data = this.originalValue;
      this.isEditing = false;
    },
  },
};
</script>
