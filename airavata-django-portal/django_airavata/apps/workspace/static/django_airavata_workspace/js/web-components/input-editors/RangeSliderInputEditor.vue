<template>
  <range-slider-input-editor
    v-if="experimentInput"
    :id="id"
    :value="data"
    :experiment-input="experimentInput"
    :read-only="readOnly"
    :min="min"
    :max="max"
    :step="step"
    :value-format="valueFormat"
    :display-format="displayFormat"
    :delimiter="delimiter"
    @input="valueChanged"
  />
</template>

<script>
import RangeSliderInputEditor from "../../components/experiment/input-editors/RangeSliderInputEditor.vue";
import WebComponentInputEditorMixin from "./WebComponentInputEditorMixin.js";

export default {
  mixins: [WebComponentInputEditorMixin],
  props: {
    // Explicit copy props from mixin, workaround for bug, see
    // https://github.com/vuejs/vue-web-component-wrapper/issues/30#issuecomment-427350734
    // for more details
    ...WebComponentInputEditorMixin.props,
    min: {
      type: Number,
    },
    max: {
      type: Number,
    },
    step: {
      type: Number,
    },
    valueFormat: {
      type: String,
      validator(value) {
        return ["percentage"].indexOf(value) !== -1;
      },
    },
    displayFormat: {
      type: String,
      validator(value) {
        return ["percentage"].indexOf(value) !== -1;
      },
    },
    delimiter: String,
  },
  components: {
    RangeSliderInputEditor,
  },
};
</script>

<style lang="scss">
@import "../styles";
// Need to explicitly import the slider CSS because importing component scss doesn't work
// https://github.com/vuejs/vue-web-component-wrapper/issues/12
// vue-3-slider-component (Vue 3 port) ships its styles under lib/styles.
@import "vue-3-slider-component/lib/styles/style.scss";
:host {
  display: block;
}
</style>
