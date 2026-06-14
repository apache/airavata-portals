<template>
  <div>
    <div class="mb-4">
      <h1 class="text-xl font-semibold">
        <div>{{ parserId }}</div>
      </h1>
    </div>
    <div v-if="parser">
      <div class="grid gap-2">
        <Label for="image-name">Image Name</Label>
        <Input id="image-name" type="text" v-model="parser.image_name" />
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";

export default {
  name: "parser-details-container",
  props: {
    parserId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      parser: null,
    };
  },
  created() {
    services.ParserService.retrieve({
      lookup: this.parserId,
    }).then((parser) => (this.parser = parser));
  },
};
</script>
