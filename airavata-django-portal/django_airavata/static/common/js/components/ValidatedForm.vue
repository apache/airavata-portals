<template>
  <form>
    <template v-for="item in items" :key="item.key">
      <validated-form-group
        :label="item.label ?? ''"
        :valid="isValid(item.key)"
        :feedback-messages="getFeedbackMessages(item.key)"
        :description="item.description"
      >
        <slot
          :item="item.item"
          :valid="() => setValid(item.key)"
          :invalid="(messages: string | string[]) => setInvalid(item.key, messages)"
        />
      </validated-form-group>
    </template>
  </form>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import ValidatedFormGroup from "./ValidatedFormGroup.vue";

interface FormItem {
  key: string;
  label?: string;
  description?: string;
  item: unknown;
}

defineProps<{
  items: FormItem[];
}>();

const emit = defineEmits<{
  valid: [];
  invalid: [];
}>();

const invalidFormItems = ref<string[]>([]);
const feedbackMessages = ref<Record<string, string[]>>({});

const valid = computed(() => invalidFormItems.value.length === 0);

function setValid(key: string): void {
  const wasValid = valid.value;
  if (invalidFormItems.value.includes(key)) {
    const index = invalidFormItems.value.indexOf(key);
    invalidFormItems.value.splice(index, 1);
  }
  if (!wasValid && valid.value) {
    emit("valid");
  }
}

function setInvalid(key: string, messages: string | string[]): void {
  const wasValid = valid.value;
  if (!invalidFormItems.value.includes(key)) {
    invalidFormItems.value.push(key);
  }
  if (typeof messages === "string") {
    feedbackMessages.value[key] = [messages];
  } else {
    feedbackMessages.value[key] = messages;
  }
  if (wasValid) {
    emit("invalid");
  }
}

function isValid(key: string): boolean {
  return !invalidFormItems.value.includes(key);
}

function getFeedbackMessages(key: string): string[] {
  if (key in feedbackMessages.value) {
    return feedbackMessages.value[key];
  } else {
    return [];
  }
}
</script>
