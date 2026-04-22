<template>
  <compoment
    :is="widgetComponent"
    :value="parameter.value"
    :parameter="parameter"
    @input="$emit('input', $event)"
    @valid="$emit('valid')"
    @invalid="$emit('invalid', $event)"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import InteractiveParameterCheckboxWidget from "./InteractiveParameterCheckboxWidget.vue";
import InteractiveParameterRangeWidget from "./InteractiveParameterRangeWidget.vue";
import InteractiveParameterSelectWidget from "./InteractiveParameterSelectWidget.vue";
import InteractiveParameterStepperWidget from "./InteractiveParameterStepperWidget.vue";
import InteractiveParameterTextInputWidget from "./InteractiveParameterTextInputWidget.vue";

const props = defineProps<{
  parameter: Record<string, unknown>;
}>();

defineEmits<{
  input: [value: unknown];
  valid: [];
  invalid: [message: string];
}>();

const widgetComponent = computed(() => {
  if (props.parameter.options) {
    return InteractiveParameterSelectWidget;
  } else if (
    props.parameter.type === "boolean" ||
    (props.parameter.widget && props.parameter.widget === "checkbox")
  ) {
    return InteractiveParameterCheckboxWidget;
  } else if (
    props.parameter.type === "string" ||
    (props.parameter.widget && props.parameter.widget === "textinput")
  ) {
    return InteractiveParameterTextInputWidget;
  } else if (
    (props.parameter.type === "float" || props.parameter.type === "integer") &&
    "min" in props.parameter &&
    "max" in props.parameter
  ) {
    return InteractiveParameterRangeWidget;
  } else if (
    props.parameter.type === "float" ||
    props.parameter.type === "integer" ||
    (props.parameter.widget && props.parameter.widget === "stepper")
  ) {
    return InteractiveParameterStepperWidget;
  } else {
    return null;
  }
});
</script>
