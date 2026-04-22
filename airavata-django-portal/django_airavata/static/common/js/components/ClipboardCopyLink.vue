<template>
  <div style="display: inline-block">
    <button
      ref="copyLink"
      type="button"
      :data-clipboard-text="text"
      class="btn btn-outline-primary btn-pill"
      :class="linkClasses"
    >
      <slot name="icon">
        <i class="far fa-clipboard me-1"></i>
      </slot>
      <slot> Copy Key </slot>
    </button>
    <div v-if="show" class="tooltip show position-absolute" role="tooltip">
      <slot name="tooltip">Copied!</slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import ClipboardJS from "clipboard";

defineProps<{
  text: string;
  linkClasses?: string[];
}>();

const copyLink = ref<HTMLElement | null>(null);
const show = ref(false);
let clipboard: ClipboardJS | null = null;

onMounted(() => {
  if (copyLink.value) {
    clipboard = new ClipboardJS(copyLink.value);
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
