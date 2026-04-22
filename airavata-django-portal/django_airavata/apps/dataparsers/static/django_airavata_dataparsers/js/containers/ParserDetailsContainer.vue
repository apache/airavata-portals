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

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { models, services } from "django-airavata-api";

const props = defineProps<{ parserId: string }>();

const parser = ref<InstanceType<typeof models.Parser> | null>(null);

onMounted(async () => {
  parser.value = await services.ParserService.retrieve({ lookup: props.parserId });
});
</script>
