<template>
  <b-badge :variant="badgeVariant">{{ label }}</b-badge>
</template>

<script>
import { models } from "django-airavata-api";

export default {
  name: "experiment-status-badge",
  props: {
    statusName: {
      type: String,
      required: true,
    },
  },
  computed: {
    experimentState: function () {
      return models.ExperimentState.byName(this.statusName);
    },
    // statusName arrives as the full proto member name (EXPERIMENT_STATE_CREATED);
    // render the prefix-stripped short alias. Falls back to the raw value if the
    // name doesn't resolve to a known state.
    label: function () {
      return this.experimentState
        ? this.experimentState.constructor.shortAlias(this.experimentState.name)
        : this.statusName;
    },
    badgeVariant: function () {
      if (this.experimentState.isProgressing) {
        return "secondary";
      } else if (this.experimentState === models.ExperimentState.COMPLETED) {
        return "success";
      } else if (
        this.experimentState === models.ExperimentState.CANCELING ||
        this.experimentState === models.ExperimentState.CANCELED
      ) {
        return "warning";
      } else if (this.experimentState === models.ExperimentState.FAILED) {
        return "danger";
      } else {
        return "info";
      }
    },
  },
};
</script>
