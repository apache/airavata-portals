<template>
  <iframe :src="url"></iframe>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";

type OutputDataObjectType = InstanceType<typeof models.OutputDataObjectType>;

const props = defineProps<{
  experimentOutput: OutputDataObjectType;
  dataProducts: unknown[];
  experimentId: string;
  providerId: string;
}>();

const url = computed(
  () =>
    "/api/notebook-output?" +
    "experiment-id=" +
    encodeURIComponent(props.experimentId) +
    "&experiment-output-name=" +
    encodeURIComponent(props.experimentOutput.name as string) +
    "&provider-id=" +
    encodeURIComponent(props.providerId),
);
</script>

<style scoped>
iframe {
  width: 100%;
  height: 400px;
  border: none;
}
</style>
