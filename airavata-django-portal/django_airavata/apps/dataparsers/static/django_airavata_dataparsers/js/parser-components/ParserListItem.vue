<template>
  <tr>
    <td>{{ parser.id }}</td>
    <td>{{ parser.image_name }}</td>
    <td>{{ parser.execution_command }}</td>
    <td>
      <a
        class="action-link"
        :href="'/dataparsers/edit/' + encodeURIComponent(parser.id) + '/'"
      >
        Edit <i class="fa fa-edit"></i>
      </a>
    </td>
  </tr>
</template>

<script>
export default {
  name: "parser-list-item",
  data() {
    return {
      show: false,
      deleteButtonVariant: "link",
      yesButtonVariant: "danger",
      noButtonVariant: "secondary",
      headerBgVariant: "danger",
      bodyBgVariant: "light",
      headerTextVariant: "light",
      deleting: false,
    };
  },
  props: ["parser"],
  computed: {},
  methods: {},
};
</script>

<style></style>
