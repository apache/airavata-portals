<template>
  <div v-if="store.pickedInterface">
    <FileOutputRow
      v-for="io in fileOutputs"
      :key="io.name"
      :descriptor="io"
      :model-value="store.draft.outputs[io.name] ?? null"
      :storages="storages"
      @update:model-value="store.setOutput(io.name, $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { UserStorage } from "django-airavata-common-ui/js/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import FileOutputRow from "./FileOutputRow.vue";

defineProps<{ storages: UserStorage[] }>();
const store = useLaunchStore();
const fileOutputs = computed(() =>
  (store.pickedInterface?.outputs ?? []).filter((o) => o.type === "file" || o.type === "dir"),
);
</script>
