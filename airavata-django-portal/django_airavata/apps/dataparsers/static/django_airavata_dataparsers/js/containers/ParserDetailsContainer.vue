<template>
  <main-layout
    title="Parser Details"
    subtitle="View the configuration for this data parser."
  >
    <Card v-if="parser">
      <CardContent>
        <div class="space-y-1.5">
          <Label for="image-name">Image Name</Label>
          <Input id="image-name" type="text" v-model="parser.image_name" />
        </div>
      </CardContent>
    </Card>
  </main-layout>
</template>

<script>
import MainLayout from "django-airavata-common-ui/js/components/MainLayout.vue";
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
  components: {
    "main-layout": MainLayout,
  },
  created() {
    services.ParserService.retrieve({
      lookup: this.parserId,
    }).then((parser) => (this.parser = parser));
  },
};
</script>
