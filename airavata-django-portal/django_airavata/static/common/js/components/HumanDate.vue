<template>
  <abbr :title="date.toString()">{{ fromNow }}</abbr>
</template>
<script>
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export default {
  name: "human-date",
  props: {
    date: Date,
  },
  computed: {
    fromNow() {
      return dayjs(this.date).fromNow();
    },
  },
};
</script>
