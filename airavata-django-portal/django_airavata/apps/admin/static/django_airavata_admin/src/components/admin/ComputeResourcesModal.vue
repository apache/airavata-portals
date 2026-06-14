<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Select Compute Resource</DialogTitle>
      </DialogHeader>
      <div class="space-y-2">
        <select
          v-model="selectedComputeResource"
          class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
        >
          <option :value="null">Please select compute resource</option>
          <option
            v-for="opt in computeResourceOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.text }}
          </option>
        </select>
      </div>
      <DialogFooter>
        <Button variant="outline" @click="hide">Cancel</Button>
        <Button
          variant="default"
          :disabled="modalSelectComputeResourceOkDisabled"
          @click="onSelectComputeResource"
          >OK</Button
        >
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script>
import { services } from "django-airavata-api";
export default {
  name: "compute-resources-modal",
  props: {
    computeResourceNames: Array,
    excludedResourceIds: Array,
  },
  data() {
    return {
      open: false,
      selectedComputeResource: null,
      localComputeResourceNames: null,
    };
  },
  created() {
    if (!this.computeResourceNames) {
      services.ComputeResourceService.namesList().then(
        (resourceNames) => (this.localComputeResourceNames = resourceNames),
      );
    }
  },
  computed: {
    modalSelectComputeResourceOkDisabled: function () {
      return this.selectedComputeResource == null;
    },
    computeResourceOptions: function () {
      const names = this.computeResourceNames
        ? this.computeResourceNames
        : this.localComputeResourceNames;
      const options = names
        ? names
            .filter((comp) =>
              this.excludedResourceIds
                ? !this.excludedResourceIds.includes(comp.host_id)
                : true,
            )
            .map((comp) => {
              return {
                value: comp.host_id,
                text: comp.host,
              };
            })
        : [];
      options.sort((a, b) =>
        a.text.toLowerCase().localeCompare(b.text.toLowerCase()),
      );
      return options;
    },
  },
  methods: {
    onSelectComputeResource() {
      this.$emit("selected", this.selectedComputeResource);
      this.hide();
    },
    show() {
      this.open = true;
    },
    hide() {
      this.open = false;
    },
  },
};
</script>
