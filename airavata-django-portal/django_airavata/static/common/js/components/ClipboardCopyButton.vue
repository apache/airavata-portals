<template>
  <button
    ref="copyButton"
    :class="['btn', 'btn-' + variant]"
    :disabled="disabled"
    :data-clipboard-text="text"
  >
    <slot></slot>
    <slot name="icon">
      <i class="far fa-clipboard"></i>
    </slot>
    <div class="tooltip" :show="show" :disabled="!show" :target="() => $refs.copyButton">
      <slot name="tooltip">Copied!</slot>
    </div>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import ClipboardJS from "clipboard";

const props = withDefaults(defineProps<{
  text?: string;
  variant?: string;
}>(), {
  text: undefined,
  variant: "secondary",
});

const copyButton = ref<HTMLElement | null>(null);
const show = ref(false);
let clipboard: ClipboardJS | null = null;

const disabled = computed(() => !props.text);

onMounted(() => {
  if (copyButton.value) {
    clipboard = new ClipboardJS(copyButton.value);
    clipboard.on("success", onCopySuccess);
  }
});

onBeforeUnmount(() => {
  clipboard?.destroy();
  clipboard = null;
});

function onCopySuccess(): void {
  show.value = true;
  setTimeout(() => (show.value = false), 2000);
}
</script>
