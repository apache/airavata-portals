<template>
  <span :class="{ 'font-italic': notAvailable }">{{ name }}</span>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { services } from "django-airavata-api";

const props = defineProps<{
  computeResourceId: string;
}>();

const computeResource = ref<{ host_name: string } | null>(null);
const notAvailable = ref(false);

const name = computed(() => {
  if (notAvailable.value) {
    return "N/A";
  } else {
    return computeResource.value ? computeResource.value.host_name : "";
  }
});

watch(
  () => props.computeResourceId,
  () => loadComputeResource(),
);

onMounted(() => {
  loadComputeResource();
});

function loadComputeResource(): void {
  services.ComputeResourceService.retrieve(
    { lookup: props.computeResourceId },
    { ignoreErrors: true, cache: true },
  )
    .then((cr: { host_name: string }) => (computeResource.value = cr))
    .catch(() => (notAvailable.value = true));
}
</script>
