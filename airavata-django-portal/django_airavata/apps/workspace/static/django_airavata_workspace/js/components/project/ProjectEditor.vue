<template>
  <div>
    <div class="d-flex">
      <slot name="title">
        <h1 class="h4 mb-4 me-auto">Edit Project</h1>
      </slot>
      <slot name="buttons"> </slot>
    </div>
    <form novalidate @submit.prevent="onSubmit" @input="onUserInput">
      <div class="mb-3">
        <label for="project-name" class="form-label"
          >Project Name <span class="text-danger">*</span></label
        >
        <input
          id="project-name"
          v-model="data.name"
          class="form-control"
          :class="{ 'is-invalid': userBeginsInput && nameState === false }"
          type="text"
          required
          placeholder="Project name"
        />
        <div v-if="userBeginsInput && nameFeedback" class="invalid-feedback">
          {{ nameFeedback }}
        </div>
      </div>
      <div class="mb-3">
        <label for="project-description" class="form-label">Description</label>
        <textarea
          id="project-description"
          v-model="data.description"
          class="form-control"
          placeholder="Optional description"
          rows="3"
        ></textarea>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models } from "django-airavata-api";

type Project = InstanceType<typeof models.Project>;

const props = defineProps<{
  modelValue: Project;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: Project];
  valid: [];
  invalid: [];
  save: [];
}>();

// VModelMixin pattern: local copy, emits on change, updates when prop changes
const data = ref<Project>(props.modelValue.clone());

watch(
  () => props.modelValue,
  (newVal) => {
    data.value = newVal.clone();
    validate();
  },
  { deep: true },
);

watch(
  data,
  (newVal, oldVal) => {
    // Only emit for objects when deep property changes (same ref)
    if (newVal === oldVal) {
      emit("update:modelValue", newVal);
    }
    validate();
  },
  { deep: true },
);

const userBeginsInput = ref(false);

const validation = computed(() => {
  const v = (data.value as unknown as { validate(): Record<string, string[]> }).validate();
  return v ? v : {};
});

const nameFeedback = computed(() => {
  if (userBeginsInput.value && validation.value.name) {
    return validation.value.name.join("; ");
  }
  return null;
});

const nameState = computed<boolean | null>(() => {
  if (validation.value.name) {
    return userBeginsInput.value ? false : null;
  }
  return true;
});

function validate() {
  if (Object.keys(validation.value).length > 0) {
    emit("invalid");
  } else {
    emit("valid");
  }
}

function onUserInput() {
  userBeginsInput.value = true;
}

function onSubmit() {
  emit("save");
}

function reset() {
  userBeginsInput.value = false;
}

onMounted(() => {
  validate();
});

defineExpose({ reset });
</script>
