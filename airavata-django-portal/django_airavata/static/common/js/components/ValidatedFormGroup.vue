<template>
  <div class="space-y-1.5">
    <Label>{{ label }}</Label>
    <slot></slot>
    <template v-if="!valid">
      <ul
        v-if="feedbackMessages && feedbackMessages.length > 1"
        class="list-inside list-disc text-sm text-destructive"
      >
        <li v-for="feedback in feedbackMessages" :key="feedback">
          {{ feedback }}
        </li>
      </ul>
      <p
        v-else-if="feedbackMessages && feedbackMessages.length === 1"
        class="text-sm text-destructive"
      >
        {{ feedbackMessages[0] }}
      </p>
    </template>
    <p v-if="description" class="text-sm text-muted-foreground">
      {{ description }}
    </p>
  </div>
</template>

<script>
export default {
  name: "validated-form-group",
  props: {
    label: {
      type: String,
      required: true,
    },
    description: {
      type: String,
    },
    valid: {
      type: Boolean,
      required: true,
    },
    feedbackMessages: {
      type: Array,
      required: true,
    },
  },
};
</script>
