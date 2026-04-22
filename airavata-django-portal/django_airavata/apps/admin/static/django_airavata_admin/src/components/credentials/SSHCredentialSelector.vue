<template>
  <div>
    <div class="input-group">
      <select v-model="data" class="form-select" :disabled="readonly">
        <option v-if="nullOption" :value="null" :disabled="nullOptionDisabled">
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
        title="Copy public key"
        @click="copyPublicKey"
      >
        <i class="far fa-clipboard"></i>
      </button>
      <button
        v-if="!readonly"
        type="button"
        class="btn btn-outline-secondary"
        title="Create new SSH credential"
        @click="showNewSSHCredentialModal"
      >
        <i class="fa fa-plus"></i>
      </button>
    </div>
    <new-ssh-credential-modal ref="newSSHCredentialModal" @new="createSSHCredential" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { services } from "django-airavata-api";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";

// TODO: disable if the 'value' is not in the list of loaded credentials?
// Because it would mean that the user doesn't have access to this credential.
// Maybe display 'You don't have access to this credential'.

interface CredentialSummary {
  token: string;
  username: string;
  description?: string;
  public_key?: string;
}

const props = defineProps<{
  modelValue: string | null;
  nullOption?: boolean;
  // This is the default credential token that will be used if the null option is selected
  nullOptionDefaultCredentialToken?: string;
  nullOptionDisabled?: boolean;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
}>();

const newSSHCredentialModal = ref<InstanceType<typeof NewSSHCredentialModal> | null>(null);
const credentials = ref<CredentialSummary[] | null>(null);
const data = ref<string | null>(props.modelValue);

watch(
  () => props.modelValue,
  (newValue) => {
    data.value = newValue;
  },
);

watch(data, (newValue) => {
  emit("update:modelValue", newValue);
});

const credentialStoreTokenOptions = computed(() => {
  const options = credentials.value
    ? credentials.value.map((summary) => ({
        value: summary.token,
        text: createCredentialDescription(summary),
      }))
    : [];
  options.sort((a, b) => a.text.toLowerCase().localeCompare(b.text.toLowerCase()));
  return options;
});

const selectedCredential = computed(() =>
  credentials.value ? credentials.value.find((cred) => cred.token === data.value) : null,
);

const defaultCredentialSummary = computed(() =>
  props.nullOptionDefaultCredentialToken && credentials.value
    ? credentials.value.find((cred) => cred.token === props.nullOptionDefaultCredentialToken)
    : null,
);

const copySSHPublicKeyText = computed(() =>
  selectedCredential.value
    ? selectedCredential.value.public_key?.trim() ?? null
    : defaultCredentialSummary.value
      ? defaultCredentialSummary.value.public_key?.trim() ?? null
      : null,
);

onMounted(() => {
  if (!credentials.value) {
    services.CredentialSummaryService.allSSHCredentials().then(
      (creds: CredentialSummary[]) => (credentials.value = creds),
    );
  }
});

function showNewSSHCredentialModal() {
  newSSHCredentialModal.value?.show();
}

async function copyPublicKey() {
  if (!copySSHPublicKeyText.value) return;
  try {
    await navigator.clipboard.writeText(copySSHPublicKeyText.value);
  } catch (e) {
    // Fallback
    const ta = document.createElement("textarea");
    ta.value = copySSHPublicKeyText.value;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
}

function createSSHCredential(credData: { description: string }) {
  services.CredentialSummaryService.createSSH({ data: credData }).then(
    (cred: CredentialSummary) => {
      credentials.value?.push(cred);
      data.value = cred.token;
    },
  );
}

function createCredentialDescription(summary: CredentialSummary) {
  return (
    summary.username +
    " - " +
    (summary.description ? summary.description : `No description (${summary.token})`)
  );
}
</script>
