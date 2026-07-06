import type { Task } from "../types";

interface Props {
  tasks: Task[];
}

export function TaskTable({ tasks }: Props) {
  if (tasks.length === 0) {
    return <div className="empty-hint">Aucune tâche dans ce projet.</div>;
  }
  return (
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
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.task_id} className={t.task_type === "summary" ? "summary-row" : ""}>
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
