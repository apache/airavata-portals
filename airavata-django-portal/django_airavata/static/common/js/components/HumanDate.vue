<template>
  <abbr :title="date.toString()">{{ fromNow }}</abbr>
</template>
<script>
export default {
  name: "human-date",
  props: {
    date: Date,
  },
  computed: {
    fromNow() {
      const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
      const diffMs = this.date - Date.now();
      const diffSecs = Math.round(diffMs / 1000);
      const diffMins = Math.round(diffSecs / 60);
      const diffHours = Math.round(diffMins / 60);
      const diffDays = Math.round(diffHours / 24);
      if (Math.abs(diffSecs) < 60) return rtf.format(diffSecs, "second");
      if (Math.abs(diffMins) < 60) return rtf.format(diffMins, "minute");
      if (Math.abs(diffHours) < 24) return rtf.format(diffHours, "hour");
      return rtf.format(diffDays, "day");
    },
  },
};
</script>
