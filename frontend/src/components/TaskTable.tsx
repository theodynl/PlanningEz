import { useState } from "react";
import type { Task } from "../types";
import type { TaskPatch } from "../api";

interface Props {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onAdd: () => void;
  onDelete: (task: Task) => void;
  onInline: (task: Task, patch: TaskPatch) => void;
}

type EditField = "name" | "duration" | "progress";

export function TaskTable({ tasks, onEdit, onAdd, onDelete, onInline }: Props) {
  const [editing, setEditing] = useState<{ id: string; field: EditField } | null>(null);
  const [value, setValue] = useState("");

  const startEdit = (task: Task, field: EditField, initial: string) => {
    setEditing({ id: task.task_id, field });
    setValue(initial);
  };

  const commit = (task: Task) => {
    if (!editing) return;
    const patch: TaskPatch = {};
    if (editing.field === "name") {
      if (value.trim()) patch.name = value.trim();
    } else if (editing.field === "duration") {
      const d = parseFloat(value);
      if (!Number.isNaN(d) && d >= 0) patch.duration = d;
    } else if (editing.field === "progress") {
      const p = parseFloat(value);
      if (!Number.isNaN(p)) patch.progress = Math.min(100, Math.max(0, p));
    }
    setEditing(null);
    if (Object.keys(patch).length > 0) onInline(task, patch);
  };

  const cellInput = (task: Task, width: number) => (
    <input
      className="inline-input"
      style={{ width }}
      value={value}
      autoFocus
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => setValue(e.target.value)}
      onBlur={() => commit(task)}
      onKeyDown={(e) => {
        if (e.key === "Enter") commit(task);
        if (e.key === "Escape") setEditing(null);
      }}
    />
  );

  const isEditing = (task: Task, field: EditField) =>
    editing?.id === task.task_id && editing.field === field;

  return (
    <div>
      <div className="table-toolbar">
        <button className="btn-primary" onClick={onAdd}>
          + Ajouter une tâche
        </button>
        <span className="muted small">
          Double-cliquez une cellule (nom, durée, %) pour l'éditer · ✎ pour tout modifier
        </span>
      </div>
      {tasks.length === 0 ? (
        <div className="empty-hint">Aucune tâche. Cliquez « Ajouter une tâche ».</div>
      ) : (
        <div className="table-scroll">
          <table className="task-table">
            <thead>
              <tr>
                <th>Tâche</th>
                <th>Type</th>
                <th>Durée</th>
                <th>Début</th>
                <th>Fin</th>
                <th>Avancement</th>
                <th>Marge</th>
                <th>Critique</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr
                  key={t.task_id}
                  className={t.task_type === "summary" ? "summary-row" : ""}
                >
                  <td
                    style={{ paddingLeft: t.parent_id ? 24 : 8 }}
                    onDoubleClick={() => startEdit(t, "name", t.name)}
                  >
                    {isEditing(t, "name") ? cellInput(t, 200) : t.name}
                  </td>
                  <td>{t.task_type}</td>
                  <td
                    onDoubleClick={() => {
                      if (!t.is_milestone) startEdit(t, "duration", String(t.duration));
                    }}
                  >
                    {isEditing(t, "duration")
                      ? cellInput(t, 60)
                      : t.is_milestone
                      ? "—"
                      : `${t.duration} ${t.unit}`}
                  </td>
                  <td>{t.start_date ?? "—"}</td>
                  <td>{t.end_date ?? "—"}</td>
                  <td onDoubleClick={() => startEdit(t, "progress", String(Math.round(t.progress)))}>
                    {isEditing(t, "progress") ? (
                      cellInput(t, 50)
                    ) : (
                      <div className="progress-cell">
                        <div className="progress-fill" style={{ width: `${t.progress}%` }} />
                        <span>{Math.round(t.progress)}%</span>
                      </div>
                    )}
                  </td>
                  <td>{t.total_slack}</td>
                  <td>{t.on_critical_path ? <span className="crit-dot" /> : ""}</td>
                  <td className="row-actions">
                    <button className="row-edit" title="Modifier" onClick={() => onEdit(t)}>
                      ✎
                    </button>
                    <button className="row-del" title="Supprimer" onClick={() => onDelete(t)}>
                      ×
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
