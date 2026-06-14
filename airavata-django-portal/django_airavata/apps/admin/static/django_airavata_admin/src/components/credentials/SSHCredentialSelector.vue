<template>
  <div>
    <div class="flex items-stretch gap-0">
      <select
        v-model="data"
        :disabled="readonly"
        class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full min-w-0 flex-1 rounded-l-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option v-if="nullOption" :value="null" :disabled="nullOptionDisabled">
          <slot
            name="null-option-label"
            :defaultCredentialSummary="defaultCredentialSummary"
          >
            <span v-if="defaultCredentialSummary">
              Use the default SSH credential ({{
                createCredentialDescription(defaultCredentialSummary)
              }})
            </span>
            <span v-else> Unset the default SSH credential </span>
          </slot>
        </option>
        <option
          v-for="opt in credentialStoreTokenOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.text }}
        </option>
      </select>
      <clipboard-copy-button
        variant="secondary"
        :text="copySSHPublicKeyText"
        class="rounded-none border-l-0"
      >
      </clipboard-copy-button>
      <Button
        v-if="!readonly"
        variant="secondary"
        class="rounded-l-none"
        @click="showNewSSHCredentialModal"
      >
        <Plus class="size-4" />
      </Button>
    </div>
    <new-ssh-credential-modal
      ref="newSSHCredentialModal"
      @new="createSSHCredential"
    />
  </div>
</template>

<script>
import { Plus } from "@lucide/vue";
import { services } from "django-airavata-api";
import { components, mixins } from "django-airavata-common-ui";
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
    Plus,
    "clipboard-copy-button": components.ClipboardCopyButton,
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
        a.text.toLowerCase().localeCompare(b.text.toLowerCase()),
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
            (cred) => cred.token === this.nullOptionDefaultCredentialToken,
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
    createSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data: data }).then(
        (cred) => {
          this.credentials.push(cred);
          this.data = cred.token;
        },
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
        (creds) => (this.credentials = creds),
      );
    }
  },
};
</script>
