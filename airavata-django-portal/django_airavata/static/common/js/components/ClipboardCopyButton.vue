<template>
  <b-button
    ref="copyButton"
    :variant="variant"
    :disabled="disabled"
    @click="onCopy"
  >
    <slot></slot>
    <slot name="icon">
      <i class="far fa-clipboard"></i>
    </slot>
    <b-tooltip :show="show" :disabled="!show" :target="() => $refs.copyButton">
      <slot name="tooltip">Copied!</slot>
    </b-tooltip>
  </b-button>
</template>

<script>
export default {
  name: "clipboard-copy-button",
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
      } catch (e) {
        // Clipboard write can fail (permissions / insecure context); ignore.
      }
    },
  },
};
</script>
