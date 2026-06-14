<template>
  <Tooltip :open="show">
    <TooltipTrigger as-child>
      <Button :variant="variant" :disabled="disabled" @click="onCopy">
        <slot></slot>
        <slot name="icon">
          <Clipboard class="size-4" />
        </slot>
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      <slot name="tooltip">Copied!</slot>
    </TooltipContent>
  </Tooltip>
</template>

<script>
import { Clipboard } from "@lucide/vue";

export default {
  name: "clipboard-copy-button",
  components: { Clipboard },
  props: {
    text: {
      type: String,
    },
    variant: {
      type: String,
      default: "secondary",
    },
  },
  data() {
    return {
      show: false,
    };
  },
  computed: {
    disabled() {
      return !this.text;
    },
  },
  methods: {
    async onCopy() {
      try {
        await navigator.clipboard.writeText(this.text);
        this.show = true;
        setTimeout(() => (this.show = false), 2000);
      } catch {
        // Clipboard write can fail (permissions / insecure context); ignore.
      }
    },
  },
};
</script>
