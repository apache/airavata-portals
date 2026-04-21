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

<script>
export default {
  name: "ParserListItem",
  props: ["parser"],
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
  computed: {},
  methods: {},
};
</script>

<style></style>
