<template>
  <div>
    <select
      :id="id"
      v-model="data"
      class="form-select"
      style="width: auto"
      :state="componentValidState"
      @input="valueChanged"
    >
      <option v-for="userfile in userfiles" :key="userfile.file_dpu" :value="userfile.file_dpu">
        {{ userfile.file_name }}
      </option>
    </select>
  </div>
</template>

<script>
import { InputEditorMixin } from "django-airavata-workspace-plugin-api";
import { utils as apiUtils } from "django-airavata-api";

export default {
  name: "UserFileInputEditor",
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
