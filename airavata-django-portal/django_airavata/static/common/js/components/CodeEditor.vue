<template>
  <div
    ref="host"
    class="code-editor"
    :class="{ 'code-editor--readonly': readOnly }"
  />
</template>

<script>
import { EditorView, keymap, lineNumbers as cmLineNumbers } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";

const LANGS = { javascript, python, markdown };

export default {
  name: "CodeEditor",
  props: {
    modelValue: { type: String, default: "" },
    language: { type: String, default: null },
    theme: { type: String, default: "default" },
    readOnly: { type: Boolean, default: false },
    lineNumbers: { type: Boolean, default: true },
  },
  emits: ["update:modelValue"],
  data() {
    return { view: null };
  },
  mounted() {
    const exts = [history(), keymap.of([...defaultKeymap, ...historyKeymap])];
    if (this.lineNumbers) exts.push(cmLineNumbers());
    if (this.language && LANGS[this.language]) exts.push(LANGS[this.language]());
    if (this.theme === "dark") exts.push(oneDark);
    if (this.readOnly) exts.push(EditorState.readOnly.of(true));
    exts.push(
      EditorView.updateListener.of((u) => {
        if (u.docChanged) this.$emit("update:modelValue", u.state.doc.toString());
      }),
    );
    this.view = new EditorView({
      doc: this.modelValue,
      extensions: exts,
      parent: this.$refs.host,
    });
  },
  beforeUnmount() {
    this.view?.destroy();
    this.view = null;
  },
  watch: {
    modelValue(next) {
      const current = this.view?.state.doc.toString();
      if (next !== current) {
        this.view.dispatch({
          changes: { from: 0, to: current.length, insert: next },
        });
      }
    },
  },
};
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
