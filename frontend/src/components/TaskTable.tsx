import type { Task } from "../types";

interface Props {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onAdd: () => void;
  onDelete: (task: Task) => void;
}

export function TaskTable({ tasks, onEdit, onAdd, onDelete }: Props) {
  return (
    <div>
      <div className="table-toolbar">
        <button className="btn-primary" onClick={onAdd}>
          + Ajouter une tâche
        </button>
        <span className="muted small">Cliquez une ligne pour la modifier</span>
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
                  className={`clickable ${t.task_type === "summary" ? "summary-row" : ""}`}
                  onClick={() => onEdit(t)}
                >
                  <td style={{ paddingLeft: t.parent_id ? 24 : 8 }}>{t.name}</td>
                  <td>{t.task_type}</td>
                  <td>{t.is_milestone ? "—" : `${t.duration} ${t.unit}`}</td>
                  <td>{t.start_date ?? "—"}</td>
                  <td>{t.end_date ?? "—"}</td>
                  <td>
                    <div className="progress-cell">
                      <div className="progress-fill" style={{ width: `${t.progress}%` }} />
                      <span>{Math.round(t.progress)}%</span>
                    </div>
                  </td>
                  <td>{t.total_slack}</td>
                  <td>{t.on_critical_path ? <span className="crit-dot" /> : ""}</td>
                  <td>
                    <button
                      className="row-del"
                      title="Supprimer"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(t);
                      }}
                    >
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
