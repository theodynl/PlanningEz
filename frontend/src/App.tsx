import { useEffect, useState } from "react";
import { api } from "./api";
import type { Meta, Project, ProjectSummary, WorkPackageSummary } from "./types";
import type { Task } from "./types";
import { GanttChart } from "./components/GanttChart";
import { TaskTable } from "./components/TaskTable";
import { TaskEditor } from "./components/TaskEditor";
import { NewProjectWizard } from "./components/NewProjectWizard";

type Tab = "gantt" | "tasks";

export function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [workPackages, setWorkPackages] = useState<WorkPackageSummary[]>([]);
  const [current, setCurrent] = useState<Project | null>(null);
  const [tab, setTab] = useState<Tab>("gantt");
  const [wizardOpen, setWizardOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshLists = async () => {
    setProjects(await api.listProjects());
    setWorkPackages(await api.listWorkPackages());
  };

  useEffect(() => {
    api.getMeta().then(setMeta).catch((e) => setError(e.message));
    refreshLists().catch((e) => setError((e as Error).message));
  }, []);

  const openProject = async (id: string) => {
    try {
      setCurrent(await api.schedule(id)); // schedule on open so the Gantt is populated
      setTab("gantt");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const onCreated = async (project: Project) => {
    setWizardOpen(false);
    await refreshLists();
    // Schedule immediately so the Gantt shows dates.
    try {
      setCurrent(await api.schedule(project.project_id));
    } catch {
      setCurrent(project);
    }
    setTab("gantt");
  };

  const recalc = async () => {
    if (!current) return;
    try {
      setCurrent(await api.schedule(current.project_id));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  // Reload the project after an edit and re-run the schedule so the Gantt and
  // slack/critical-path indicators stay in sync.
  const reloadCurrent = async () => {
    if (!current) return;
    try {
      setCurrent(await api.schedule(current.project_id));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const openAddTask = () => {
    setEditingTask(null);
    setEditorOpen(true);
  };

  const openEditTask = (task: Task) => {
    setEditingTask(task);
    setEditorOpen(true);
  };

  const deleteTask = async (task: Task) => {
    if (!current) return;
    if (!confirm(`Supprimer la tâche « ${task.name} » ?`)) return;
    try {
      await api.deleteTask(current.project_id, task.task_id);
      await reloadCurrent();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const removeProject = async (id: string) => {
    await api.deleteProject(id);
    if (current?.project_id === id) setCurrent(null);
    await refreshLists();
  };

  const criticalCount = current?.tasks.filter((t) => t.on_critical_path).length ?? 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◆</span> PlanningEz
        </div>
        <div className="brand-sub">Assistant de planification · WBS · Work Packages</div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <button className="btn-primary block" onClick={() => setWizardOpen(true)}>
            + Nouveau projet
          </button>

          <h3>Projets</h3>
          {projects.length === 0 && <p className="muted">Aucun projet.</p>}
          <ul className="proj-list">
            {projects.map((p) => (
              <li
                key={p.project_id}
                className={current?.project_id === p.project_id ? "active" : ""}
              >
                <button className="proj-btn" onClick={() => openProject(p.project_id)}>
                  <span className="proj-name">{p.name}</span>
                  <span className="proj-meta">{p.tasks} tâches</span>
                </button>
                <button
                  className="proj-del"
                  title="Supprimer"
                  onClick={() => removeProject(p.project_id)}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>

          <h3>Bibliothèque de Work Packages</h3>
          <ul className="wp-list">
            {workPackages.map((wp) => (
              <li key={wp.work_package_id}>
                <span className="wp-code">{wp.code}</span>
                <span className="wp-name">{wp.name}</span>
                <span className="wp-tasks">{wp.tasks}</span>
              </li>
            ))}
          </ul>
        </aside>

        <main className="content">
          {error && (
            <div className="error-banner" onClick={() => setError(null)}>
              {error} (cliquer pour fermer)
            </div>
          )}

          {!current && (
            <div className="placeholder">
              <h2>Bienvenue sur PlanningEz</h2>
              <p>
                Créez un projet à partir de zéro, d'un WBS structuré en JSON, ou en assemblant
                des Work Packages réutilisables.
              </p>
              <button className="btn-primary" onClick={() => setWizardOpen(true)}>
                + Créer un projet
              </button>
            </div>
          )}

          {current && (
            <>
              <div className="project-header">
                <div>
                  <h2>{current.name}</h2>
                  <div className="project-stats">
                    {current.tasks.length} tâches · {current.dependencies.length} dépendances ·{" "}
                    {criticalCount} sur le chemin critique
                  </div>
                </div>
                <div className="header-actions">
                  <button className="btn-secondary" onClick={recalc}>
                    ↻ Recalculer le planning
                  </button>
                  {meta?.export_formats.map((fmt) => (
                    <a
                      key={fmt}
                      className="btn-export"
                      href={api.exportUrl(current.project_id, fmt)}
                    >
                      ⇩ {fmt}
                    </a>
                  ))}
                </div>
              </div>

              <div className="tabs">
                <button className={tab === "gantt" ? "active" : ""} onClick={() => setTab("gantt")}>
                  Diagramme de Gantt
                </button>
                <button className={tab === "tasks" ? "active" : ""} onClick={() => setTab("tasks")}>
                  Tableau des tâches
                </button>
              </div>

              {tab === "gantt" ? (
                <GanttChart tasks={current.tasks} onSelect={openEditTask} />
              ) : (
                <TaskTable
                  tasks={current.tasks}
                  onEdit={openEditTask}
                  onAdd={openAddTask}
                  onDelete={deleteTask}
                />
              )}
            </>
          )}
        </main>
      </div>

      {wizardOpen && (
        <NewProjectWizard
          workPackages={workPackages}
          onCreated={onCreated}
          onClose={() => setWizardOpen(false)}
        />
      )}

      {editorOpen && current && (
        <TaskEditor
          project={current}
          task={editingTask}
          meta={meta}
          onChanged={reloadCurrent}
          onClose={() => setEditorOpen(false)}
        />
      )}
    </div>
  );
}
