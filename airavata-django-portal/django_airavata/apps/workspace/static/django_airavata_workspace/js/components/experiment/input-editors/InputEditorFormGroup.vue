<template>
  <div class="space-y-1.5">
    <Label :for="labelFor">{{ label }}</Label>
    <slot></slot>
    <div v-if="state === false" class="text-sm text-destructive">
      <ul
        v-if="feedbackMessages && feedbackMessages.length > 1"
        class="list-disc pl-5"
      >
        <li v-for="feedback in feedbackMessages" :key="feedback">
          {{ feedback }}
        </li>
      </ul>
      <div v-else-if="feedbackMessages && feedbackMessages.length === 1">
        {{ feedbackMessages[0] }}
      </div>
    </div>
    <p v-if="description" class="text-sm text-muted-foreground">
      <linkify>{{ description }}</linkify>
    </p>
  </div>
</template>

<script>
import { components } from "django-airavata-common-ui";
export default {
  name: "input-editor-form-group",
  props: {
    label: {
      type: String,
      required: true,
    },
    labelFor: {
      type: String,
      required: true,
    },
    state: {
      type: Boolean,
    },
    feedbackMessages: {
      type: Array,
    },
    description: {
      type: String,
    },
  },
  components: {
    linkify: components.Linkify,
  },
};
</script>
