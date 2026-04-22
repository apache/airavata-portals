<template>
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb">
      <li
        v-for="item in items"
        :key="item.path"
        class="breadcrumb-item"
        :class="{ active: item.active }"
        @click="directorySelected(item.path)"
      >
        {{ item.text }}
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface BreadcrumbItem {
  text: string;
  path: string;
  active: boolean;
}

const props = withDefaults(
  defineProps<{
    parts: string[];
    rootName?: string;
  }>(),
  { rootName: "Home" },
);

const emit = defineEmits<{
  "directory-selected": [path: string];
}>();

const items = computed<BreadcrumbItem[]>(() => {
  const subparts: string[] = [];
  const partsItems = props.parts.map((part, index) => {
    subparts.push(part);
    return {
      text: part,
      path: subparts.join("/"),
      active: index === props.parts.length - 1,
    };
  });
  return [{ text: props.rootName, path: "", active: props.parts.length === 0 }].concat(partsItems);
});

function directorySelected(path: string) {
  emit("directory-selected", path);
}
</script>
