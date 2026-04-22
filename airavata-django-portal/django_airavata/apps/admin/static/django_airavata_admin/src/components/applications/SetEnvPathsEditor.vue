<template>
  <div class="card" :title="title" title-tag="h5">
    <div
      v-for="setEnvPath in data"
      :key="setEnvPath.key"
      class="input-group mb-1 align-items-center"
    >
      <input
        ref="nameInputs"
        v-model="setEnvPath.name"
        class="form-control"
        type="text"
        required
        placeholder="NAME"
        :disabled="readonly"
      />
      <i class="fa fa-equals mx-1"></i>
      <input
        v-model="setEnvPath.value"
        class="form-control"
        type="text"
        required
        placeholder="VALUE"
        :disabled="readonly"
      />
      <span class="input-group-text">
        <button class="btn btn-secondary btn-sm" @click="deleteEnvPath(setEnvPath)">
          <i class="fa fa-trash"></i>
          <span class="visually-hidden">Delete</span>
        </button>
      </span>
    </div>
    <button v-if="!readonly" class="btn btn-secondary btn-sm" @click="addEnvPath">
      {{ addButtonLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { models } from "django-airavata-api";

type SetEnvPaths = InstanceType<typeof models.SetEnvPaths>;

const props = defineProps<{
  modelValue: SetEnvPaths[] | null;
  title: string;
  addButtonLabel: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: SetEnvPaths[]];
}>();

const nameInputs = ref<HTMLInputElement[]>([]);

const data = ref<SetEnvPaths[]>(
  props.modelValue ? props.modelValue.map((item) => item.clone() as SetEnvPaths) : [],
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue ? newValue.map((item) => item.clone() as SetEnvPaths) : [];
  },
  { deep: true },
);

watch(
  data,
  (newValue) => {
    emit("update:modelValue", newValue);
  },
  { deep: true },
);

function addEnvPath() {
  if (!data.value) {
    data.value = [];
  }
  data.value.push(new models.SetEnvPaths());
  nextTick(() => {
    const inputs = nameInputs.value;
    if (inputs && inputs.length > 0) {
      inputs[inputs.length - 1].focus();
    }
  });
}

function deleteEnvPath(setEnvPath: SetEnvPaths) {
  const index = data.value.findIndex((env) => (env as SetEnvPaths).key === setEnvPath.key);
  data.value.splice(index, 1);
}
</script>
