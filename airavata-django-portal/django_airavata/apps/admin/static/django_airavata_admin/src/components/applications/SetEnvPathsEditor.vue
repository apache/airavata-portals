<template>
  <Card>
    <CardHeader>
      <CardTitle>{{ title }}</CardTitle>
    </CardHeader>
    <CardContent>
      <div
        v-for="setEnvPath in data"
        :key="setEnvPath.key"
        class="mb-1 flex items-center gap-2"
      >
        <Input
          type="text"
          v-model="setEnvPath.name"
          required
          placeholder="NAME"
          ref="nameInputs"
          :disabled="readonly"
        />
        <Equal class="mx-1 size-4 shrink-0" />
        <Input
          type="text"
          v-model="setEnvPath.value"
          required
          placeholder="VALUE"
          :disabled="readonly"
        />
        <Button
          v-if="!readonly"
          variant="secondary"
          @click="deleteEnvPath(setEnvPath)"
        >
          <Trash2 class="size-4" />
          <span class="sr-only">Delete</span>
        </Button>
      </div>
      <Button v-if="!readonly" variant="secondary" @click="addEnvPath">{{
        addButtonLabel
      }}</Button>
    </CardContent>
  </Card>
</template>

<script>
import { Equal, Trash2 } from "@lucide/vue";
import { models } from "django-airavata-api";
import { mixins } from "django-airavata-common-ui";

export default {
  name: "set-env-paths-editor",
  components: { Equal, Trash2 },
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
    addEnvPath() {
      if (!this.data) {
        this.data = [];
      }
      this.data.push(new models.SetEnvPaths());
      this.$nextTick(() =>
        this.$refs.nameInputs[this.$refs.nameInputs.length - 1].$el.focus(),
      );
    },
    deleteEnvPath(setEnvPath) {
      const index = this.data.findIndex((env) => env.key === setEnvPath.key);
      this.data.splice(index, 1);
    },
  },
};
</script>
