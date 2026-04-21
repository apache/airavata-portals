<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">
          <div>{{ parserId }}</div>
        </h1>
      </div>
    </div>
    <div v-if="parser" class="row">
      <div class="col">
        <div class="mb-3" label="Image Name" label-for="image-name">
          <input id="image-name" v-model="parser.imageName" class="form-control" type="text" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";

export default {
  name: "ParserDetailsContainer",
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
