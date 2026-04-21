<template>
  <div>
    <div v-if="showDismissibleAlert" :class="['alert', 'alert-' + alertVariant]">
      {{ alertMsg }}
    </div>
    <table class="table table-hover">
      <thead>
        <tr>
          <th>Name</th>
          <th>Image Name</th>
          <th>Execution Command</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <parser-list-item v-for="parser in parsers" :key="parser.id" :parser="parser">
        </parser-list-item>
        <tr v-if="parsers && parsers.length === 0">
          <td colspan="4" class="text-center text-muted py-4">
            <i class="fa fa-cogs fa-2x d-block mb-2 text-muted"></i>
            No parsers yet. Click "Create New Parser" to define one.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import ParserListItem from "./ParserListItem.vue";

export default {
  name: "ParserList",
  components: {
    ParserListItem,
  },
  props: ["parsers"],
  data: function () {
    return {
      owner: "owner",
      alertMsg: null,
      alertVariant: "primary",
      showDismissibleAlert: false,
    };
  },
  methods: {},
};
</script>

<style>
#parser-list-actions-header {
  min-width: 150px;
}
</style>
