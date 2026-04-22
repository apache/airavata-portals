<template>
  <parser-editor
    v-if="parser"
    :parser="parser"
    @saved="handleSaved"
    @cancelled="handleCancelled"
  ></parser-editor>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { models, services } from "django-airavata-api";
import ParserEditor from "../parser-components/ParserEditor.vue";

const props = defineProps<{ parserId: string }>();

const parser = ref<InstanceType<typeof models.Parser> | null>(null);

onMounted(async () => {
  parser.value = await services.ParserService.retrieve({ lookup: props.parserId });
});

function handleSaved(): void {
  window.location.assign("/dataparsers/");
}

function handleCancelled(): void {
  window.location.assign("/dataparsers/");
}
</script>
