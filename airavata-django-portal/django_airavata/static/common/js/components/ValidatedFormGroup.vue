<template>
  <div class="mb-3">
    <label v-if="label" class="form-label">{{ label }}</label>
    <slot></slot>
    <div v-if="description" class="form-text">{{ description }}</div>
    <div v-if="!valid && feedbackMessages && feedbackMessages.length > 0" class="invalid-feedback d-block">
      <ul v-if="feedbackMessages.length > 1" class="mb-0">
        <li v-for="feedback in feedbackMessages" :key="feedback">
          {{ feedback }}
        </li>
      </ul>
      <div v-else>
        {{ feedbackMessages[0] }}
      </div>
    </div>
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
