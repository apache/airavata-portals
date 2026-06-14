<template>
  <div style="display: inline-block;">
    <a
      href="#"
      ref="copyLink"
      class="action-link"
      :class="linkClasses"
      @click.prevent="onCopy"
    >
      <slot>
        Copy Key
      </slot>
      <slot name="icon">
        <i class="far fa-clipboard"></i>
      </slot>
    </a>
    <b-tooltip :show="show" :disabled="!show" :target="() => $refs.copyLink">
      <slot name="tooltip">Copied!</slot>
    </b-tooltip>
  </div>
</template>

<script>
export default {
  name: "clipboard-copy-link",
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
      } catch (e) {
        // Clipboard write can fail (permissions / insecure context); ignore.
      }
    },
  },
};
</script>
