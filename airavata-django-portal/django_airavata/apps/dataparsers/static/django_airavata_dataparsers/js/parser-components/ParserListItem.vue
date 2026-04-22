<template>
  <tr>
    <td>{{ parser.id }}</td>
    <td>{{ parser.imageName }}</td>
    <td>{{ parser.executionCommand }}</td>
    <td>
      <a class="action-link" :href="'/dataparsers/edit/' + encodeURIComponent(parser.id) + '/'">
        Edit <i class="fa fa-edit"></i>
      </a>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { models } from "django-airavata-api";

defineProps<{ parser: InstanceType<typeof models.Parser> }>();
</script>

<style></style>
