<template>
  <main-layout
    title="Create Group"
    subtitle="Create a new group and choose its members."
  >
    <group-editor :group="newGroup" @saved="handleSaved"></group-editor>
  </main-layout>
</template>

<script>
import GroupEditor from "../group_components/GroupEditor.vue";

import { models, session } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
export default {
  name: "group-create-container",
  props: {
    next: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      newGroup: this.createNewGroup(),
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
    createNewGroup() {
      const group = new models.Group();
      const ownerId = session.Session.airavataInternalUserId;
      group.members.push(ownerId);
      group.owner_id = ownerId;
      return group;
    },
  },
  computed: {},
  beforeMount: function () {},
};
</script>
