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

<script>
import { mixins } from "django-airavata-common-ui";
import SSHCredentialSelector from "../credentials/SSHCredentialSelector.vue";

export default {
  name: "StoragePreferenceEditor",
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
  mixins: [mixins.VModelMixin],
  props: {
    defaultCredentialStoreToken: {
      type: String,
      required: true,
    },
  },
};
</script>
