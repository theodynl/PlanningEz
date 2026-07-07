import { useEffect, useState } from "react";
import { api } from "./api";
import type { Meta, Project, ProjectSummary, WorkPackageSummary } from "./types";
import type { Task } from "./types";
import { GanttChart } from "./components/GanttChart";
import { TaskTable } from "./components/TaskTable";
import { TaskEditor } from "./components/TaskEditor";
import { NewProjectWizard } from "./components/NewProjectWizard";
import { WorkPackageEditor } from "./components/WorkPackageEditor";
import { ContextMenu, type MenuItem } from "./components/ContextMenu";
import { descendantIds, candidateParents } from "./hierarchy";

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
  const [menu, setMenu] = useState<{ task: Task; x: number; y: number } | null>(null);
  const [wpEditorOpen, setWpEditorOpen] = useState(false);
  const [editingWpId, setEditingWpId] = useState<string | null>(null);
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

  // Inline table edits and Gantt drag/resize all funnel through here.
  const patchTask = async (task: Task, patch: Parameters<typeof api.updateTask>[2]) => {
    if (!current) return;
    try {
      await api.updateTask(current.project_id, task.task_id, patch);
      await reloadCurrent();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const moveTask = (task: Task, newStartISO: string) =>
    patchTask(task, { constraint_date: newStartISO });

  const resizeTask = (task: Task, newDuration: number) =>
    patchTask(task, { duration: newDuration });

  // --- Hierarchy actions (context menu) ---
  const setParent = (task: Task, parentId: string | null) =>
    patchTask(task, parentId ? { parent_id: parentId } : { clear_parent: true });

  const addSubtask = async (parent: Task) => {
    if (!current) return;
    try {
      await api.addTask(current.project_id, {
        name: "Nouvelle sous-tâche",
        duration: 1,
        parent_id: parent.task_id,
      });
      await reloadCurrent();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const indentTask = (task: Task) => {
    if (!current) return;
    const idx = current.tasks.findIndex((t) => t.task_id === task.task_id);
    const prev = current.tasks[idx - 1];
    if (prev && !descendantIds(current.tasks, task.task_id).has(prev.task_id)) {
      setParent(task, prev.task_id);
    }
  };

  const outdentTask = (task: Task) => {
    if (!current || !task.parent_id) return;
    const parent = current.tasks.find((t) => t.task_id === task.parent_id);
    setParent(task, parent?.parent_id ?? null);
  };

  const openContext = (task: Task, x: number, y: number) => setMenu({ task, x, y });

  // --- Work Package library management ---
  const openNewWp = () => {
    setEditingWpId(null);
    setWpEditorOpen(true);
  };
  const openEditWp = (id: string) => {
    setEditingWpId(id);
    setWpEditorOpen(true);
  };
  const onWpSaved = async () => {
    setWpEditorOpen(false);
    await refreshLists();
  };
  const deleteWp = async (wp: WorkPackageSummary) => {
    if (!confirm(`Supprimer le Work Package « ${wp.name} » ?`)) return;
    try {
      await api.deleteWorkPackage(wp.work_package_id);
      await refreshLists();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const buildMenu = (task: Task): MenuItem[] => {
    if (!current) return [];
    const idx = current.tasks.findIndex((t) => t.task_id === task.task_id);
    const prev = current.tasks[idx - 1];
    const forbidden = descendantIds(current.tasks, task.task_id);
    const canIndent = !!prev && !forbidden.has(prev.task_id) && prev.task_id !== task.parent_id;
    const parents = candidateParents(current.tasks, task).filter(
      (p) => p.task_id !== task.parent_id
    );
    return [
      { label: "Modifier…", onClick: () => openEditTask(task) },
      { label: "Ajouter une sous-tâche", onClick: () => addSubtask(task) },
      { label: "", separator: true },
      { label: "Indenter (rendre fille)", onClick: () => indentTask(task), disabled: !canIndent },
      { label: "Désindenter", onClick: () => outdentTask(task), disabled: !task.parent_id },
      {
        label: "Définir la tâche mère",
        submenu: [
          {
            label: "— Aucune (racine) —",
            onClick: () => setParent(task, null),
            disabled: !task.parent_id,
          },
          ...parents.map((p) => ({
            label: p.name,
            onClick: () => setParent(task, p.task_id),
          })),
        ],
      },
      { label: "", separator: true },
      { label: "Supprimer", danger: true, onClick: () => deleteTask(task) },
    ];
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

          <div className="wp-lib-head">
            <h3>Bibliothèque de Work Packages</h3>
            <button className="btn-link" onClick={openNewWp}>
              + Nouveau
            </button>
          </div>
          <ul className="wp-list">
            {workPackages.map((wp) => (
              <li key={wp.work_package_id}>
                <button
                  className="wp-item"
                  title="Modifier"
                  onClick={() => openEditWp(wp.work_package_id)}
                >
                  <span className="wp-code">{wp.code}</span>
                  <span className="wp-name">{wp.name}</span>
                  <span className="wp-tasks">{wp.tasks}</span>
                </button>
                <button className="wp-del" title="Supprimer" onClick={() => deleteWp(wp)}>
                  ×
                </button>
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
                <GanttChart
                  tasks={current.tasks}
                  onSelect={openEditTask}
                  onMove={moveTask}
                  onResize={resizeTask}
                  onContext={openContext}
                />
              ) : (
                <TaskTable
                  tasks={current.tasks}
                  onEdit={openEditTask}
                  onAdd={openAddTask}
                  onDelete={deleteTask}
                  onInline={patchTask}
                  onContext={openContext}
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

      {menu && current && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          items={buildMenu(menu.task)}
          onClose={() => setMenu(null)}
        />
      )}

      {wpEditorOpen && (
        <WorkPackageEditor
          workPackageId={editingWpId}
          meta={meta}
          onSaved={onWpSaved}
          onClose={() => setWpEditorOpen(false)}
        />
      )}
    </div>
  );
}
