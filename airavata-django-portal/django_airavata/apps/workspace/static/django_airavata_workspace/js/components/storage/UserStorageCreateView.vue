<template>
  <div v-if="userHasWriteAccess" class="d-flex gap-2 mb-2">
    <uppy
      ref="file-upload"
      :xhr-upload-endpoint="uploadEndpoint"
      :tus-upload-finish-endpoint="uploadEndpoint"
      @upload-finished="uploadFinished"
      multiple
    />
    <div class="input-group input-group-sm" style="max-width: 300px;">
      <input class="form-control"
        v-model="dirName"
        placeholder="New directory name"
        @keydown.enter="addDirectory"
      />
      <button class="btn btn-outline-secondary" @click="addDirectory" :disabled="!this.dirName">
        <i class="fa fa-folder-plus me-1"></i>Add
      </button>
    </div>
  </div>
</template>

<script>
import { components } from "django-airavata-common-ui";
import { session } from "django-airavata-api";

export default {
  name: "user-storage-create-view",
  components: {
    uppy: components.Uppy,
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
  data() {
    return {
      dirName: null,
    };
  },
  props: {
    userStoragePath: {
      required: true,
    },
    storagePath: {
      required: true,
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
