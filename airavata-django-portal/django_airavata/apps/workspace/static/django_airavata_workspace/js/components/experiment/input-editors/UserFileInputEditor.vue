<template>
  <div>
    <select
      :id="id"
      v-model="data"
      class="form-select"
      style="width: auto"
      :state="componentValidState"
      @input="valueChanged"
    >
      <option v-for="userfile in userfiles" :key="userfile.file_dpu" :value="userfile.file_dpu">
        {{ userfile.file_name }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeMount } from "vue";
import { models, utils as apiUtils } from "django-airavata-api";
import { useInputEditor } from "@/composables/useInputEditor";

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;

interface UserFile {
  file_dpu: string;
  file_name: string;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
}>();

const { data, componentValidState, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const userfiles = ref<UserFile[]>([]);

onBeforeMount(() => {
  // loads the list of file entries in django UserFiles model
  apiUtils.FetchUtils.get("/api/get-ufiles").then(
    (res: { "user-files": UserFile[] }) => (userfiles.value = res["user-files"]),
  );
});
</script>

<style scoped></style>
