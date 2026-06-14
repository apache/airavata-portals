<template>
  <main-layout title="Projects" subtitle="Browse and manage your projects.">
    <template #actions>
      <project-button-new @new-project="onNewProject" />
    </template>
    <Card>
      <CardContent>
        <project-list v-bind:projects="projects"></project-list>
        <pager
          v-bind:paginator="projectsPaginator"
          v-on:next="nextProjects"
          v-on:previous="previousProjects"
        ></pager>
      </CardContent>
    </Card>
  </main-layout>
</template>

<script>
import ProjectButtonNew from "../components/project/ProjectButtonNew.vue";
import ProjectList from "../components/project/ProjectList.vue";

import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";

export default {
  props: ["initialProjectsData"],
  name: "project-list-container",
  data() {
    return {
      projectsPaginator: null,
    };
  },
  components: {
    "main-layout": comps.MainLayout,
    "project-list": ProjectList,
    "project-button-new": ProjectButtonNew,
    pager: comps.Pager,
  },
  methods: {
    nextProjects: function () {
      this.projectsPaginator.next();
    },
    previousProjects: function () {
      this.projectsPaginator.previous();
    },
    onNewProject: function () {
      services.ProjectService.list().then(
        (result) => (this.projectsPaginator = result),
      );
    },
  },
  computed: {
    projects: function () {
      return this.projectsPaginator ? this.projectsPaginator.results : null;
    },
  },
  beforeMount: function () {
    services.ProjectService.list({
      initialData: this.initialProjectsData,
    }).then((result) => (this.projectsPaginator = result));
  },
};
</script>
