<template>
  <div>
    <Alert
      v-if="showDismissibleAlert"
      :variant="alertVariant === 'destructive' ? 'destructive' : 'default'"
      class="mb-4"
    >
      <AlertDescription class="flex w-full items-start gap-2">
        <span>{{ alertMsg }}</span>
        <Button
          variant="ghost"
          size="icon"
          class="ml-auto shrink-0"
          @click="showDismissibleAlert = false"
        >
          <X class="size-4" />
        </Button>
      </AlertDescription>
    </Alert>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Image Name</TableHead>
          <TableHead>Execution Command</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <parser-list-item
          v-bind:parser="parser"
          v-for="parser in parsers"
          v-bind:key="parser.id"
        >
        </parser-list-item>
      </TableBody>
    </Table>
  </div>
</template>

<script>
import { X } from "@lucide/vue";
import ParserListItem from "./ParserListItem.vue";

export default {
  name: "parser-list",
  props: ["parsers"],
  data: function () {
    return {
      owner: "owner",
      alertMsg: null,
      alertVariant: "default",
      showDismissibleAlert: false,
    };
  },
  components: {
    X,
    ParserListItem,
  },
  methods: {},
};
</script>
