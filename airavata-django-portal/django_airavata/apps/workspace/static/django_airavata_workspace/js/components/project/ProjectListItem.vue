<template>
  <tr style="cursor: pointer" @click="navigate">
    <td>
      <i class="fa fa-folder me-2 text-muted"></i>
      <strong>{{ project.name }}</strong>
    </td>
    <td>
      <span class="fw-medium">{{ ownerUsername }}</span>
      <span v-if="isCurrentUser" class="badge bg-secondary ms-1">You</span>
      <span v-else-if="isAdmin" class="badge bg-primary ms-1">Admin</span>
    </td>
    <td class="text-nowrap" :title="project.creation_time">{{ creationTime }}</td>
    <td class="text-nowrap" style="width: 1%" @click.stop>
      <div class="d-flex gap-2 justify-content-end flex-nowrap">
        <button
          type="button"
          class="btn btn-outline-danger btn-pill"
          @click="$emit('delete', project)"
        >
          <i class="fa fa-trash me-1" aria-hidden="true"></i>Delete
        </button>
      </div>
    </td>
  </tr>
</template>

<script>
import urls from "../../utils/urls";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";
import { session } from "django-airavata-api";

export default {
  name: "ProjectListItem",
  props: ["project"],
  emits: ["delete"],
  computed: {
    creationTime: function () {
      var dt = new Date(this.project.creation_time);
      return relativeTime(dt);
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
  methods: {
    navigate() {
      window.location.href = this.overviewLink;
    },
  },
};
</script>
