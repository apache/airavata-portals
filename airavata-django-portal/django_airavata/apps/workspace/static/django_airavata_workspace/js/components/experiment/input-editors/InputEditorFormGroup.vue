<template>
  <div class="mb-3">
    <label v-if="label" :for="labelFor" class="form-label">{{ label }}</label>
    <slot></slot>
    <div v-if="feedbackMessages && feedbackMessages.length > 1" class="invalid-feedback d-block">
      <ul>
        <li v-for="feedback in feedbackMessages" :key="feedback">
          {{ feedback }}
        </li>
      </ul>
    </div>
    <div
      v-else-if="feedbackMessages && feedbackMessages.length === 1"
      class="invalid-feedback d-block"
    >
      {{ feedbackMessages[0] }}
    </div>
    <small v-if="description" class="form-text text-muted">
      <linkify>{{ description }}</linkify>
    </small>
  </div>
</template>

<script setup lang="ts">
import { components } from "django-airavata-common-ui";

const Linkify = components.Linkify;

withDefaults(
  defineProps<{
    label: string;
    labelFor: string;
    state?: boolean | null;
    feedbackMessages?: string[] | null;
    description?: string | null;
  }>(),
  {
    state: null,
    feedbackMessages: null,
    description: null,
  },
);
</script>
