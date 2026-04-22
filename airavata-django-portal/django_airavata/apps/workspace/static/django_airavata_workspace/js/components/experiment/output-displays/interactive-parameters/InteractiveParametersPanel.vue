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

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import InteractiveParameterWidgetContainer from "./InteractiveParameterWidgetContainer.vue";
import { components } from "django-airavata-common-ui";

const ValidatedForm = components.ValidatedForm;

type Parameter = Record<string, unknown>;

const props = defineProps<{
  parameters: Parameter[];
}>();

const emit = defineEmits<{
  input: [parameters: Parameter[]];
}>();

const validatedForm = ref<InstanceType<typeof ValidatedForm> | null>(null);

function parametersCopy(): Parameter[] {
  return JSON.parse(JSON.stringify(props.parameters)) as Parameter[];
}

const localParameters = ref<Parameter[]>(parametersCopy());

const formItems = computed(() =>
  localParameters.value.map((p) => ({
    key: p.name,
    label: p.label || p.name,
    item: p,
    description: p.help,
  })),
);

const valid = computed(() => (validatedForm.value as unknown as { valid: boolean } | null)?.valid ?? false);

watch(
  () => props.parameters,
  () => {
    localParameters.value = parametersCopy();
  },
);

function updated(param: Parameter, value: unknown) {
  const i = localParameters.value.findIndex((x) => x.name === param.name);
  (localParameters.value[i] as Record<string, unknown>).value = value;
  emit("input", localParameters.value);
}

defineExpose({ valid });
</script>
