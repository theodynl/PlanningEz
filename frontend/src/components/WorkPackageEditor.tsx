import { useEffect, useState } from "react";
import { api } from "../api";
import type { Meta } from "../types";

interface Props {
  workPackageId: string | null; // null = create
  meta: Meta | null;
  onSaved: () => void;
  onClose: () => void;
}

interface Row {
  name: string;
  duration: number;
  is_milestone: boolean;
}

export function WorkPackageEditor({ workPackageId, meta, onSaved, onClose }: Props) {
  const isEdit = workPackageId !== null;
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [discipline, setDiscipline] = useState("engineering");
  const [description, setDescription] = useState("");
  const [rows, setRows] = useState<Row[]>([{ name: "", duration: 1, is_milestone: false }]);
  const [chain, setChain] = useState(true);
  const [deliverables, setDeliverables] = useState("");
  const [assumptions, setAssumptions] = useState("");
  const [suppliers, setSuppliers] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the package when editing.
  useEffect(() => {
    if (!workPackageId) return;
    api
      .getWorkPackage(workPackageId)
      .then((wp) => {
        setName((wp.name as string) ?? "");
        setCode((wp.code as string) ?? "");
        setDiscipline((wp.discipline as string) ?? "engineering");
        setDescription((wp.description as string) ?? "");
        const tasks = (wp.tasks as { name: string; duration: number }[]) ?? [];
        const ms = (wp.milestones as { name: string }[]) ?? [];
        const loaded: Row[] = [
          ...tasks.map((t) => ({ name: t.name, duration: t.duration, is_milestone: false })),
          ...ms.map((m) => ({ name: m.name, duration: 0, is_milestone: true })),
        ];
        setRows(loaded.length ? loaded : [{ name: "", duration: 1, is_milestone: false }]);
        setChain(((wp.dependencies as unknown[]) ?? []).length > 0);
        setDeliverables(
          ((wp.deliverables as { name: string }[]) ?? []).map((d) => d.name).join("\n")
        );
        setAssumptions(((wp.assumptions as string[]) ?? []).join("\n"));
        setSuppliers(((wp.suppliers as string[]) ?? []).join("\n"));
      })
      .catch((e) => setError((e as Error).message));
  }, [workPackageId]);

  const updateRow = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  const addRow = () =>
    setRows((rs) => [...rs, { name: "", duration: 1, is_milestone: false }]);
  const removeRow = (i: number) => setRows((rs) => rs.filter((_, idx) => idx !== i));

  const lines = (text: string) =>
    text.split("\n").map((l) => l.trim()).filter(Boolean);

  const save = async () => {
    setBusy(true);
    setError(null);
    const document: Record<string, unknown> = {
      name,
      code,
      discipline,
      description,
      tasks: rows
        .filter((r) => !r.is_milestone && r.name.trim())
        .map((r) => ({ name: r.name.trim(), duration: r.duration, task_type: "task" })),
      milestones: rows
        .filter((r) => r.is_milestone && r.name.trim())
        .map((r) => ({ name: r.name.trim() })),
      deliverables: lines(deliverables).map((n) => ({ name: n })),
      assumptions: lines(assumptions),
      suppliers: lines(suppliers),
    };
    try {
      if (isEdit && workPackageId) {
        await api.updateWorkPackage(workPackageId, document, chain);
      } else {
        await api.createWorkPackage(document, chain);
      }
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal wp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{isEdit ? "Modifier le Work Package" : "Nouveau Work Package"}</h2>

        <div className="wp-grid">
          <label className="field">
            <span>Nom</span>
            <input value={name} onChange={(e) => setName(e.target.value)} autoFocus />
          </label>
          <label className="field">
            <span>Code</span>
            <input value={code} onChange={(e) => setCode(e.target.value)} />
          </label>
          <label className="field">
            <span>Discipline</span>
            <select value={discipline} onChange={(e) => setDiscipline(e.target.value)}>
              {(meta?.disciplines ?? ["engineering", "other"]).map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field">
          <span>Description</span>
          <input value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>

        <div className="wp-section">
          <div className="wp-section-head">
            <h3>Tâches &amp; jalons</h3>
            <button className="btn-secondary btn-sm" onClick={addRow}>
              + Ligne
            </button>
          </div>
          <div className="wp-rows">
            {rows.map((r, i) => (
              <div className="wp-row" key={i}>
                <input
                  className="wp-row-name"
                  placeholder="Nom"
                  value={r.name}
                  onChange={(e) => updateRow(i, { name: e.target.value })}
                />
                <label className="wp-row-ms" title="Jalon">
                  <input
                    type="checkbox"
                    checked={r.is_milestone}
                    onChange={(e) => updateRow(i, { is_milestone: e.target.checked })}
                  />
                  jalon
                </label>
                {!r.is_milestone && (
                  <input
                    className="wp-row-dur"
                    type="number"
                    min={0}
                    step={0.5}
                    value={r.duration}
                    onChange={(e) => updateRow(i, { duration: parseFloat(e.target.value) || 0 })}
                  />
                )}
                <button className="row-del" title="Retirer" onClick={() => removeRow(i)}>
                  ×
                </button>
              </div>
            ))}
          </div>
          <label className="checkbox-field">
            <input type="checkbox" checked={chain} onChange={(e) => setChain(e.target.checked)} />
            <span>Chaîner les tâches séquentiellement (dépendances Fin→Début)</span>
          </label>
        </div>

        <div className="wp-grid">
          <label className="field">
            <span>Livrables (un par ligne)</span>
            <textarea rows={3} value={deliverables} onChange={(e) => setDeliverables(e.target.value)} />
          </label>
          <label className="field">
            <span>Hypothèses (une par ligne)</span>
            <textarea rows={3} value={assumptions} onChange={(e) => setAssumptions(e.target.value)} />
          </label>
          <label className="field">
            <span>Fournisseurs (un par ligne)</span>
            <textarea rows={3} value={suppliers} onChange={(e) => setSuppliers(e.target.value)} />
          </label>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="modal-actions">
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
