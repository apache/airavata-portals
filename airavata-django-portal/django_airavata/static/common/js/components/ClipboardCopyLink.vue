<template>
  <div style="display: inline-block;">
    <button
      type="button"
      ref="copyLink"
      :data-clipboard-text="text"
      class="btn btn-outline-primary btn-pill"
      :class="linkClasses"
    >
      <slot name="icon">
        <i class="far fa-clipboard me-1"></i>
      </slot>
      <slot>
        Copy Key
      </slot>
    </button>
    <div v-if="show" class="tooltip show position-absolute" role="tooltip">
      <slot name="tooltip">Copied!</slot>
    </div>
  </div>
</template>

<script>
import ClipboardJS from "clipboard";

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
  mounted() {
    let clipboard = new ClipboardJS(this.$refs.copyLink);
    clipboard.on("success", this.onCopySuccess);
  },
  beforeDestroy() {
    let clipboard = new ClipboardJS(this.$refs.copyLink);
    clipboard.destroy();
  },
  methods: {
    onCopySuccess() {
      this.show = true;
      setTimeout(() => (this.show = false), 2000);
    },
  },
};
</script>

