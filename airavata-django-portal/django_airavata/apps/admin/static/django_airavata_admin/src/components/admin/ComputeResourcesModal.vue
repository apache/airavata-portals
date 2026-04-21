<template>
  <!-- TODO: migrate to Bootstrap 5 modal -->
  <div
    ref="modal"
    class="modal"
    title="Select Compute Resource"
    :ok-disabled="modalSelectComputeResourceOkDisabled"
    @ok="onSelectComputeResource"
  >
    <select v-model="selectedComputeResource" class="form-select" :options="computeResourceOptions">
      <template slot="first">
        <option :value="null">Please select compute resource</option>
      </template>
    </select>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
export default {
  name: "ComputeResourcesModal",
  props: {
    computeResourceNames: Array,
    excludedResourceIds: Array,
  },
  data() {
    return {
      selectedComputeResource: null,
      localComputeResourceNames: null,
    };
  },
  computed: {
    modalSelectComputeResourceOkDisabled: function () {
      // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
      return this.selectedComputeResource == null;
    },
    computeResourceOptions: function () {
      const names = this.computeResourceNames
        ? this.computeResourceNames
        : this.localComputeResourceNames;
      const options = names
        ? names
            .filter((comp) =>
              this.excludedResourceIds ? !this.excludedResourceIds.includes(comp.host_id) : true,
            )
            .map((comp) => {
              return {
                value: comp.host_id,
                text: comp.host,
              };
            })
        : [];
      options.sort((a, b) => a.text.toLowerCase().localeCompare(b.text.toLowerCase()));
      return options;
    },
  },
  created() {
    if (!this.computeResourceNames) {
      services.ComputeResourceService.namesList().then(
        (resourceNames) => (this.localComputeResourceNames = resourceNames),
      );
    }
  },
  methods: {
    onSelectComputeResource() {
      this.$emit("selected", this.selectedComputeResource);
    },
    show() {
      this.$refs.modal.show();
    },
  },
};
</script>
