<template>
  <tr @click="navigate" :style="navigable ? 'cursor: pointer' : ''">
    <td>
      {{ group.name }}
      <gateway-groups-badge
        :group="group"
        v-if="
          group.is_gateway_admins_group ||
          group.is_read_only_gateway_admins_group ||
          group.is_default_gateway_users_group
        "
      />
    </td>
    <td>
      <span class="fw-medium">{{ ownerUsername }}</span>
      <span class="badge bg-secondary ms-1" v-if="isCurrentUser">You</span>
      <span class="badge bg-primary ms-1" v-else-if="isAdmin">Admin</span>
    </td>
    <td>{{ group.description }}</td>
    <td class="text-nowrap" style="width: 1%" @click.stop>
      <a
        href="#"
        v-if="deleteable"
        class="action-link"
        @click.prevent="show = true"
        :variant="deleteButtonVariant"
      >
        Delete <i class="fa fa-trash"></i>
      </a>
      <div v-if="show" class="alert alert-danger mt-2">
        <p class="my-2">
          You cannot go back! Do you really want to delete the group '<strong>{{
            group.name
          }}</strong>'?
        </p>
        <div class="d-flex justify-content-end">
          <button class="btn btn-danger btn-sm ms-1"
            :disabled="deleting"
            @click="deleteGroup(group.id)"
            >Yes</button
          >
          <button class="btn btn-secondary btn-sm ms-1"
            :disabled="deleting"
            @click="show = false"
            >No</button
          >
        </div>
      </div>
    </td>
  </tr>
</template>

<script>
import { services, session } from "django-airavata-api";
import { components } from "django-airavata-common-ui";

export default {
  name: "group-list-item",
  data() {
    return {
      show: false,
      deleteButtonVariant: "link",
      yesButtonVariant: "danger",
      noButtonVariant: "secondary",
      headerBgVariant: "danger",
      bodyBgVariant: "light",
      headerTextVariant: "light",
      deleting: false,
    };
  },
  props: ["group"],
  components: {
    "gateway-groups-badge": components.GatewayGroupsBadge,
  },
  computed: {
    navigable() {
      return this.group.is_owner || this.group.is_admin;
    },
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
    isCurrentUser() {
      return this.ownerUsername === session.Session.username;
    },
    isAdmin() {
      const name = this.ownerUsername;
      return name === "default-admin" || name === "admin";
    },
  },
  methods: {
    navigate() {
      if (!this.navigable) return;
      window.location.href = '/resources/sharing/edit/' + encodeURIComponent(this.group.id) + '/';
    },
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

<style></style>
