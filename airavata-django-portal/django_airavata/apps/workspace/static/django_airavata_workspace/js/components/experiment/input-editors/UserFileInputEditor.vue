<template>
  <div>
    <select
      :id="id"
      v-model="data"
      style="width: auto"
      :aria-invalid="componentValidState === false"
      class="border-input dark:bg-input/30 focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 aria-invalid:border-destructive h-9 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-3 disabled:cursor-not-allowed disabled:opacity-50"
      @change="valueChanged"
    >
      <option
        v-for="userfile in userfiles"
        v-bind:key="userfile.file_dpu"
        v-bind:value="userfile.file_dpu"
      >
        {{ userfile.file_name }}
      </option>
    </select>
  </div>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { utils as apiUtils } from "django-airavata-api";

export default {
  name: "user-file-input-editor",
  mixins: [InputEditorMixin],
  data() {
    return {
      userfiles: [],
    };
  },
  beforeMount: function () {
    // loads the list of file entries in django UserFiles model
    return apiUtils.FetchUtils.get("/api/get-ufiles").then(
      (res) => (this.userfiles = res["user-files"]),
    );
  },
};
</script>

<style scoped></style>
