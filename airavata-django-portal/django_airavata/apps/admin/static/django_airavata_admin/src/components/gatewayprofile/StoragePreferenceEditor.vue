<template>
  <div class="space-y-4">
    <div class="space-y-1.5">
      <Label for="login-username">Login username</Label>
      <Input id="login-username" v-model="data.login_user_name" type="text" />
    </div>
    <div class="space-y-1.5">
      <Label for="filesystem-root-location">File System Root Location</Label>
      <Input
        id="filesystem-root-location"
        v-model="data.file_system_root_location"
        type="text"
      />
    </div>
    <div class="space-y-1.5">
      <Label for="default-credential-store-token"
        >Resource Specific SSH Credential</Label
      >
      <ssh-credential-selector
        id="default-credential-store-token"
        v-model="data.resource_specific_credential_store_token"
        :null-option-default-credential-token="defaultCredentialStoreToken"
        :null-option-disabled="!defaultCredentialStoreToken"
      >
        <template v-slot:null-option-label="nullOptionLabelScope">
          <span v-if="nullOptionLabelScope.defaultCredentialSummary">
            Use the gateway's default SSH credential ({{
              nullOptionLabelScope.defaultCredentialSummary.username
            }}
            - {{ nullOptionLabelScope.defaultCredentialSummary.description }})
          </span>
          <span v-else> Select a SSH credential </span>
        </template>
      </ssh-credential-selector>
      <p class="text-sm text-muted-foreground">
        This is the SSH credential that will be used for to move data to/from
        this storage resource.
      </p>
    </div>
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
