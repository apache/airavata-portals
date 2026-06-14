<template>
  <Card>
    <CardHeader>
      <CardTitle>{{ title }}</CardTitle>
    </CardHeader>
    <CardContent>
      <div
        v-for="commandObject in data"
        :key="commandObject.key"
        class="mb-1 flex items-stretch gap-2"
      >
        <Input
          type="text"
          v-model="commandObject.command"
          required
          ref="commandObjectInputs"
          :disabled="readonly"
        />
        <Button
          v-if="!readonly"
          variant="secondary"
          @click="deleteCommandObject(commandObject)"
        >
          <Trash2 class="size-4" />
          <span class="sr-only">Delete</span>
        </Button>
      </div>
      <Button v-if="!readonly" variant="secondary" @click="addCommandObject">{{
        addButtonLabel
      }}</Button>
    </CardContent>
  </Card>
</template>

<script>
import { Trash2 } from "@lucide/vue";
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "command-objects-editor",
  components: { Trash2 },
  mixins: [mixins.VModelMixin],
  props: {
    value: {
      type: Array,
    },
    title: {
      type: String,
      required: true,
    },
    addButtonLabel: {
      type: String,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    addCommandObject() {
      if (!this.data) {
        this.data = [];
      }
      this.data.push(new models.CommandObject());
      this.$nextTick(() =>
        this.$refs.commandObjectInputs[
          this.$refs.commandObjectInputs.length - 1
        ].$el.focus(),
      );
    },
    deleteCommandObject(commandObject) {
      const index = this.data.findIndex((cmd) => cmd.key === commandObject.key);
      this.data.splice(index, 1);
    },
  },
};
</script>
