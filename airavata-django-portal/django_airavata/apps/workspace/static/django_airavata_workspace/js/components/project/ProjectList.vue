<template>
  <table class="table table-hover">
    <thead>
      <tr>
        <th>Name</th>
        <th>Owner</th>
        <th>Creation Time</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <project-list-item v-for="project in projects" :key="project.project_id" :project="project">
      </project-list-item>
    </tbody>
  </table>
</template>

<script>
import ProjectListItem from "./ProjectListItem.vue";

export default {
  name: "ProjectList",
  components: {
    ProjectListItem,
  },
  props: ["projects"],
  data: function () {
    return {};
  },
};
</script>
