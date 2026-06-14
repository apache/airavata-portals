<template>
  <nav class="flex flex-wrap items-center gap-1 text-sm">
    <template v-for="(item, index) in items" :key="item.path">
      <ChevronRight
        v-if="index > 0"
        class="size-3.5 text-muted-foreground"
        aria-hidden="true"
      />
      <span v-if="item.active" class="text-muted-foreground">{{
        item.text
      }}</span>
      <a
        v-else
        href="#"
        class="text-primary"
        @click.prevent="directorySelected(item.path)"
        >{{ item.text }}</a
      >
    </template>
  </nav>
</template>

<script>
import { ChevronRight } from "@lucide/vue";

export default {
  name: "storage-path-breadcrumb",
  components: { ChevronRight },
  props: {
    parts: {
      type: Array,
      required: true,
    },
    rootName: {
      type: String,
      default: "Home",
    },
  },
  computed: {
    items() {
      const subparts = [];
      const partsItems = this.parts.map((part, index) => {
        subparts.push(part);
        return {
          text: part,
          path: subparts.join("/"),
          active: index === this.parts.length - 1,
        };
      });
      return [
        { text: this.rootName, path: "", active: this.parts.length === 0 },
      ].concat(partsItems);
    },
  },
  methods: {
    directorySelected(path) {
      this.$emit("directory-selected", path);
    },
  },
};
</script>
