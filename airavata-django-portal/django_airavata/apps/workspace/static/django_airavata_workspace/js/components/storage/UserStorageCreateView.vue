<template>
  <div class="space-y-4">
    <p class="inline-flex items-center gap-1 text-sm text-muted-foreground">
      <FolderOpen class="size-4" /> {{ username }}
    </p>
    <div class="flex flex-wrap gap-4" v-if="userHasWriteAccess">
      <div class="flex-1">
        <uppy
          class="mb-1"
          ref="file-upload"
          :xhr-upload-endpoint="uploadEndpoint"
          :tus-upload-finish-endpoint="uploadEndpoint"
          @upload-finished="uploadFinished"
          multiple
        />
      </div>
      <div class="flex-1">
        <div class="flex">
          <Input
            class="rounded-r-none"
            v-model="dirName"
            placeholder="New directory name"
            @keydown.enter="addDirectory"
          />
          <Button
            variant="outline"
            class="rounded-l-none"
            @click="addDirectory"
            :disabled="!dirName"
            >Add directory
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { FolderOpen } from "@lucide/vue";
import { components } from "django-airavata-common-ui";
import { session } from "django-airavata-api";

export default {
  name: "user-storage-create-view",
  components: {
    FolderOpen,
    uppy: components.Uppy,
  },
  computed: {
    uploadEndpoint() {
      // This endpoint can handle XHR upload or a TUS uploadURL
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
