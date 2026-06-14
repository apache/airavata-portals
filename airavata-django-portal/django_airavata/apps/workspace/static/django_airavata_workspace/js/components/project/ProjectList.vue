<template>
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Name</TableHead>
        <TableHead>Owner</TableHead>
        <TableHead>Creation Time</TableHead>
        <TableHead>Actions</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <project-list-item
        v-bind:project="project"
        v-for="project in projects"
        v-bind:key="project.project_id"
      >
      </project-list-item>
    </TableBody>
  </Table>
</template>

<script>
import ProjectListItem from "./ProjectListItem.vue";

export default {
  name: "project-list",
  props: ["projects"],
  data: function () {
    return {};
  },
  components: {
    ProjectListItem,
  },
};
</script>
