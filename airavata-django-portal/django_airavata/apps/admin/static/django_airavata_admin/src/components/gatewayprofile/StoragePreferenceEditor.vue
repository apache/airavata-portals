<template>
  <div>
    <div class="mb-3" label="Login username" label-for="login-username">
      <input id="login-username" v-model="data.login_user_name" class="form-control" type="text" />
    </div>
    <form-group label="File System Root Location" label-for="filesystem-root-location">
      <input
        id="filesystem-root-location"
        v-model="data.file_system_root_location"
        class="form-control"
        type="text"
      />
    </form-group>
    <form-group
      label="Resource Specific SSH Credential"
      label-for="default-credential-store-token"
      description="This is the SSH credential that will be used for to move data to/from this storage resource."
    >
      <ssh-credential-selector
        id="default-credential-store-token"
        v-model="data.resource_specific_credential_store_token"
        :null-option-default-credential-token="defaultCredentialStoreToken"
        :null-option-disabled="!defaultCredentialStoreToken"
      >
        <template #null-option-label="nullOptionLabelScope">
          <span v-if="nullOptionLabelScope.defaultCredentialSummary">
            Use the gateway's default SSH credential ({{
              nullOptionLabelScope.defaultCredentialSummary.username
            }}
            - {{ nullOptionLabelScope.defaultCredentialSummary.description }})
          </span>
          <span v-else> Select a SSH credential </span>
        </template>
      </ssh-credential-selector>
    </form-group>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import SshCredentialSelector from "../credentials/SSHCredentialSelector.vue";

interface StoragePreference {
  login_user_name?: string;
  file_system_root_location?: string;
  resource_specific_credential_store_token?: string | null;
  [key: string]: unknown;
}

const props = defineProps<{
  modelValue: StoragePreference;
  defaultCredentialStoreToken?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: StoragePreference];
}>();

const data = ref<StoragePreference>({ ...props.modelValue });

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
