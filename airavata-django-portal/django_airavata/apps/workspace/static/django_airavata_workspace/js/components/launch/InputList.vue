<template>
  <div v-if="store.pickedInterface">
    <div
      v-for="io in store.pickedInterface.inputs"
      :key="io.name"
      data-test="input-row"
    >
      <FileInputRow
        v-if="io.type === 'file' || io.type === 'dir'"
        :descriptor="io"
        :model-value="(store.draft.inputs[io.name] as { storage_id: string; path: string } | null) ?? null"
        :storages="storages"
        @update:model-value="store.setInput(io.name, $event)"
      />
      <ScalarInputRow
        v-else
        :descriptor="io"
        :model-value="(store.draft.inputs[io.name] as string | number | boolean | null) ?? null"
        @update:model-value="store.setInput(io.name, $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UserStorage } from "django-airavata-common-ui/js/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";
import FileInputRow from "./FileInputRow.vue";
import ScalarInputRow from "./ScalarInputRow.vue";

defineProps<{ storages: UserStorage[] }>();
const store = useLaunchStore();
</script>
