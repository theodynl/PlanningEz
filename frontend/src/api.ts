import type {
  Meta,
  Project,
  ProjectSummary,
  WorkPackageSummary,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore non-JSON errors */
    }
    throw new Error(detail);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  getMeta: () => request<Meta>("/meta"),

  listProjects: () => request<ProjectSummary[]>("/projects"),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  deleteProject: (id: string) =>
    request<{ status: string }>(`/projects/${id}`, { method: "DELETE" }),

  createProject: (body: Record<string, unknown>) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(body) }),

  generateProject: (body: Record<string, unknown>) =>
    request<Project>("/projects/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  schedule: (id: string) => request<Project>(`/projects/${id}/schedule`),

  previewWbs: (format: string, content: string) =>
    request<{ node_count: number; depth: number }>("/wbs/preview", {
      method: "POST",
      body: JSON.stringify({ format, content }),
    }),

  listWorkPackages: () => request<WorkPackageSummary[]>("/work-packages"),

  exportUrl: (id: string, format: string) =>
    `${BASE}/projects/${id}/export/${format}`,
};
