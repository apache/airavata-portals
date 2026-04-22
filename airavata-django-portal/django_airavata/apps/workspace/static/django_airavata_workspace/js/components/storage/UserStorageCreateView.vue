<template>
  <div v-if="userHasWriteAccess" class="d-flex gap-2 mb-2">
    <uppy
      ref="fileUpload"
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

<script setup lang="ts">
import { ref, computed } from "vue";
import { components } from "django-airavata-common-ui";

const Uppy = components.Uppy;

interface UserStoragePathLike {
  user_has_write_access: boolean;
}

const props = defineProps<{
  userStoragePath: UserStoragePathLike;
  storagePath: string;
}>();

const emit = defineEmits<{
  "upload-finished": [];
  "add-directory": [dirName: string];
}>();

const fileUpload = ref<{ reset: () => void } | null>(null);
const dirName = ref<string | null>(null);

const uploadEndpoint = computed(() => `/api/user-storage/${props.storagePath}`);
const userHasWriteAccess = computed(() => props.userStoragePath.user_has_write_access);

function uploadFinished() {
  fileUpload.value?.reset();
  emit("upload-finished");
}

function addDirectory() {
  if (dirName.value) {
    emit("add-directory", dirName.value);
    dirName.value = null;
  }
}

// Register uppy as a component
const uppy = Uppy;
</script>
