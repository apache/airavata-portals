<template>
  <div class="space-y-6">
    <Alert
      v-if="showDismissibleAlert.dismissable"
      :variant="
        showDismissibleAlert.variant === 'danger' ? 'destructive' : 'default'
      "
    >
      <AlertDescription class="flex w-full items-start gap-2">
        <span>{{ showDismissibleAlert.message }}</span>
        <Button
          variant="ghost"
          size="icon"
          class="ml-auto shrink-0"
          @click="showDismissibleAlert.dismissable = false"
        >
          <X class="size-4" />
        </Button>
      </AlertDescription>
    </Alert>

    <form class="space-y-6" @submit.prevent="submitForm">
      <div class="space-y-4">
        <div class="space-y-1.5">
          <Label for="group_name">Group Name</Label>
          <Input
            id="group_name"
            type="text"
            v-model="localGroup.name"
            required
            placeholder="Enter group name"
          />
          <p class="text-sm text-muted-foreground">
            Name should only contain alpha characters.
          </p>
        </div>

        <div class="space-y-1.5">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            :rows="6"
            v-model="localGroup.description"
            required
            placeholder="Enter description of the group"
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Manage Group Members</CardTitle>
        </CardHeader>
        <CardContent>
          <group-members-editor
            :group="localGroup"
            @add-member="addGroupMember"
            @remove-member="removeGroupMember"
            @change-role-to-member="changeRoleToMember"
            @change-role-to-admin="changeRoleToAdmin"
          />
        </CardContent>
      </Card>
    </form>

    <div class="flex justify-end">
      <Button @click="submitForm">Submit</Button>
    </div>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import GroupMembersEditor from "./GroupMembersEditor.vue";
import { X } from "@lucide/vue";

export default {
  props: {
    group: {
      type: models.Group,
      required: true,
    },
  },
  data() {
    return {
      localGroup: this.group.clone(),
      showDismissibleAlert: {
        variant: "success",
        message: "no data",
        dismissable: false,
      },
      userProfiles: [],
    };
  },
  components: {
    GroupMembersEditor,
    X,
  },
  methods: {
    submitForm() {
      let saveOperation = this.localGroup.id
        ? services.GroupService.update({
            lookup: this.localGroup.id,
            data: this.localGroup,
          })
        : services.GroupService.create({ data: this.localGroup });
      saveOperation
        .then((group) => {
          this.$emit("saved", group);
        })
        .catch((error) => {
          this.showDismissibleAlert.dismissable = true;
          this.showDismissibleAlert.message = "Error: " + error.data;
          this.showDismissibleAlert.variant = "danger";
        });
    },
    addGroupMember(airavataInternalUserId) {
      this.localGroup.members.push(airavataInternalUserId);
    },
    removeGroupMember(airavataInternalUserId) {
      const index = this.localGroup.members.indexOf(airavataInternalUserId);
      this.localGroup.members.splice(index, 1);
      this.removeAdminMember(airavataInternalUserId);
    },
    removeAdminMember(airavataInternalUserId) {
      const adminIndex = this.localGroup.admins.indexOf(airavataInternalUserId);
      if (adminIndex >= 0) {
        this.localGroup.admins.splice(adminIndex, 1);
      }
    },
    changeRoleToMember(airavataInternalUserId) {
      this.removeAdminMember(airavataInternalUserId);
    },
    changeRoleToAdmin(airavataInternalUserId) {
      const adminIndex = this.localGroup.admins.indexOf(airavataInternalUserId);
      if (adminIndex < 0) {
        this.localGroup.admins.push(airavataInternalUserId);
      }
    },
  },
};
</script>
