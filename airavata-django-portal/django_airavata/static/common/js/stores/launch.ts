import { defineStore } from "pinia";
import { computed, reactive, ref, watch } from "vue";
import type {
  Application,
  ExperimentDraft,
  IODescriptor,
  InterfaceDescriptor,
  InputValue,
  PreviewResponse,
  ResourceProfile,
  RuntimeChoice,
  StorageRef,
  UserStorage,
} from "./launch-types";

const EMPTY_RUNTIME: RuntimeChoice = {
  compute_resource_id: null,
  partition: null,
  walltime: "01:00:00",
  nodes: 1,
  cpus_per_node: 1,
};

function makeDraft(): ExperimentDraft {
  return {
    name: "",
    project_id: null,
    description: "",
    app_id: null,
    interface_name: null,
    inputs: {},
    outputs: {},
    runtime: { ...EMPTY_RUNTIME },
  };
}

function isStorageRef(v: InputValue): v is StorageRef {
  return typeof v === "object" && v !== null && "storage_id" in v && "path" in v;
}

function inputHasValue(io: IODescriptor, v: InputValue): boolean {
  if (v === null || v === undefined) return !io.required;
  if (io.type === "file" || io.type === "dir") {
    return isStorageRef(v) && v.path.length > 0 && v.storage_id.length > 0;
  }
  return true;
}

export const useLaunchStore = defineStore("launch", () => {
  const draft = reactive<ExperimentDraft>(makeDraft());
  const pickedApp = ref<Application | null>(null);
  const profile = ref<ResourceProfile | null>(null);
  const storages = ref<UserStorage[]>([]);
  const preview = ref<PreviewResponse | null>(null);
  const previewError = ref<string | null>(null);
  const previewLoading = ref(false);
  const lastPreviewedHash = ref<string | null>(null);

  function setMeta(m: { name: string; project_id: string | null; description: string }) {
    if (draft.project_id !== m.project_id) {
      draft.runtime = { ...EMPTY_RUNTIME };
      profile.value = null;
    }
    draft.name = m.name;
    draft.project_id = m.project_id;
    draft.description = m.description;
  }

  function pickApp(a: Application) {
    pickedApp.value = a;
    draft.app_id = a.app_id;
    draft.interface_name = null;
    draft.inputs = {};
    draft.outputs = {};
  }

  function pickInterface(name: string) {
    draft.interface_name = name;
    draft.inputs = {};
    draft.outputs = {};
  }

  function setInput(name: string, value: InputValue) {
    draft.inputs[name] = value;
  }

  function setOutput(name: string, value: StorageRef) {
    draft.outputs[name] = value;
  }

  function setRuntime(r: RuntimeChoice) {
    draft.runtime = { ...r };
  }

  const pickedInterface = computed<InterfaceDescriptor | null>(() => {
    const a = pickedApp.value;
    const n = draft.interface_name;
    if (!a || !n) return null;
    return a.interfaces.find((i) => i.name === n) ?? null;
  });

  const tab1Valid = computed(() => {
    if (!draft.name || !draft.project_id || !draft.app_id || !draft.interface_name) return false;
    const iface = pickedInterface.value;
    if (!iface) return false;
    for (const io of iface.inputs) {
      if (!inputHasValue(io, draft.inputs[io.name] ?? null)) return false;
    }
    for (const io of iface.outputs) {
      if (io.type !== "file" && io.type !== "dir") continue;
      const v = draft.outputs[io.name];
      if (!v) {
        if (io.required) return false;
        continue;
      }
      if (!v.path || !v.storage_id) return false;
    }
    return true;
  });

  const tab2Valid = computed(() => {
    const r = draft.runtime;
    return Boolean(r.compute_resource_id && r.partition && r.walltime && r.nodes >= 1 && r.cpus_per_node >= 1);
  });

  // FNV-1a 32-bit string hash on JSON of the draft. Stable, fast, no deps.
  const draftHash = computed(() => {
    const s = JSON.stringify(draft);
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 0x01000193);
    }
    return (h >>> 0).toString(16);
  });

  function setStorages(s: UserStorage[]) {
    storages.value = s;
  }

  function setProfile(p: ResourceProfile | null) {
    profile.value = p;
  }

  const STORAGE_KEY = "launch-draft";

  function persist(draftValue: ExperimentDraft) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(draftValue)); } catch { /* ignore quota */ }
  }

  function clearPersisted() {
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* noop */ }
  }

  function hydrate() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<ExperimentDraft>;
      Object.assign(draft, makeDraft(), parsed);
    } catch {
      /* ignore corrupted draft */
    }
  }

  watch(draft, (d) => persist(d), { deep: true, flush: "sync" });

  function reset() {
    Object.assign(draft, makeDraft());
    pickedApp.value = null;
    profile.value = null;
    preview.value = null;
    previewError.value = null;
    previewLoading.value = false;
    lastPreviewedHash.value = null;
    clearPersisted();
  }

  return {
    draft,
    pickedApp,
    pickedInterface,
    profile,
    storages,
    preview,
    previewError,
    previewLoading,
    lastPreviewedHash,
    tab1Valid,
    tab2Valid,
    draftHash,
    setMeta,
    pickApp,
    pickInterface,
    setInput,
    setOutput,
    setRuntime,
    setStorages,
    setProfile,
    hydrate,
    reset,
  };
});
