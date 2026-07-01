<template>
  <TableRow>
    <TableCell>{{ project.name }}</TableCell>
    <TableCell>{{ project.owner }}</TableCell>
    <TableCell v-bind:title="project.creation_time">{{
      creationTime
    }}</TableCell>
    <TableCell>
      <a
        :href="editLink"
        v-if="project.user_has_write_access"
        class="inline-flex items-center gap-1 text-primary"
        >Edit <Pencil class="size-4" aria-hidden="true" /></a
      >
    </TableCell>
  </TableRow>
</template>

<script>
import { Pencil } from "@lucide/vue";
import urls from "../../utils/urls";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export default {
  name: "project-list-item",
  components: { Pencil },
  props: ["project"],
  computed: {
    creationTime: function () {
      var dt = new Date(this.project.creation_time);
      return dayjs(dt).fromNow();
    },
    editLink() {
      return urls.editProject(this.project);
    },
  },
};
</script>

<style></style>
