<template>
  <Tooltip :open="show">
    <TooltipTrigger as-child>
      <a
        href="#"
        class="inline-flex cursor-pointer items-center gap-1 whitespace-nowrap text-primary hover:underline"
        :class="linkClasses"
        @click.prevent="onCopy"
      >
        <slot> Copy Key </slot>
        <slot name="icon">
          <Clipboard class="size-4" />
        </slot>
      </a>
    </TooltipTrigger>
    <TooltipContent>
      <slot name="tooltip">Copied!</slot>
    </TooltipContent>
  </Tooltip>
</template>

<script>
import { Clipboard } from "@lucide/vue";

export default {
  name: "clipboard-copy-link",
  components: { Clipboard },
  props: {
    text: {
      type: String,
      required: true,
    },
    linkClasses: {
      type: Array,
    },
  },
  data() {
    return {
      show: false,
    };
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
