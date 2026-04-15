<template>
  <div>
    <div class="input-group">
      <select class="form-select"
        v-model="data"
        :disabled="readonly"
      >
        <option
          v-if="nullOption"
          :value="null"
          :disabled="nullOptionDisabled"
        >
          <template v-if="defaultCredentialSummary">
            Use the default SSH credential ({{
              createCredentialDescription(defaultCredentialSummary)
            }})
          </template>
          <template v-else>Unset the default SSH credential</template>
        </option>
        <option
          v-for="option in credentialStoreTokenOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.text }}
        </option>
      </select>
      <button
        type="button"
        class="btn btn-outline-secondary"
        :disabled="!copySSHPublicKeyText"
        @click="copyPublicKey"
        title="Copy public key"
      >
        <i class="far fa-clipboard"></i>
      </button>
      <button
        type="button"
        class="btn btn-outline-secondary"
        v-if="!readonly"
        @click="showNewSSHCredentialModal"
        title="Create new SSH credential"
      >
        <i class="fa fa-plus"></i>
      </button>
    </div>
    <new-ssh-credential-modal
      ref="newSSHCredentialModal"
      @new="createSSHCredential"
    />
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";

export default {
  // TODO: disable if the 'value' is not in the list of loaded credentials?
  // Because it would mean that the user doesn't have access to this credential.
  // Maybe display 'You don't have access to this credential'.
  name: "ssh-credential-selector",
  props: {
    nullOption: {
      type: Boolean,
      default: true,
    },
    // This is the default credential token that will be used if the null option is selected
    nullOptionDefaultCredentialToken: {
      type: String,
    },
    nullOptionDisabled: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  mixins: [mixins.VModelMixin],
  components: {
    "new-ssh-credential-modal": NewSSHCredentialModal,
  },
  data() {
    return {
      credentials: null,
    };
  },
  computed: {
    credentialStoreTokenOptions() {
      const options = this.credentials
        ? this.credentials.map((summary) => {
            return {
              value: summary.token,
              text: this.createCredentialDescription(summary),
            };
          })
        : [];
      options.sort((a, b) =>
        a.text.toLowerCase().localeCompare(b.text.toLowerCase())
      );
      return options;
    },
    selectedCredential() {
      return this.credentials
        ? this.credentials.find((cred) => cred.token === this.data)
        : null;
    },
    defaultCredentialSummary() {
      return this.nullOptionDefaultCredentialToken && this.credentials
        ? this.credentials.find(
            (cred) => cred.token === this.nullOptionDefaultCredentialToken
          )
        : null;
    },
    copySSHPublicKeyText() {
      return this.selectedCredential
        ? this.selectedCredential.public_key.trim()
        : this.defaultCredentialSummary
        ? this.defaultCredentialSummary.public_key.trim()
        : null;
    },
  },
  methods: {
    showNewSSHCredentialModal() {
      this.$refs.newSSHCredentialModal.show();
    },
    async copyPublicKey() {
      if (!this.copySSHPublicKeyText) return;
      try {
        await navigator.clipboard.writeText(this.copySSHPublicKeyText);
      } catch (e) {
        // Fallback
        const ta = document.createElement("textarea");
        ta.value = this.copySSHPublicKeyText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
    },
    createSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data: data }).then(
        (cred) => {
          this.credentials.push(cred);
          this.data = cred.token;
        }
      );
    },
    createCredentialDescription(summary) {
      return (
        summary.username +
        " - " +
        (summary.description
          ? summary.description
          : `No description (${summary.token})`)
      );
    },
  },
  created() {
    if (!this.credentials) {
      services.CredentialSummaryService.allSSHCredentials().then(
        (creds) => (this.credentials = creds)
      );
    }
  },
};
</script>
