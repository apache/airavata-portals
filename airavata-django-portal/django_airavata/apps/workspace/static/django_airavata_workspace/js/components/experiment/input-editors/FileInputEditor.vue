<template>
  <div class="file-input-editor">
    <div v-if="isDataProductURI && dataProduct" class="d-flex">
      <UserStorageLink
        class="me-auto"
        :data-product-uri="(dataProduct as Record<string, unknown>).productUri as string"
        :mime-type="(dataProduct as Record<string, unknown>).mime_type as string"
        :file-name="(dataProduct as Record<string, unknown>).productName as string"
      />
      <DeleteLink
        v-if="!readOnly && (dataProduct as Record<string, unknown>).isInputFileUpload"
        class="ms-2"
        @delete="deleteDataProduct"
      >
        Are you sure you want to delete input file
        <strong>{{ (dataProduct as Record<string, unknown>).productName }}</strong
        >?
      </DeleteLink>
      <a v-else-if="!readOnly" class="ms-2 text-secondary" @click="unselect">
        Unselect
        <i class="fa fa-times" aria-hidden="true"></i>
      </a>
    </div>
    <InputFileSelector
      v-if="!readOnly && (!isDataProductURI || uploading)"
      :selected-data-product-u-r-is="selectedDataProductURIs"
      @uploadstart="uploadStart"
      @uploadend="uploadEnd"
      @selected="fileSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { models, services, utils } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import { useInputEditor } from "@/composables/useInputEditor";
import InputFileSelector from "./InputFileSelector.vue";
import UserStorageLink from "../../storage/storage-edit/UserStorageLink.vue";

const DeleteLink = components.DeleteLink;

type InputDataObjectType = InstanceType<typeof models.InputDataObjectType>;
type Experiment = InstanceType<typeof models.Experiment>;
type DataProduct = InstanceType<typeof models.DataProduct>;

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    experimentInput: InputDataObjectType;
    experiment?: Experiment;
    id: string;
    readOnly?: boolean;
  }>(),
  { modelValue: null, experiment: undefined, readOnly: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [messages: string[]];
  uploadstart: [];
  uploadend: [];
}>();

const { data, valueChanged } = useInputEditor(
  props,
  (_, v) => emit("update:modelValue", v),
  () => emit("valid"),
  (msgs) => emit("invalid", msgs),
);

const dataProduct = ref<DataProduct | null>(null);
const uploading = ref(false);

const isDataProductURI = computed(
  () =>
    data.value && typeof data.value === "string" && data.value.startsWith("airavata-dp://"),
);

const selectedDataProductURIs = computed(() => {
  if (
    props.experimentInput.type === models.DataType.URI_COLLECTION &&
    props.experimentInput.value
  ) {
    return props.experimentInput.value.split(",");
  } else {
    return [];
  }
});

watch(data, (value, oldValue) => {
  if (isDataProductURI.value && value !== oldValue) {
    loadDataProduct(value as string);
  }
});

onMounted(() => {
  if (isDataProductURI.value) {
    loadDataProduct(data.value as string);
  }
});

function loadDataProduct(dataProductURI: string) {
  services.DataProductService.retrieve({ lookup: dataProductURI })
    .then((dp: unknown) => {
      const product = dp as DataProduct;
      if ((product as unknown as Record<string, unknown>).download_url === null) {
        data.value = null;
        valueChanged();
      } else {
        dataProduct.value = product;
      }
    })
    .catch(() => {
      data.value = null;
      valueChanged();
    });
}

function deleteDataProduct() {
  utils.FetchUtils.delete(
    "/api/delete-file?data-product-uri=" + encodeURIComponent(data.value as string),
    { ignoreErrors: true },
  )
    .then(() => {
      data.value = null;
      valueChanged();
    })
    .catch((err: Record<string, unknown>) => {
      if ((err.details as Record<string, unknown>)?.status === 404) {
        data.value = null;
        valueChanged();
      } else {
        throw err;
      }
    })
    .catch((utils as unknown as Record<string, unknown>).FetchUtils as unknown as (_e: unknown) => void);
}

function unselect() {
  data.value = null;
  valueChanged();
}

function fileSelected(dataProductURI: string, dp?: DataProduct) {
  data.value = dataProductURI;
  if (!dp) {
    loadDataProduct(dataProductURI);
  } else {
    dataProduct.value = dp;
  }
  valueChanged();
}

function uploadStart() {
  uploading.value = true;
  emit("uploadstart");
}

function uploadEnd() {
  uploading.value = false;
  emit("uploadend");
}
</script>

<style scoped>
.input-file-option {
  flex: 1 1 50%;
}
</style>
