<template>
  <tr>
    <td>
      <i class="fa fa-folder me-2 text-muted"></i>
      <a :href="overviewLink" class="text-decoration-none"><strong>{{ project.name }}</strong></a>
    </td>
    <td>
      <span class="fw-medium">{{ ownerUsername }}</span>
      <span class="badge bg-secondary ms-1" v-if="isCurrentUser">You</span>
      <span class="badge bg-primary ms-1" v-else-if="isAdmin">Admin</span>
    </td>
    <td class="text-nowrap" v-bind:title="project.creation_time">{{ creationTime }}</td>
    <td class="text-nowrap" style="width: 1%">
      <div class="d-flex gap-2 justify-content-end flex-nowrap">
        <button type="button" class="btn btn-outline-danger btn-pill" @click="$emit('delete', project)">
          <i class="fa fa-trash me-1" aria-hidden="true"></i>Delete
        </button>
      </div>
    </td>
  </tr>
</template>

<script>
import urls from "../../utils/urls";
import moment from "moment";
import { session } from "django-airavata-api";

export default {
  name: "project-list-item",
  props: ["project"],
  emits: ["delete"],
  computed: {
    creationTime: function () {
      var dt = new Date(this.project.creation_time);
      return moment(dt).fromNow();
    },
    overviewLink() {
      return urls.projectOverview(this.project);
    },
    ownerUsername() {
      const owner = this.project.owner || "";
      const lastAt = owner.lastIndexOf("@");
      return lastAt > 0 ? owner.substring(0, lastAt) : owner;
    },
    isCurrentUser() {
      return this.ownerUsername === session.Session.username;
    },
    isAdmin() {
      const name = this.ownerUsername;
      return name === "default-admin" || name === "admin";
    },
  },
};
</script>

