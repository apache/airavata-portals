<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Gateway Resource Profile - {{ data.gateway_id }}</h1>
        <form-group
          label="Default SSH Credential"
          label-for="default-credential-store-token"
          description="This is the default SSH credential that will be used for storage preferences that don't specify their own SSH credential."
        >
          <ssh-credential-selector
            id="default-credential-store-token"
            v-model="data.credential_store_token"
            :readonly="!data.user_has_write_access"
          />
        </form-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import SshCredentialSelector from "../credentials/SSHCredentialSelector.vue";

const props = defineProps<{
  modelValue: Record<string, unknown>;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, unknown>];
}>();

const data = ref<Record<string, unknown>>({ ...props.modelValue });

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = { ...newValue };
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
</script>
