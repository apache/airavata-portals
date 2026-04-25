<template>
  <div class="nav nav-tabs mb-3" role="tablist">
    <button
      v-for="t in tabs"
      :key="t.idx"
      role="tab"
      type="button"
      class="nav-link"
      :class="{ active: t.idx === active }"
      :disabled="t.disabled"
      @click="onClick(t.idx, t.disabled)"
    >
      {{ t.idx }} · {{ t.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

defineProps<{ active: 1 | 2 | 3 }>();
const emit = defineEmits<{ "update:active": [n: 1 | 2 | 3] }>();

const store = useLaunchStore();

const tabs = computed(() => [
  { idx: 1 as const, label: "Application & Inputs", disabled: false },
  { idx: 2 as const, label: "Runtime", disabled: !store.tab1Valid },
  { idx: 3 as const, label: "Review & Launch", disabled: !store.tab1Valid || !store.tab2Valid },
]);

function onClick(n: 1 | 2 | 3, disabled: boolean) {
  if (disabled) return;
  emit("update:active", n);
}
</script>
