<template>
  <TableRow>
    <TableCell>{{ parser.id }}</TableCell>
    <TableCell>{{ parser.image_name }}</TableCell>
    <TableCell>{{ parser.execution_command }}</TableCell>
    <TableCell>
      <a
        class="inline-flex items-center gap-1 text-primary hover:text-primary/90"
        :href="'/dataparsers/edit/' + encodeURIComponent(parser.id) + '/'"
      >
        Edit <Pencil class="size-4" aria-hidden="true" />
      </a>
    </TableCell>
  </TableRow>
</template>

<script>
import { Pencil } from "@lucide/vue";

export default {
  name: "parser-list-item",
  components: {
    Pencil,
  },
  data() {
    return {
      deleting: false,
    };
  },
  props: ["parser"],
  computed: {},
  methods: {},
};
</script>
