<script>
/* eslint-disable vue/multi-word-component-names */
import { h, Text } from "vue";
import * as linkify from "linkifyjs";

export default {
  name: "linkify",

  render() {
    // Find top-level plain-text vnodes and run linkify on their text, converting
    // them into an array of links and text nodes. In Vue 3 the default slot is a
    // function and text vnodes carry their content as `children` (a string).
    const slot = this.$slots.default ? this.$slots.default() : [];
    const children = slot
      .map((node) => {
        if (node.type === Text && typeof node.children === "string") {
          const tokens = linkify.tokenize(node.children);
          return tokens.map((t) => {
            if (t.isLink) {
              return h(
                "a",
                {
                  href: t.toHref("https"),
                  target: "_blank",
                  onClick: this.clickHandler,
                },
                t.toString()
              );
            } else {
              return t.toString();
            }
          });
        } else {
          return node;
        }
      })
      // Flatten array since text nodes are mapped to arrays
      .flat();
    return h("span", null, children);
  },
  methods: {
    clickHandler(e) {
      // stop click event from bubbling up
      e.stopPropagation();
    },
  },
};
</script>
