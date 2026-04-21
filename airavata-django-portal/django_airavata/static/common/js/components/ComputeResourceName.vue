<template>
  <span :class="{ 'font-italic': notAvailable }">{{ name }}</span>
</template>
<script>
import { services } from "django-airavata-api";
export default {
  name: "ComputeResourceName",
  props: {
    computeResourceId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      computeResource: null,
      notAvailable: false,
    };
  },
  computed: {
    name() {
      if (this.notAvailable) {
        return "N/A";
      } else {
        return this.computeResource ? this.computeResource.host_name : "";
      }
    },
  },
  watch: {
    computeResourceId() {
      this.loadComputeResource();
    },
  },
  created() {
    this.loadComputeResource();
  },
  methods: {
    loadComputeResource() {
      services.ComputeResourceService.retrieve(
        { lookup: this.computeResourceId },
        { ignoreErrors: true, cache: true },
      )
        .then((computeResource) => (this.computeResource = computeResource))
        .catch(() => (this.notAvailable = true));
    },
  },
};
</script>
