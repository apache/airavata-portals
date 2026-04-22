<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Application Details</h1>
        <form-group
          label="Application Name"
          label-for="application-name"
          :invalid-feedback="validationFeedback.appModuleName.invalidFeedback"
          :state="validationFeedback.appModuleName.state"
        >
          <input
            id="application-name"
            v-model="data.appModuleName"
            class="form-control"
            type="text"
            required
            :disabled="readonly"
            :state="validationFeedback.appModuleName.state"
          />
        </form-group>
        <form-group label="Application Version" label-for="application-version">
          <input
            id="application-version"
            v-model="data.appModuleVersion"
            class="form-control"
            type="text"
            :disabled="readonly"
          />
        </form-group>
        <form-group label="Application Description" label-for="application-description">
          <textarea
            id="application-description"
            v-model="data.appModuleDescription"
            class="form-control"
            :rows="3"
            :disabled="readonly"
          ></textarea>
        </form-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { models } from "django-airavata-api";
import { errors } from "django-airavata-common-ui";

type ApplicationModule = InstanceType<typeof models.ApplicationModule>;

const props = defineProps<{
  modelValue: ApplicationModule;
  readonly?: boolean;
  validationErrors?: Record<string, unknown> | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: ApplicationModule];
}>();

const data = ref<ApplicationModule>(
  props.modelValue.clone() as ApplicationModule,
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue.clone() as ApplicationModule;
  },
  { deep: true },
);

watch(
  data,
  (newValue, oldValue) => {
    if (newValue === oldValue) {
      emit("update:modelValue", newValue);
    }
  },
  { deep: true },
);

const validationFeedback = computed(() =>
  errors.ValidationErrors.createValidationFeedback(data.value, props.validationErrors),
);

</script>
