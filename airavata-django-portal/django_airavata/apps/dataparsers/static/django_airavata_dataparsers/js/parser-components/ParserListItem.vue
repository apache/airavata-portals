<template>
  <TableRow>
    <TableCell>{{ parser.id }}</TableCell>
    <TableCell>{{ parser.image_name }}</TableCell>
    <TableCell>{{ parser.execution_command }}</TableCell>
    <TableCell>
      <Button
        as="a"
        variant="link"
        size="sm"
        :href="'/dataparsers/edit/' + encodeURIComponent(parser.id) + '/'"
      >
        Edit <Pencil class="size-4" aria-hidden="true" />
      </Button>
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
