<template>
  <div v-html="rawOutput" />
</template>

<script setup lang="ts">
import { computed, watch } from "vue";

const props = defineProps<{
  viewData: Record<string, unknown>;
}>();

const rawOutput = computed(() =>
  props.viewData && props.viewData.output ? (props.viewData.output as string) : null,
);
const rawJSFile = computed(() =>
  props.viewData && props.viewData.js ? (props.viewData.js as string) : null,
);

watch(rawJSFile, (val) => {
  // TODO: check if script is already loaded
  if (val) {
    loadScripts(val);
  }
});

// Attaches the script to the head, the name of the script can be passed from
// output view provider
function loadScripts(src: string): Promise<void> {
  return new Promise((resolve) => {
    const scriptEl = document.createElement("script");
    scriptEl.src = src;
    scriptEl.type = "text/javascript";
    document.getElementsByTagName("head")[0].appendChild(scriptEl);
    scriptEl.addEventListener("load", () => {
      resolve();
    });
  });
}
</script>
