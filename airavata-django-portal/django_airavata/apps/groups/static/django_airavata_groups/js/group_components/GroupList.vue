<template>
  <div>
    <div :class="['alert', 'alert-' + alertVariant]"
      v-if="showDismissibleAlert"
      >{{ alertMsg }}</div
    >
    <table class="table table-hover">
      <thead>
        <tr>
          <th>Name</th>
          <th class="text-nowrap">Owner</th>
          <th class="text-nowrap">Description</th>
          <th class="text-nowrap" style="width: 1%">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!groupsForOwners || groupsForOwners.length === 0">
          <td colspan="4">
            <div class="table-empty">
              <i class="fa fa-users table-empty__icon"></i>
              <div class="table-empty__title">No groups yet</div>
              <div class="table-empty__text">Create a group to share resources with other users.</div>
            </div>
          </td>
        </tr>
        <group-list-item
          v-else
          @deleteSuccess="deleteSuccess"
          @deleteFailed="deleteFailed"
          v-bind:group="group"
          v-bind:type="owner"
          v-for="group in groupsForOwners"
          v-bind:key="group.groupID"
        >
        </group-list-item>
      </tbody>
    </table>
  </div>
</template>

<script>
import GroupListItem from "./GroupListItem.vue";

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

<style></style>
