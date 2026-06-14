<template>
  <div>
    <Alert
      v-if="showDismissibleAlert"
      :variant="alertVariant === 'danger' ? 'destructive' : 'default'"
      class="mb-4"
    >
      <AlertDescription class="flex w-full items-start gap-2">
        <span>{{ alertMsg }}</span>
        <Button
          variant="ghost"
          size="icon"
          class="ml-auto shrink-0"
          @click="showDismissibleAlert = false"
        >
          <X class="size-4" />
        </Button>
      </AlertDescription>
    </Alert>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Owner</TableHead>
          <TableHead>Description</TableHead>
          <TableHead class="min-w-[150px]">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <group-list-item
          @deleteSuccess="deleteSuccess"
          @deleteFailed="deleteFailed"
          :group="group"
          :type="owner"
          v-for="group in groupsForOwners"
          :key="group.id"
        >
        </group-list-item>
      </TableBody>
    </Table>
  </div>
</template>

<script>
import GroupListItem from "./GroupListItem.vue";
import { X } from "@lucide/vue";

export default {
  name: "group-list",
  props: ["groupsForOwners"],
  data: function () {
    return {
      owner: "owner",
      alertMsg: null,
      alertVariant: "primary",
      showDismissibleAlert: false,
    };
  },
  components: {
    GroupListItem,
    X,
  },
  methods: {
    deleteSuccess() {
      window.location.reload(true);
    },
    deleteFailed(value) {
      this.alertMsg = value;
      this.alertVariant = "danger";
      this.showDismissibleAlert = true;
    },
  },
};
</script>
