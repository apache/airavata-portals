<template>
  <TableRow>
    <TableCell>
      {{ group.name }}
      <gateway-groups-badge
        :group="group"
        v-if="
          group.is_gateway_admins_group ||
          group.is_read_only_gateway_admins_group ||
          group.is_default_gateway_users_group
        "
      />
    </TableCell>
    <TableCell>{{ ownerUsername }}</TableCell>
    <TableCell>{{ group.description }}</TableCell>
    <TableCell>
      <div class="flex items-center gap-2">
        <Button
          v-if="group.is_owner || group.is_admin"
          as="a"
          variant="ghost"
          size="sm"
          :href="'/groups/edit/' + encodeURIComponent(group.id) + '/'"
        >
          Edit <Pencil class="size-4" />
        </Button>
        <Button
          v-if="deleteable"
          variant="ghost"
          size="sm"
          @click="show = true"
        >
          Delete <Trash2 class="size-4" />
        </Button>
      </div>
      <Dialog v-model:open="show">
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you sure?</DialogTitle>
          </DialogHeader>
          <p class="text-sm">
            You cannot go back! Do you really want to delete the group '<strong>{{
              group.name
            }}</strong
            >'?
          </p>
          <DialogFooter>
            <Button
              variant="secondary"
              :disabled="deleting"
              @click="show = false"
              >No</Button
            >
            <Button
              variant="destructive"
              :disabled="deleting"
              @click="deleteGroup(group.id)"
              >Yes</Button
            >
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TableCell>
  </TableRow>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import { Pencil, Trash2 } from "@lucide/vue";

export default {
  name: "group-list-item",
  data() {
    return {
      show: false,
      deleting: false,
    };
  },
  props: ["group"],
  components: {
    "gateway-groups-badge": components.GatewayGroupsBadge,
    Pencil,
    Trash2,
  },
  computed: {
    deleteable: function () {
      return (
        this.group.is_owner &&
        // Don't allow deleting "GatewayGroups" groups since they serve
        // a special function in the gateway
        this.group.is_gateway_admins_group === false &&
        this.group.is_read_only_gateway_admins_group === false &&
        this.group.is_default_gateway_users_group === false
      );
    },
    ownerUsername() {
      const lastAtIndex = this.group.owner_id.lastIndexOf("@");
      if (lastAtIndex > 0) {
        return this.group.owner_id.substring(0, lastAtIndex);
      }
      return this.group.owner_id;
    },
  },
  methods: {
    deleteGroup(id) {
      this.deleting = true;
      services.GroupService.delete({ lookup: id })
        .then(() => {
          this.$emit("deleteSuccess", "Group Deleted Successfully!");
          this.show = false;
          this.deleting = false;
        })
        .catch(() => {
          this.$emit("deleteFailed", "Group Delete Failed!");
          this.show = false;
          this.deleting = false;
        });
    },
  },
};
</script>
