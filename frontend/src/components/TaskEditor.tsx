import { useMemo, useState } from "react";
import { api } from "../api";
import type { Meta, Project, Task } from "../types";

interface Props {
  project: Project;
  task: Task | null; // null = create mode
  meta: Meta | null;
  onChanged: () => void; // parent reloads + reschedules
  onClose: () => void;
}

export function TaskEditor({ project, task, meta, onChanged, onClose }: Props) {
  const isEdit = task !== null;
  const [name, setName] = useState(task?.name ?? "");
  const [isMilestone, setIsMilestone] = useState(task?.is_milestone ?? false);
  const [duration, setDuration] = useState(task?.duration ?? 1);
  const [status, setStatus] = useState(task?.status ?? "not_started");
  const [progress, setProgress] = useState(task?.progress ?? 0);
  const [responsible, setResponsible] = useState(task?.responsible ?? "");
  const [predecessor, setPredecessor] = useState("");
  const [depType, setDepType] = useState("FS");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Predecessors already linked to this task.
  const predecessors = useMemo(() => {
    if (!task) return [];
    return project.dependencies
      .filter((d) => d.successor_id === task.task_id)
      .map((d) => ({
        dep: d,
        name: project.tasks.find((t) => t.task_id === d.predecessor_id)?.name ?? "?",
      }));
  }, [project, task]);

  const otherTasks = project.tasks.filter(
    (t) => t.task_id !== task?.task_id && t.task_type !== "summary"
  );

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const save = () =>
    run(async () => {
      if (isEdit && task) {
        await api.updateTask(project.project_id, task.task_id, {
          name,
          duration: isMilestone ? 0 : duration,
          status,
          progress,
          responsible: responsible || null,
        });
      } else {
        await api.addTask(project.project_id, {
          name,
          duration: isMilestone ? 0 : duration,
          task_type: isMilestone ? "milestone" : "task",
          is_milestone: isMilestone,
          responsible: responsible || null,
        });
      }
      onClose();
    });

  const remove = () =>
    run(async () => {
      if (task) await api.deleteTask(project.project_id, task.task_id);
      onClose();
    });

  const addPredecessor = () =>
    run(async () => {
      if (task && predecessor) {
        await api.addDependency(project.project_id, {
          predecessor_id: predecessor,
          successor_id: task.task_id,
          dependency_type: depType,
        });
        setPredecessor("");
      }
    });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{isEdit ? "Modifier la tâche" : "Nouvelle tâche"}</h2>

        <label className="field">
          <span>Nom</span>
          <input value={name} onChange={(e) => setName(e.target.value)} autoFocus />
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={isMilestone}
            onChange={(e) => setIsMilestone(e.target.checked)}
          />
          <span>Jalon (durée nulle)</span>
        </label>

        {!isMilestone && (
          <label className="field">
            <span>Durée (jours)</span>
            <input
              type="number"
              min={0}
              step={0.5}
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value) || 0)}
            />
          </label>
        )}

        {isEdit && (
          <>
            <label className="field">
              <span>Statut</span>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                {(meta?.task_statuses ?? ["not_started", "in_progress", "completed", "on_hold"]).map(
                  (s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  )
                )}
              </select>
            </label>

            <label className="field">
              <span>Avancement : {Math.round(progress)}%</span>
              <input
                type="range"
                min={0}
                max={100}
                value={progress}
                onChange={(e) => setProgress(parseFloat(e.target.value))}
              />
            </label>
          </>
        )}

        <label className="field">
          <span>Responsable</span>
          <select value={responsible ?? ""} onChange={(e) => setResponsible(e.target.value)}>
            <option value="">— Aucun —</option>
            {project.resources.map((r) => (
              <option key={r.resource_id} value={r.resource_id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        {isEdit && (
          <div className="dep-section">
            <h3>Prédécesseurs</h3>
            {predecessors.length === 0 && <p className="muted small">Aucun prédécesseur.</p>}
            <ul className="dep-list">
              {predecessors.map((p) => (
                <li key={p.dep.dep_id}>
                  <span className="dep-type">{p.dep.dependency_type}</span> {p.name}
                </li>
              ))}
            </ul>
            {otherTasks.length > 0 && (
              <div className="dep-add">
                <select value={predecessor} onChange={(e) => setPredecessor(e.target.value)}>
                  <option value="">Choisir une tâche…</option>
                  {otherTasks.map((t) => (
                    <option key={t.task_id} value={t.task_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
                <select value={depType} onChange={(e) => setDepType(e.target.value)}>
                  {(meta?.dependency_types ?? ["FS", "SS", "FF", "SF"]).map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
                <button className="btn-secondary" onClick={addPredecessor} disabled={!predecessor}>
                  + Lier
                </button>
              </div>
            )}
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div className="modal-actions">
          {isEdit && (
            <button className="btn-danger" onClick={remove} disabled={busy}>
              Supprimer
            </button>
          )}
          <div className="spacer" />
          <button className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button className="btn-primary" onClick={save} disabled={busy || !name.trim()}>
            {busy ? "…" : "Enregistrer"}
          </button>
        </div>
      </div>
    </div>
  );
}
