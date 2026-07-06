import type { Task } from "../types";

interface Props {
  tasks: Task[];
}

const ROW_H = 32;
const DAY_W = 22;
const LABEL_W = 240;
const HEADER_H = 40;

function parseDate(value: string | null): Date | null {
  return value ? new Date(value + "T00:00:00") : null;
}

function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / 86400000);
}

export function GanttChart({ tasks }: Props) {
  const scheduled = tasks.filter((t) => t.start_date);
  if (scheduled.length === 0) {
    return (
      <div className="gantt-empty">
        Aucune date planifiée. Cliquez sur « Recalculer le planning ».
      </div>
    );
  }

  const starts = scheduled.map((t) => parseDate(t.start_date)!.getTime());
  const ends = scheduled.map(
    (t) => parseDate(t.end_date ?? t.start_date)!.getTime()
  );
  const minDate = new Date(Math.min(...starts));
  const maxDate = new Date(Math.max(...ends));
  const totalDays = Math.max(daysBetween(minDate, maxDate) + 2, 7);

  const chartW = LABEL_W + totalDays * DAY_W;
  const chartH = HEADER_H + tasks.length * ROW_H;
  const today = new Date();
  const todayX = LABEL_W + daysBetween(minDate, today) * DAY_W;

  // Week gridlines (label every Monday).
  const weekLines: { x: number; label: string }[] = [];
  for (let d = 0; d <= totalDays; d++) {
    const day = new Date(minDate.getTime() + d * 86400000);
    if (day.getDay() === 1) {
      weekLines.push({
        x: LABEL_W + d * DAY_W,
        label: `${day.getDate()}/${day.getMonth() + 1}`,
      });
    }
  }

  return (
    <div className="gantt-scroll">
      <svg width={chartW} height={chartH} className="gantt-svg">
        {/* Week gridlines */}
        {weekLines.map((w, i) => (
          <g key={i}>
            <line x1={w.x} y1={HEADER_H} x2={w.x} y2={chartH} className="gantt-grid" />
            <text x={w.x + 3} y={26} className="gantt-week">
              {w.label}
            </text>
          </g>
        ))}

        {/* Today marker */}
        {todayX >= LABEL_W && todayX <= chartW && (
          <line x1={todayX} y1={HEADER_H} x2={todayX} y2={chartH} className="gantt-today" />
        )}

        {/* Header separator */}
        <line x1={0} y1={HEADER_H} x2={chartW} y2={HEADER_H} className="gantt-grid" />

        {tasks.map((task, i) => {
          const y = HEADER_H + i * ROW_H;
          const start = parseDate(task.start_date);
          const end = parseDate(task.end_date ?? task.start_date);
          const indent = task.parent_id ? 16 : 0;
          const isSummary = task.task_type === "summary";

          return (
            <g key={task.task_id}>
              <rect
                x={0}
                y={y}
                width={chartW}
                height={ROW_H}
                className={i % 2 ? "gantt-row-odd" : "gantt-row-even"}
              />
              <text x={10 + indent} y={y + 21} className={isSummary ? "gantt-label summary" : "gantt-label"}>
                {task.name.length > 30 ? task.name.slice(0, 29) + "…" : task.name}
              </text>

              {start &&
                (() => {
                  const x = LABEL_W + daysBetween(minDate, start) * DAY_W;
                  const barY = y + 8;
                  const barH = ROW_H - 16;

                  if (task.is_milestone || task.task_type === "milestone") {
                    const cx = x;
                    const cy = y + ROW_H / 2;
                    return (
                      <polygon
                        points={`${cx},${cy - 8} ${cx + 8},${cy} ${cx},${cy + 8} ${cx - 8},${cy}`}
                        className="gantt-milestone"
                      />
                    );
                  }

                  const span = end ? Math.max(daysBetween(start, end) + 1, 1) : 1;
                  const width = span * DAY_W - 4;

                  if (isSummary) {
                    return (
                      <rect x={x} y={y + ROW_H / 2 - 3} width={Math.max(width, 4)} height={6} className="gantt-summary-bar" />
                    );
                  }

                  return (
                    <g>
                      <rect
                        x={x}
                        y={barY}
                        width={Math.max(width, 4)}
                        height={barH}
                        rx={3}
                        className={task.on_critical_path ? "gantt-bar critical" : "gantt-bar"}
                      />
                      {task.progress > 0 && (
                        <rect
                          x={x}
                          y={barY}
                          width={Math.max((width * task.progress) / 100, 2)}
                          height={barH}
                          rx={3}
                          className="gantt-progress"
                        />
                      )}
                    </g>
                  );
                })()}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
