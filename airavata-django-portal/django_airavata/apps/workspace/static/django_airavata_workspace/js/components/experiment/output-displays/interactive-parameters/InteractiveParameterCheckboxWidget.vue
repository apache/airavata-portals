<template>
  <div class="form-check">
    <input
      class="form-check-input"
      type="checkbox"
      :checked="value"
      @input="$emit('input', $event)"
    />
  </div>
</template>

<script>
export default {
  name: "InteractiveParameterCheckboxWidget",
  props: {
    value: {
      type: Boolean,
      required: true,
    },
  },
};
</script>
