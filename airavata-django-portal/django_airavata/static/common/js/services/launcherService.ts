import type {
  Application,
  ExperimentDraft,
  PreviewResponse,
  ResourceProfile,
  UserStorage,
} from "../stores/launch-types";

const API = "/api/launcher";

async function getJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    ...init,
    credentials: "same-origin",
    headers: { Accept: "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: res.statusText }));
    throw Object.assign(new Error(body.message ?? res.statusText), { status: res.status, body });
  }
  return res.json() as Promise<T>;
}

function csrf(): string {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m?.[1] ?? "";
}

export const launcherService = {
  listApplications(params: { category?: string; search?: string } = {}): Promise<{ results: Application[] }> {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    if (params.search) qs.set("search", params.search);
    const tail = qs.toString();
    return getJson(`${API}/applications/${tail ? "?" + tail : ""}`);
  },

  getApplication(appId: string): Promise<Application> {
    return getJson(`${API}/applications/${encodeURIComponent(appId)}/`);
  },

  getProjectResourceProfile(projectId: string): Promise<ResourceProfile> {
    return getJson(`${API}/projects/${encodeURIComponent(projectId)}/resource-profile/`);
  },

  listUserStorages(): Promise<{ results: UserStorage[] }> {
    return getJson(`${API}/storages/`);
  },

  listProjects(): Promise<{ results: Array<{ project_id: string; name: string }> }> {
    return getJson(`${API}/projects/`);
  },

  generatePreview(draft: ExperimentDraft, signal?: AbortSignal): Promise<PreviewResponse> {
    return getJson(`${API}/experiment-drafts/preview/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(draft),
      signal,
    });
  },

  launchExperiment(draft: ExperimentDraft): Promise<{ experiment_id: string }> {
    return getJson(`${API}/experiment-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(draft),
    });
  },
};
