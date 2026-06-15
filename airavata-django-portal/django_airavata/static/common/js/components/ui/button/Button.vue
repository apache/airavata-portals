<script setup>
import { Primitive } from "reka-ui";
import { cn } from "@/lib/utils";
import { buttonVariants } from ".";

const props = defineProps({
  variant: { type: null, required: false },
  size: { type: null, required: false },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false, default: "button" },
  // Default to a non-submitting button, matching the prior Bootstrap-Vue
  // <b-button> default. A native <button> defaults to type="submit", so inside a
  // <form> a bare <Button @click="…"> would also submit the form on click —
  // triggering a full-page navigation and the browser's "Leave site?" unsaved-
  // changes guard before the click handler runs. Pass type="submit" explicitly
  // for real submit buttons.
  type: { type: String, required: false, default: "button" },
});
</script>

<template>
  <Primitive
    data-slot="button"
    :data-variant="variant"
    :data-size="size"
    :as="as"
    :as-child="asChild"
    :type="as === 'button' && !asChild ? type : undefined"
    :class="cn(buttonVariants({ variant, size }), props.class)"
  >
    <slot />
  </Primitive>
</template>
