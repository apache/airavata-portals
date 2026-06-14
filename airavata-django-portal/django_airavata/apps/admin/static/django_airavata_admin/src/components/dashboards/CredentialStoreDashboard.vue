<template>
  <div>
    <list-layout
      @add-new-item="showNewSSHCredentialModal"
      :items="sshKeys"
      title="SSH Credentials"
      new-item-button-text="New SSH Credential"
    >
      <template v-slot:additional-buttons>
        <span>
          <Button
            v-if="userIsAdmin"
            variant="outline"
            @click="showNewSharedSSHCredentialModel"
          >
            New Gateway SSH Credential
            <Plus class="size-4" aria-hidden="true" />
          </Button>
        </span>
      </template>
      <template v-slot:item-list="slotProps">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead v-for="field in fields" :key="field.key">
                {{ field.label }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="item in slotProps.items" :key="item.token">
              <TableCell>{{ item.description }}</TableCell>
              <TableCell>{{ item.username }}</TableCell>
              <TableCell><human-date :date="item.persisted_time" /></TableCell>
              <TableCell>
                <share-button
                  :entity-id="item.token"
                  :disallow-editing-admin-groups="false"
                  :auto-add-admin-groups="false"
                />
              </TableCell>
              <TableCell>
                <clipboard-copy-link
                  :text="item.public_key.trim()"
                  class="mr-1"
                />
                <delete-link
                  v-if="item.user_has_write_access"
                  @delete="deleteSSHCredential(item)"
                >
                  Are you sure you want to delete the
                  <strong>{{ item.description }}</strong> SSH credential?
                </delete-link>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </template>
    </list-layout>
    <new-ssh-credential-modal
      ref="newSSHCredentialModal"
      @new="createNewSSHCredential"
    />
    <new-shared-ssh-credential-modal
      ref="newSharedSSHCredentialModal"
      @new="createNewSharedSSHCredential"
    />
    <!--
    <list-layout class="mt-4" @add-new-item="showNewPasswordCredentialModal" :items="passwordCredentials" title="Password Credentials"
      new-item-button-text="New Password Credential">
      <template #item-list="slotProps">

        <b-table striped hover :fields="fields" :items="slotProps.items">
          <template #cell(sharing)="data">
            <share-button :entity-id="data.item.token" :disallow-editing-admin-groups="false" :auto-add-admin-groups="false"/>
          </template>
          <template #cell(action)="data">
            <delete-link v-if="data.item.user_has_write_access" @delete="deletePasswordCredential(data.item)">
              Are you sure you want to delete the
              <strong>{{ data.item.description }}</strong> password credential?
            </delete-link>
          </template>
        </b-table>
      </template>
    </list-layout>
    <new-password-credential-modal ref="newPasswordCredentialModal" @new="createNewPasswordCredential" />
    -->
  </div>
</template>

<script>
import { Plus } from "@lucide/vue";
import { models, services, session } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";
// import NewPasswordCredentialModal from "../credentials/NewPasswordCredentialModal.vue";

export default {
  components: {
    Plus,
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    "list-layout": layouts.ListLayout,
    "clipboard-copy-link": components.ClipboardCopyLink,
    // "new-password-credential-modal": NewPasswordCredentialModal,
    "new-ssh-credential-modal": NewSSHCredentialModal,
    "new-shared-ssh-credential-modal": NewSSHCredentialModal,
    "share-button": components.ShareButton,
  },
  created: function () {
    this.fetchSSHKeys();
    this.fetchPasswordCredentials();
  },
  data: function () {
    return {
      sshKeys: [],
      passwordCredentials: [],
      userIsAdmin: session.Session.isGatewayAdmin,
      adminsGroup: null,
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "Description",
          key: "description",
        },
        {
          label: "User",
          key: "username",
        },
        {
          label: "Created",
          key: "persisted_time",
        },
        {
          label: "Sharing",
          key: "sharing",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
  },
  methods: {
    fetchSSHKeys() {
      services.CredentialSummaryService.allSSHCredentials().then((sshCreds) => {
        this.sshKeys = sshCreds;
      });
    },
    fetchPasswordCredentials() {
      services.CredentialSummaryService.allPasswordCredentials().then(
        (passwordCreds) => (this.passwordCredentials = passwordCreds),
      );
    },
    showNewSSHCredentialModal() {
      this.$refs.newSSHCredentialModal.show();
    },
    createNewSSHCredential(data) {
      services.CredentialSummaryService.createSSH({ data: data }).then(() =>
        this.fetchSSHKeys(),
      );
    },
    deleteSSHCredential(cred) {
      services.CredentialSummaryService.delete({
        lookup: cred.token,
      }).then(() => this.fetchSSHKeys());
    },
    showNewPasswordCredentialModal() {
      this.$refs.newPasswordCredentialModal.show();
    },
    createNewPasswordCredential(data) {
      services.CredentialSummaryService.createPassword({
        data: data,
      }).then(() => this.fetchPasswordCredentials());
    },
    deletePasswordCredential(cred) {
      services.CredentialSummaryService.delete({
        lookup: cred.token,
      }).then(() => this.fetchPasswordCredentials());
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
      services.CredentialSummaryService.createSSH({ data: data }).then(
        (cred) => {
          const sharedEntity = new models.SharedEntity();
          services.UserProfileService.retrieve({
            lookup: session.Session.username,
          }).then((userProfile) => {
            sharedEntity.owner = userProfile;
            sharedEntity.is_owner =
              session.Session.username == sharedEntity.owner.user_id;
            sharedEntity.addGroup({
              group: this.adminsGroup,
              permissionType: models.ResourcePermissionType.MANAGE_SHARING,
            });
            services.SharedEntityService.merge({
              data: sharedEntity,
              lookup: cred.token,
            }).then(() => {
              this.fetchSSHKeys();
            });
          });
        },
      );
    },
  },
};
</script>
