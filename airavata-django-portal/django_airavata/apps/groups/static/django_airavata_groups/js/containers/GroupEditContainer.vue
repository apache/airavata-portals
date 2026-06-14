<template>
  <main-layout
    title="Edit Group"
    subtitle="Update group details and manage its members."
  >
    <group-editor v-if="group" :group="group" @saved="handleSaved"></group-editor>
  </main-layout>
</template>

<script>
import GroupEditor from "../group_components/GroupEditor.vue";

import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";

export default {
  name: "group-edit-container",
  props: {
    groupId: {
      type: String,
      required: true,
    },
    next: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      group: null,
    };
  },
  components: {
    "main-layout": comps.MainLayout,
    GroupEditor,
  },
  methods: {
    handleSaved: function () {
      window.location.assign(this.next);
    },
  },
  computed: {},
  mounted: function () {
    services.GroupService.retrieve({ lookup: this.groupId }).then(
      (group) => (this.group = group)
    );
  },
};
</script>
