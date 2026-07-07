import type { Task } from "./types";

/** Map of parent_id -> ordered children. */
function childrenMap(tasks: Task[]): Map<string, Task[]> {
  const map = new Map<string, Task[]>();
  for (const t of tasks) {
    if (t.parent_id) {
      const list = map.get(t.parent_id) ?? [];
      list.push(t);
      map.set(t.parent_id, list);
    }
  }
  return map;
}

/** Ids of every descendant of `taskId` (children, grandchildren, …). */
export function descendantIds(tasks: Task[], taskId: string): Set<string> {
  const map = childrenMap(tasks);
  const result = new Set<string>();
  const stack = [...(map.get(taskId) ?? [])];
  while (stack.length) {
    const node = stack.pop()!;
    if (result.has(node.task_id)) continue;
    result.add(node.task_id);
    stack.push(...(map.get(node.task_id) ?? []));
  }
  return result;
}

/** Depth of a task in the parent hierarchy (0 = root). */
export function depthOf(tasks: Task[], task: Task): number {
  const byId = new Map(tasks.map((t) => [t.task_id, t]));
  let depth = 0;
  let current = task;
  const guard = new Set<string>();
  while (current.parent_id && !guard.has(current.task_id)) {
    guard.add(current.task_id);
    const parent = byId.get(current.parent_id);
    if (!parent) break;
    depth += 1;
    current = parent;
  }
  return depth;
}

/** Tasks that may legally become the parent of `task` (excludes self + descendants). */
export function candidateParents(tasks: Task[], task: Task): Task[] {
  const forbidden = descendantIds(tasks, task.task_id);
  forbidden.add(task.task_id);
  return tasks.filter((t) => !forbidden.has(t.task_id) && t.task_type !== "milestone");
}
