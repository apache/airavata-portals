<template>
  <div></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

const props = withDefaults(defineProps<{
  dirty?: boolean;
}>(), {
  dirty: false,
});

onMounted(() => {
  window.addEventListener("beforeunload", onBeforeUnload);
});

// Vue 3 lifecycle: the Vue 2 `destroyed()` hook was renamed to
// `unmounted()`. Without this rename the listener leaks and every past
// editor instance with dirty=true keeps blocking navigation after the
// user has moved on.
onUnmounted(() => {
  window.removeEventListener("beforeunload", onBeforeUnload);
});

function onBeforeUnload(event: BeforeUnloadEvent): string | void {
  if (props.dirty) {
    event.preventDefault();
    // Have to return a message for some browsers in order to trigger popup
    // asking user if they want to leave the page. I don't think any browser
    // displays the message that we return here, but a returned message is
    // still required.
    const msg = "You have unsaved changes. Are you sure that you want to leave this page?";
    // For Chrome, set event.returnValue
    event.returnValue = msg;
    return msg;
  }
}
</script>
