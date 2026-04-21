<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">SSH Credentials</h1>
        <p class="text-muted mb-0">
          Manage SSH key pairs for accessing compute and storage resources.
        </p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary btn-sm me-1" @click="showNewSSHCredentialModal">
          <i class="fa fa-plus me-1"></i>Create New
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <table class="table table-hover table-sm">
          <thead>
            <tr>
              <th>Description</th>
              <th class="text-nowrap">User</th>
              <th class="text-nowrap">Created</th>
              <th class="text-nowrap" style="width: 1%">Actions</th>
            </tr>
          </thead>
          <tbody class="align-middle">
            <tr v-if="sshKeys.length === 0">
              <td colspan="4">
                <div class="table-empty">
                  <i class="fa fa-key table-empty__icon"></i>
                  <div class="table-empty__title">No SSH credentials</div>
                  <div class="table-empty__text">
                    Add an SSH key pair using the <strong>Create New</strong> button above.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="cred in sshKeys" :key="cred.token">
              <td>
                <i class="fa fa-key me-2 text-muted"></i
                ><strong>{{ cred.description || "-" }}</strong>
              </td>
              <td>
                <span class="fw-medium">{{ cred.username }}</span>
                <span v-if="cred.username === currentUsername" class="badge bg-secondary ms-1"
                  >You</span
                >
                <span v-else-if="isAdminUser(cred.username)" class="badge bg-primary ms-1"
                  >Admin</span
                >
              </td>
              <td class="text-nowrap"><human-date :date="cred.persisted_time" /></td>
              <td class="text-nowrap" style="width: 1%">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <clipboard-copy-link :text="(cred.public_key || '').trim()" />
                  <share-button
                    :entity-id="cred.token"
                    :disallow-editing-admin-groups="false"
                    :auto-add-admin-groups="false"
                  />
                  <delete-link
                    v-if="cred.user_has_write_access"
                    @delete="deleteSSHCredential(cred)"
                  >
                    Are you sure you want to delete <strong>{{ cred.description }}</strong
                    >?
                  </delete-link>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-if="sshKeys.length > 0"
          class="text-end text-muted"
          style="font-size: 0.75rem; padding: 6px 8px"
        >
          Showing {{ sshKeys.length }}
        </div>
      </div>
    </div>

    <new-ssh-credential-modal ref="newSSHCredentialModal" @new="createNewSSHCredential" />
  </div>
</template>

<script>
import { services, session } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";

export default {
  components: {
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    "clipboard-copy-link": components.ClipboardCopyLink,
    "new-ssh-credential-modal": NewSSHCredentialModal,
    "share-button": components.ShareButton,
  },
  data() {
    return {
      sshKeys: [],
      currentUsername: session.Session.username,
    };
  },
  created() {
    this.fetchSSHKeys();
  },
  methods: {
    isAdminUser(username) {
      return username === "default-admin" || username === "admin";
    },
    fetchSSHKeys() {
      services.CredentialSummaryService.allSSHCredentials().then((creds) => (this.sshKeys = creds));
    },
    showNewSSHCredentialModal() {
      this.$refs.newSSHCredentialModal.show();
    },
    createNewSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data }).then(() => this.fetchSSHKeys());
    },
    deleteSSHCredential(cred) {
      services.CredentialSummaryService.delete({ lookup: cred.token }).then(() =>
        this.fetchSSHKeys(),
      );
    },
  },
};
</script>
