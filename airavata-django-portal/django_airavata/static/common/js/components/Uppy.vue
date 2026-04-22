<template>
  <div class="custom-Uppy">
    <div ref="dragDrop" />
    <div ref="statusBar" />
    <div v-if="restrictionFailed" class="alert alert-danger mt-1">
      {{ restrictionFailedMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
/* eslint-disable vue/multi-word-component-names */
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { services, utils } from "django-airavata-api";

import Uppy from "@uppy/core";
import DragDrop from "@uppy/drag-drop";
import StatusBar from "@uppy/status-bar";
import Tus from "@uppy/tus";
import XHRUpload from "@uppy/xhr-upload";

import "@uppy/core/dist/style.min.css";
import "@uppy/status-bar/dist/style.min.css";
import "@uppy/drag-drop/dist/style.min.css";

const props = withDefaults(defineProps<{
  xhrUploadEndpoint: string;
  // endpoint should accept POST request. Request will include form data with
  // the key uploadURL.
  tusUploadFinishEndpoint?: string;
  multiple?: boolean;
}>(), {
  tusUploadFinishEndpoint: undefined,
  multiple: false,
});

const emit = defineEmits<{
  "upload-success": [result: unknown];
  "upload-started": [];
  "upload-finished": [];
}>();

const dragDrop = ref<HTMLElement | null>(null);
const statusBar = ref<HTMLElement | null>(null);
// Uppy's published TypeScript types are incomplete; using InstanceType here.
type UppyAny = InstanceType<typeof Uppy>;
let uppy: UppyAny | null = null;

const restrictionFailedMessage = ref<string | null>(null);
const settings = ref<{ fileUploadMaxFileSize?: number; tusEndpoint?: string } | null>(null);
let uploadFilesCount = 0;

const maxFileUploadSizeMB = computed(() =>
  settings.value ? (settings.value.fileUploadMaxFileSize ?? 0) / 1024 / 1024 : 0,
);

const maxFileUploadSizeMessage = computed(() => {
  if (maxFileUploadSizeMB.value) {
    return "Max file upload size is " + Math.round(maxFileUploadSizeMB.value) + " MB";
  } else {
    return null;
  }
});

const restrictionFailed = computed(() => {
  // eslint-disable-next-line eqeqeq -- intentionally loose (null/undefined match)
  return restrictionFailedMessage.value != null;
});

watch(
  () => props.xhrUploadEndpoint,
  (val: string) => {
    // Update the xhrUploadEndpoint configuration on XHRUpload whenever it changes
    if (uppy && settings.value && !settings.value.tusEndpoint) {
      uppy.getPlugin("XHRUpload")?.setOptions({ endpoint: val });
    }
  },
);

onMounted(() => {
  services.SettingsService.get().then((s: typeof settings.value) => {
    settings.value = s;
    initUppy();
  });
});

onUnmounted(() => {
  if (uppy) {
    uppy.close();
  }
});

function initUppy(): void {
  // Uppy v3's constructor can be called as a function in some versions; cast to avoid TS error
  uppy = new Uppy({
    autoProceed: true,
    debug: true,
    restrictions: {
      maxNumberOfFiles: props.multiple ? null : 1,
      maxFileSize: settings.value?.fileUploadMaxFileSize,
    },
  });
  uppy.use(DragDrop, {
    target: dragDrop.value!,
    note: maxFileUploadSizeMessage.value ?? undefined,
  });
  uppy.use(StatusBar, {
    target: statusBar.value!,
    hideUploadButton: true,
    hideAfterFinish: false,
  });
  if (settings.value?.tusEndpoint) {
    uppy.use(Tus, { endpoint: settings.value.tusEndpoint });
    uppy.on("upload-success", (...args: unknown[]) => {
      const response = args[1] as { uploadURL?: string };
      const data = new FormData();
      data.append("uploadURL", response.uploadURL ?? "");
      utils.FetchUtils.post(props.tusUploadFinishEndpoint, data, "", {
        showSpinner: false,
      }).then((result: unknown) => {
        emit("upload-success", result);
        fileFinishedUploading();
      });
    });
  } else {
    uppy.use(XHRUpload, {
      endpoint: props.xhrUploadEndpoint,
      withCredentials: true,
      headers: {
        "X-CSRFToken": utils.FetchUtils.getCSRFToken(),
      },
      fieldName: "file",
    });
    uppy.on("upload-success", (...args: unknown[]) => {
      const response = args[1] as { body?: unknown };
      emit("upload-success", response.body);
      fileFinishedUploading();
    });
  }
  uppy.on("upload", (...args: unknown[]) => {
    const data = args[0] as { fileIDs?: string[] };
    emit("upload-started");
    uploadFilesCount = data.fileIDs?.length ?? 0;
  });
  uppy.on("complete", () => {
    restrictionFailedMessage.value = null;
  });
  uppy.on("restriction-failed", (...args: unknown[]) => {
    const file = args[0] as { name?: string };
    const error = args[1] as { message?: string };
    restrictionFailedMessage.value = `${file.name ?? "file"}: ${error.message ?? "error"}`;
  });
  uppy.on("upload-error", () => {
    fileFinishedUploading();
  });
}

function fileFinishedUploading(): void {
  uploadFilesCount--;
  if (uploadFilesCount <= 0) {
    emit("upload-finished");
  }
}

function reset(): void {
  // uppy.reset() may not be in all Uppy type versions; call via double-cast
  if (uppy) {
    const uppyAny = uppy as unknown as Record<string, unknown>;
    if (typeof uppyAny["reset"] === "function") {
      (uppyAny["reset"] as () => void)();
    }
  }
}

defineExpose({ reset });
</script>

<style scoped>
.custom-Uppy :deep(.uppy-DragDrop-inner) {
  padding: 5px 0px;
}
.custom-Uppy :deep(.UppyIcon) {
  display: none;
}
.custom-Uppy :deep(.uppy-DragDrop-label) {
  margin-bottom: 0px;
}
.custom-Uppy :deep(.uppy-StatusBar) {
  background-color: inherit;
}
</style>
