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
    <div class="mt-1 flex items-center gap-2">
      <Button size="sm" variant="default" @click="toggleEditing"
        >Save description</Button
      >
      <Button
        size="sm"
        variant="ghost"
        title="Cancel editing"
        @click="cancelEditing"
      >
        <X class="size-4" />
        <span class="sr-only">Cancel editing</span>
      </Button>
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
