<template>
  <div
    ref="host"
    class="code-editor"
    :class="{ 'code-editor--readonly': readOnly }"
  />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { EditorView, keymap, lineNumbers as cmLineNumbers } from "@codemirror/view";
import { EditorState, type Extension } from "@codemirror/state";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";

const LANGS: Record<string, () => Extension> = { javascript, python, markdown };

const props = withDefaults(defineProps<{
  modelValue?: string;
  language?: string | null;
  theme?: string;
  readOnly?: boolean;
  lineNumbers?: boolean;
}>(), {
  modelValue: "",
  language: null,
  theme: "default",
  readOnly: false,
  lineNumbers: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const host = ref<HTMLElement | null>(null);
let view: EditorView | null = null;

onMounted(() => {
  const exts = [history(), keymap.of([...defaultKeymap, ...historyKeymap])];
  if (props.lineNumbers) exts.push(cmLineNumbers());
  if (props.language && LANGS[props.language]) exts.push(LANGS[props.language]());
  if (props.theme === "dark") exts.push(oneDark);
  if (props.readOnly) exts.push(EditorState.readOnly.of(true));
  exts.push(
    EditorView.updateListener.of((u) => {
      if (u.docChanged) emit("update:modelValue", u.state.doc.toString());
    }),
  );
  view = new EditorView({
    doc: props.modelValue,
    extensions: exts,
    parent: host.value!,
  });
});

onBeforeUnmount(() => {
  view?.destroy();
  view = null;
});

watch(
  () => props.modelValue,
  (next) => {
    const current = view?.state.doc.toString();
    if (next !== current && view && current !== undefined) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: next },
      });
    }
  },
);
</script>

<style scoped>
.code-editor {
  border: 1px solid var(--bs-border-color, #ced4da);
  border-radius: 4px;
}
.code-editor--readonly {
  background: #f8f9fa;
}
</style>
