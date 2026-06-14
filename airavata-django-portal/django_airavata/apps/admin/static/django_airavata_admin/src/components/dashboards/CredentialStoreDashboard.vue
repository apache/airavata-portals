<template>
  <main-layout
    title="Credential Store"
    subtitle="Manage the SSH and gateway credentials used to access compute resources."
  >
    <template v-slot:actions>
      <Button
        v-if="userIsAdmin"
        variant="outline"
        @click="showNewSharedSSHCredentialModel"
      >
        New Gateway SSH Credential
        <Plus class="size-4" aria-hidden="true" />
      </Button>
      <Button @click="showNewSSHCredentialModal">
        New SSH Credential
        <Plus class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <Card>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead v-for="field in fields" :key="field.key">
                {{ field.label }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="item in sshKeys" :key="item.token">
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
      </CardContent>
    </Card>
    <new-ssh-credential-modal
      ref="newSSHCredentialModal"
      @new="createNewSSHCredential"
    />
    <new-shared-ssh-credential-modal
      ref="newSharedSSHCredentialModal"
      @new="createNewSharedSSHCredential"
    />
  </main-layout>
</template>

<script>
import { Plus } from "@lucide/vue";
import { models, services, session } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import NewSSHCredentialModal from "../credentials/NewSSHCredentialModal.vue";

export default {
  components: {
    Plus,
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    "main-layout": components.MainLayout,
    "clipboard-copy-link": components.ClipboardCopyLink,
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
