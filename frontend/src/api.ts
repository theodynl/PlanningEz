import type {
  Meta,
  Project,
  ProjectSummary,
  Task,
  Dependency,
  WorkPackageSummary,
} from "./types";

export interface TaskInput {
  name: string;
  duration?: number;
  task_type?: string;
  parent_id?: string | null;
  responsible?: string | null;
  progress?: number;
  is_milestone?: boolean;
}

export interface TaskPatch {
  name?: string;
  duration?: number;
  status?: string;
  progress?: number;
  responsible?: string | null;
  parent_id?: string | null;
  clear_parent?: boolean;
  constraint_date?: string | null;
  clear_constraint?: boolean;
}

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

  addTask: (projectId: string, body: TaskInput) =>
    request<Task>(`/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateTask: (projectId: string, taskId: string, body: TaskPatch) =>
    request<Task>(`/projects/${projectId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteTask: (projectId: string, taskId: string) =>
    request<{ status: string }>(`/projects/${projectId}/tasks/${taskId}`, {
      method: "DELETE",
    }),

  addDependency: (
    projectId: string,
    body: { predecessor_id: string; successor_id: string; dependency_type?: string; lag?: number }
  ) =>
    request<Dependency>(`/projects/${projectId}/dependencies`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  previewWbs: (format: string, content: string) =>
    request<{ node_count: number; depth: number }>("/wbs/preview", {
      method: "POST",
      body: JSON.stringify({ format, content }),
    }),

  listWorkPackages: () => request<WorkPackageSummary[]>("/work-packages"),

  exportUrl: (id: string, format: string) =>
    `${BASE}/projects/${id}/export/${format}`,
};
