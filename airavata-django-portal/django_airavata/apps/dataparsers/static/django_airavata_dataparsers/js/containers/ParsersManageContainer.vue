<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Parsers</h1>
      </div>
      <div id="col-new-group" class="col-sm-2">
        <button class="btn btn-primary" href="create">
          Create New Parser&nbsp;&nbsp;<i class="fa fa-plus" aria-hidden="true"></i>
        </button>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <parser-list :parsers="parsers"></parser-list>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeMount, ref } from "vue";
import { models, services } from "django-airavata-api";
import ParserList from "../parser-components/ParserList.vue";

const parsers = ref<InstanceType<typeof models.Parser>[] | null>(null);

onBeforeMount(async () => {
  parsers.value = await services.ParserService.list();
});
</script>

<style>
#col-new-group {
  text-align: right;
}
#modal-new-group {
  text-align: left;
}
</style>
