<template>
  <tr>
    <td><a :href="overviewLink">{{ project.name }}</a></td>
    <td>{{ project.owner }}</td>
    <td v-bind:title="project.creationTime">{{ creationTime }}</td>
    <td>
      <a :href="editLink" v-if="project.userHasWriteAccess" class="action-link">
        Edit <i class="fa fa-edit" aria-hidden="true"></i>
      </a>
      <a href="#" v-if="project.isOwner" class="action-link text-danger ms-2" @click.prevent="$emit('delete', project)">
        Delete <i class="fa fa-trash" aria-hidden="true"></i>
      </a>
    </td>
  </tr>
</template>

<script>
import urls from "../../utils/urls";
import moment from "moment";

export default {
  name: "project-list-item",
  props: ["project"],
  emits: ["delete"],
  computed: {
    creationTime: function () {
      var dt = new Date(this.project.creationTime);
      return moment(dt).fromNow();
    },
    overviewLink() {
      return urls.projectOverview(this.project);
    },
    editLink() {
      return urls.editProject(this.project);
    },
  },
};
</script>

<style></style>
