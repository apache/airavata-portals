<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">SSH Credentials</h1>
        <p class="text-muted mb-0">Manage SSH key pairs for accessing compute and storage resources.</p>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary btn-sm me-1" @click="showNewSSHCredentialModal">
          <i class="fa fa-plus me-1"></i>Create New
        </button>
        <button class="btn btn-outline-secondary btn-sm" v-if="userIsAdmin" @click="showNewSharedSSHCredentialModel">
          <i class="fa fa-plus me-1"></i>Gateway Credential
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Description</th>
              <th>User</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="sshKeys.length === 0">
              <td colspan="4">
                <div class="table-empty">
                  <i class="fa fa-key table-empty__icon"></i>
                  <div class="table-empty__title">No SSH credentials</div>
                  <div class="table-empty__text">Add an SSH key pair using the <strong>Create New</strong> button above.</div>
                </div>
              </td>
            </tr>
            <tr v-for="cred in sshKeys" :key="cred.token">
              <td>{{ cred.description || '-' }}</td>
              <td>{{ cred.username }}</td>
              <td><human-date :date="cred.persisted_time" /></td>
              <td>
                <clipboard-copy-link :text="(cred.public_key || '').trim()" class="action-link me-2" />
                <share-button :entity-id="cred.token" :disallow-editing-admin-groups="false" :auto-add-admin-groups="false" />
                <delete-link v-if="cred.user_has_write_access" @delete="deleteSSHCredential(cred)">
                  Are you sure you want to delete <strong>{{ cred.description }}</strong>?
                </delete-link>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="sshKeys.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ sshKeys.length }}</div>
      </div>
    </div>

    <new-ssh-credential-modal ref="newSSHCredentialModal" @new="createNewSSHCredential" />
    <new-shared-ssh-credential-modal ref="newSharedSSHCredentialModal" @new="createNewSharedSSHCredential" />
  </div>
</template>

<script>
import { models, services, session } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";

export default {
  components: {
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    "clipboard-copy-link": components.ClipboardCopyLink,
    "new-ssh-credential-modal": NewSSHCredentialModal,
    "new-shared-ssh-credential-modal": NewSSHCredentialModal,
    "share-button": components.ShareButton,
  },
  created() {
    this.fetchSSHKeys();
  },
  data() {
    return {
      sshKeys: [],
      userIsAdmin: session.Session.is_gateway_admin,
      adminsGroup: null,
    };
  },
  methods: {
    fetchSSHKeys() {
      services.CredentialSummaryService.allSSHCredentials().then(
        (creds) => (this.sshKeys = creds)
      );
    },
    showNewSSHCredentialModal() {
      this.$refs.newSSHCredentialModal.show();
    },
    createNewSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data }).then(() => this.fetchSSHKeys());
    },
    deleteSSHCredential(cred) {
      services.CredentialSummaryService.delete({ lookup: cred.token }).then(() => this.fetchSSHKeys());
    },
    showNewSharedSSHCredentialModel() {
      if (!this.adminsGroup) {
        services.GroupService.list({ limit: -1 }).then((groups) => {
          this.adminsGroup = groups.filter((g) => g.is_gateway_admins_group)[0];
          this.$refs.newSharedSSHCredentialModal.show();
        });
      } else {
        this.$refs.newSharedSSHCredentialModal.show();
      }
    },
    createNewSharedSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data }).then((cred) => {
        const sharedEntity = new models.SharedEntity();
        services.UserProfileService.retrieve({ lookup: session.Session.username }).then((userProfile) => {
          sharedEntity.owner = userProfile;
          sharedEntity.is_owner = session.Session.username == sharedEntity.owner.user_id;
          sharedEntity.addGroup({
            group: this.adminsGroup,
            permissionType: models.ResourcePermissionType.MANAGE_SHARING,
          });
          services.SharedEntityService.merge({ data: sharedEntity, lookup: cred.token }).then(() => this.fetchSSHKeys());
        });
      });
    },
  },
};
</script>
