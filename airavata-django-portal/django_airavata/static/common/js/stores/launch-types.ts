export type ScalarType = "string" | "int" | "float" | "bool" | "enum" | "multi-string";
export type FileType = "file" | "dir";
export type IOType = ScalarType | FileType;

export interface IODescriptor {
  name: string;
  type: IOType;
  required?: boolean;
  options?: string[]; // for enum
}

export interface InterfaceDescriptor {
  name: string;
  inputs: IODescriptor[];
  outputs: IODescriptor[];
}

export interface AppContent {
  kind: "tarball" | "github";
  url: string;
}

export interface Application {
  app_id: string;
  name: string;
  category: string;
  content: AppContent;
  interfaces: InterfaceDescriptor[];
}

export interface Partition {
  name: string;
  max_walltime: string;
  max_nodes: number;
  cpus_per_node: number;
}

export interface MappedStorage {
  storage_id: string;
  scratch_path: string;
}

export interface ComputeResource {
  compute_resource_id: string;
  name: string;
  mapped_storage: MappedStorage;
  partitions: Partition[];
}

export interface ResourceProfile {
  project_id: string;
  allocation_id: string;
  compute_resources: ComputeResource[];
}

export interface UserStorage {
  storage_id: string;
  name: string;
  is_primary: boolean;
}

export type StorageRef = { storage_id: string; path: string };
export type ScalarValue = string | number | boolean;
export type InputValue = ScalarValue | StorageRef | null;

export interface RuntimeChoice {
  compute_resource_id: string | null;
  partition: string | null;
  walltime: string;
  nodes: number;
  cpus_per_node: number;
}

export interface ExperimentDraft {
  name: string;
  project_id: string | null;
  description: string;
  app_id: string | null;
  interface_name: string | null;
  inputs: Record<string, InputValue>;
  outputs: Record<string, StorageRef>;
  runtime: RuntimeChoice;
}

export interface PreviewResponse {
  invocation_command: string;
  script_contents: string;
  warnings: string[];
}
