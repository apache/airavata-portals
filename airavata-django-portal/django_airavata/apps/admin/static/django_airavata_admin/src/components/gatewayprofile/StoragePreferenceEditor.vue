<template>
  <div>
    <div class="mb-3" label="Login username" label-for="login-username">
      <input class="form-control"
        id="login-username"
        v-model="data.login_user_name"
        type="text"
      />
    </div>
    <form-group
      label="File System Root Location"
      label-for="filesystem-root-location"
    >
      <input class="form-control"
        id="filesystem-root-location"
        v-model="data.file_system_root_location"
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
        <template slot="null-option-label" slot-scope="nullOptionLabelScope">
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
  name: "storage-preference-editor",
  mixins: [mixins.VModelMixin],
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
  props: {
    defaultCredentialStoreToken: {
      type: String,
      required: true,
    },
  },
};
</script>
