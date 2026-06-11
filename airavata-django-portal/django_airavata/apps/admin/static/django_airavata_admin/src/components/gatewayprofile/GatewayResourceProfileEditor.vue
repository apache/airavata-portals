<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Gateway Resource Profile - {{ data.gateway_id }}</h1>
        <b-form-group
          label="Default SSH Credential"
          label-for="default-credential-store-token"
          description="This is the default SSH credential that will be used for storage preferences that don't specify their own SSH credential."
        >
          <ssh-credential-selector
            id="default-credential-store-token"
            v-model="data.credential_store_token"
            :readonly="!data.user_has_write_access"
          />
        </b-form-group>
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
