<template>
  <div v-if="store.pickedApp" class="row g-2">
    <div
      v-for="iface in store.pickedApp.interfaces"
      :key="iface.name"
      class="col-6 col-md-3"
      data-test="iface-card"
    >
      <button
        type="button"
        class="card w-100 text-start p-2"
        :class="{ 'border-primary': store.draft.interface_name === iface.name }"
        :data-test="`iface-card-${iface.name}`"
        @click="store.pickInterface(iface.name)"
      >
        <code class="d-block fw-bold">{{ iface.name }}</code>
        <small class="text-muted" :data-test="`iface-sig-${iface.name}`">
          ({{ formatList(iface.inputs) }}) → {{ formatList(iface.outputs) || "void" }}
        </small>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IODescriptor } from "django-airavata-common-ui/js/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const store = useLaunchStore();

function formatList(io: IODescriptor[]): string {
  return io.map((x) => `${x.name}: ${x.type}`).join(", ");
}
</script>
