<script setup lang="ts">
/* eslint-disable vue/multi-word-component-names */
// Linkify is a renderless component that processes slot content.
// The render function must live in the Options API block below.
</script>

<script lang="ts">
import { h, type VNode } from "vue";
import * as linkify from "linkifyjs";

function clickHandler(e: Event): void {
  // stop click event from bubbling up
  e.stopPropagation();
}

export default {
  render() {
    // Find top level text nodes and run linkify on the text, converting them
    // into an array of links and text nodes
    const defaultSlot: VNode[] = this.$slots.default ? this.$slots.default() : [];
    const children = defaultSlot
      .flatMap((node) => {
        // In Vue 3, text VNodes have children as a string
        const text = typeof node.children === "string" ? node.children : null;
        if (text) {
          const tokens = linkify.tokenize(text);
          return tokens.map((t) => {
            if (t.isLink) {
              return h(
                "a",
                { href: t.toHref("https"), target: "_blank", onClick: clickHandler },
                t.toString(),
              );
            } else {
              return t.toString();
            }
          });
        } else {
          return [node];
        }
      });
    return h("span", {}, children);
  },
};
</script>
