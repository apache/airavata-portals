<template>
  <div v-if="userHasWriteAccess" class="d-flex gap-2 mb-2">
    <uppy
      ref="file-upload"
      :xhr-upload-endpoint="uploadEndpoint"
      :tus-upload-finish-endpoint="uploadEndpoint"
      multiple
      @upload-finished="uploadFinished"
    />
    <div class="input-group input-group-sm" style="max-width: 300px">
      <input
        v-model="dirName"
        class="form-control"
        placeholder="New directory name"
        @keydown.enter="addDirectory"
      />
      <button class="btn btn-outline-secondary" :disabled="!dirName" @click="addDirectory">
        <i class="fa fa-folder-plus me-1"></i>Add
      </button>
    </div>
  </div>
</template>

<script>
import { components } from "django-airavata-common-ui";
import { session } from "django-airavata-api";

export default {
  name: "UserStorageCreateView",
  components: {
    uppy: components.Uppy,
  },
  props: {
    userStoragePath: {
      required: true,
    },
    storagePath: {
      required: true,
    },
  },
  data() {
    return {
      dirName: null,
    };
  },
  computed: {
    uploadEndpoint() {
      return "/api/user-storage/" + this.storagePath;
    },
    username() {
      return session.Session.username;
    },
    userHasWriteAccess() {
      return this.userStoragePath.user_has_write_access;
    },
  },
  methods: {
    uploadFinished() {
      this.$refs["file-upload"].reset();
      this.$emit("upload-finished");
    },
    addDirectory() {
      this.$emit("add-directory", this.dirName);
      this.dirName = null;
    },
  },
};
</script>
