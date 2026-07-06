import { useState } from "react";
import { api } from "../api";
import type { Project, WorkPackageSummary } from "../types";

interface Props {
  workPackages: WorkPackageSummary[];
  onCreated: (project: Project) => void;
  onClose: () => void;
}

type Mode = "empty" | "wbs" | "work_package";

const SAMPLE_WBS = `{
  "Projet": {
    "Engineering": {
      "Process": {},
      "Mechanical": {},
      "Electrical": {},
      "Automation": {}
    },
    "Procurement": {
      "Long Lead Items": {},
      "Equipment": {}
    },
    "Manufacturing": {},
    "Installation": {},
    "Commissioning": {}
  }
}`;

export function NewProjectWizard({ workPackages, onCreated, onClose }: Props) {
  const [mode, setMode] = useState<Mode>("work_package");
  const [name, setName] = useState("Nouveau projet");
  const [wbsContent, setWbsContent] = useState(SAMPLE_WBS);
  const [selected, setSelected] = useState<string[]>([]);
  const [connectMode, setConnectMode] = useState("sequential");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      let project: Project;
      if (mode === "empty") {
        project = await api.createProject({ mode: "empty", name });
      } else if (mode === "wbs") {
        project = await api.createProject({
          mode: "wbs",
          name,
          wbs_format: "json",
          wbs_content: wbsContent,
        });
      } else {
        project = await api.generateProject({
          name,
          work_package_ids: selected,
          connect_mode: connectMode,
        });
      }
      onCreated(project);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Nouveau projet</h2>

        <label className="field">
          <span>Nom du projet</span>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>

        <div className="mode-tabs">
          <button className={mode === "empty" ? "active" : ""} onClick={() => setMode("empty")}>
            Projet vide
          </button>
          <button className={mode === "wbs" ? "active" : ""} onClick={() => setMode("wbs")}>
            À partir d'un WBS
          </button>
          <button
            className={mode === "work_package" ? "active" : ""}
            onClick={() => setMode("work_package")}
          >
            À partir de Work Packages
          </button>
        </div>

        {mode === "empty" && (
          <p className="mode-desc">Un projet vierge avec un calendrier par défaut.</p>
        )}

        {mode === "wbs" && (
          <div>
            <p className="mode-desc">
              Collez un WBS structuré en JSON. L'arborescence, les niveaux et la numérotation
              sont générés automatiquement.
            </p>
            <textarea
              className="wbs-input"
              value={wbsContent}
              onChange={(e) => setWbsContent(e.target.value)}
              rows={10}
            />
          </div>
        )}

        {mode === "work_package" && (
          <div>
            <p className="mode-desc">
              Sélectionnez des Work Packages : le WBS, les tâches, les jalons et les dépendances
              seront générés et connectés automatiquement.
            </p>
            <div className="wp-picker">
              {workPackages.map((wp) => (
                <label key={wp.work_package_id} className="wp-option">
                  <input
                    type="checkbox"
                    checked={selected.includes(wp.work_package_id)}
                    onChange={() => toggle(wp.work_package_id)}
                  />
                  <span className="wp-code">{wp.code}</span>
                  <span className="wp-name">{wp.name}</span>
                  <span className="wp-disc">{wp.discipline}</span>
                </label>
              ))}
            </div>
            <label className="field">
              <span>Connexion entre Work Packages</span>
              <select value={connectMode} onChange={(e) => setConnectMode(e.target.value)}>
                <option value="sequential">Séquentielle (l'un après l'autre)</option>
                <option value="parallel">Parallèle (indépendants)</option>
              </select>
            </label>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button
            className="btn-primary"
            onClick={submit}
            disabled={busy || (mode === "work_package" && selected.length === 0)}
          >
            {busy ? "Création…" : "Créer le projet"}
          </button>
        </div>
      </div>
    </div>
  );
}
