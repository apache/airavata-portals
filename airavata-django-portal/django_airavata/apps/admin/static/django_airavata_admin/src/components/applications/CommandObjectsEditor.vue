<template>
  <div class="card" :title="title" title-tag="h5">
    <div v-for="commandObject in data" :key="commandObject.key" class="input-group mb-1">
      <input
        ref="commandObjectInputs"
        v-model="commandObject.command"
        class="form-control"
        type="text"
        required
        :disabled="readonly"
      />
      <span class="input-group-text">
        <button class="btn btn-secondary btn-sm" @click="deleteCommandObject(commandObject)">
          <i class="fa fa-trash"></i>
          <span class="visually-hidden">Delete</span>
        </button>
      </span>
    </div>
    <button v-if="!readonly" class="btn btn-secondary btn-sm" @click="addCommandObject">
      {{ addButtonLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { models } from "django-airavata-api";

type CommandObject = InstanceType<typeof models.CommandObject>;

const props = defineProps<{
  modelValue: CommandObject[] | null;
  title: string;
  addButtonLabel: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: CommandObject[]];
}>();

const commandObjectInputs = ref<HTMLInputElement[]>([]);

// Local reactive copy
const data = ref<CommandObject[]>(
  props.modelValue ? props.modelValue.map((item) => item.clone() as CommandObject) : [],
);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue ? newValue.map((item) => item.clone() as CommandObject) : [];
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

function addCommandObject() {
  if (!data.value) {
    data.value = [];
  }
  data.value.push(new models.CommandObject());
  nextTick(() => {
    const inputs = commandObjectInputs.value;
    if (inputs && inputs.length > 0) {
      inputs[inputs.length - 1].focus();
    }
  });
}

function deleteCommandObject(commandObject: CommandObject) {
  const index = data.value.findIndex((cmd) => (cmd as CommandObject).key === commandObject.key);
  data.value.splice(index, 1);
}
</script>
