export interface Task {
  task_id: string;
  name: string;
  duration: number;
  unit: string;
  task_type: string;
  status: string;
  progress: number;
  start_date: string | null;
  end_date: string | null;
  constraint_date: string | null;
  parent_id: string | null;
  responsible: string | null;
  is_milestone: boolean;
  total_slack: number;
  on_critical_path: boolean;
}

export interface Dependency {
  dep_id: string;
  predecessor_id: string;
  successor_id: string;
  dependency_type: string;
  lag: number;
}

export interface Resource {
  resource_id: string;
  name: string;
  role: string;
  daily_cost: number;
}

export interface Project {
  project_id: string;
  name: string;
  start_date: string | null;
  total_duration: number;
  tasks: Task[];
  dependencies: Dependency[];
  resources: Resource[];
  critical_path_tasks: string[];
}

export interface ProjectSummary {
  project_id: string;
  name: string;
  tasks: number;
  resources: number;
  start_date: string | null;
}

export interface WorkPackageSummary {
  work_package_id: string;
  name: string;
  code: string;
  discipline: string;
  version: string;
  tasks: string;
}

export interface Meta {
  start_modes: string[];
  disciplines: string[];
  resource_roles: string[];
  task_types: string[];
  task_statuses: string[];
  dependency_types: string[];
  connect_modes: string[];
  export_formats: string[];
}
