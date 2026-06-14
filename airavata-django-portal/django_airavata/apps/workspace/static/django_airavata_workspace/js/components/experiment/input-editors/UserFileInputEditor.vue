<template>
  <div>
    <select
      :id="id"
      v-model="data"
      :aria-invalid="componentValidState === false"
      :class="nativeSelectClass"
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
import { cn, NATIVE_SELECT_CLASS } from "../../../lib/utils";

export default {
  name: "user-file-input-editor",
  mixins: [InputEditorMixin],
  data() {
    return {
      userfiles: [],
    };
  },
  computed: {
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>, sized to
      // its content, plus the invalid-state ring mirroring shadcn controls.
      return cn(
        NATIVE_SELECT_CLASS,
        "w-auto aria-invalid:border-destructive aria-invalid:ring-destructive/40",
      );
    },
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
