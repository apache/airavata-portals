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

<script setup lang="ts">
import ProjectListItem from "./ProjectListItem.vue";

interface Project {
  project_id: string;
  name: string;
  owner?: string;
  creation_time?: string | Date;
  [key: string]: unknown;
}

defineProps<{
  projects: Project[];
}>();
</script>
