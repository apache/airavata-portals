<template>
  <div class="card" title="Parameters">
    <validated-form ref="validatedForm" :items="formItems">
      <template #default="form">
        <interactive-parameter-widget-container
          :parameter="form.item"
          @valid="form.valid"
          @invalid="form.invalid"
          @input="updated(form.item, $event)"
        />
      </template>
    </validated-form>
  </div>
</template>

<script>
import InteractiveParameterWidgetContainer from "./InteractiveParameterWidgetContainer";
import { components } from "django-airavata-common-ui";

export default {
  name: "InteractiveParametersPanel",
  components: {
    InteractiveParameterWidgetContainer,
    "validated-form": components.ValidatedForm,
  },
  props: {
    parameters: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      localParameters: this.parametersCopy(),
    };
  },
  computed: {
    formItems() {
      return this.localParameters.map((p) => {
        return {
          key: p.name,
          label: p.label || p.name,
          item: p,
          description: p.help,
        };
      });
    },
    valid() {
      return this.$refs.validatedForm.valid;
    },
  },
  watch: {
    parameters() {
      this.localParameters = this.parametersCopy();
    },
  },
  methods: {
    updated(param, value) {
      const i = this.localParameters.findIndex((x) => x.name === param.name);
      this.localParameters[i].value = value;
      this.$emit("input", this.localParameters);
    },
    parametersCopy() {
      return JSON.parse(JSON.stringify(this.parameters));
    },
  },
};
</script>
