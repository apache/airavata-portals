<template>
  <div>
    <div>
      <h2 class="mb-4 text-lg font-semibold">
        Gateway Resource Profile - {{ data.gateway_id }}
      </h2>
      <div class="space-y-1.5">
        <Label for="default-credential-store-token"
          >Default SSH Credential</Label
        >
        <ssh-credential-selector
          id="default-credential-store-token"
          v-model="data.credential_store_token"
          :readonly="!data.user_has_write_access"
        />
        <p class="text-sm text-muted-foreground">
          This is the default SSH credential that will be used for storage
          preferences that don't specify their own SSH credential.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { mixins } from "django-airavata-common-ui";
import SSHCredentialSelector from "../credentials/SSHCredentialSelector.vue";

export default {
  name: "gateway-resource-profile-editor",
  mixins: [mixins.VModelMixin],
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
};
</script>
