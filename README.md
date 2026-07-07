# PlanningEz

**PlanningEz** est un outil moderne de planification de projets conçu pour simplifier la création de plannings professionnels tout en restant compatible avec Microsoft Project.

## 🎯 Objectif

Réduire drastiquement le temps de création d'un planning initial. PlanningEz fonctionne comme un assistant de préparation de planning, permettant ensuite d'exporter le résultat vers Microsoft Project pour les utilisateurs qui le souhaitent.

## ✨ Caractéristiques principales

- **Interface moderne et intuitive** - Démarreur rapide et ergonomie pensée pour les chefs de projet
- **Diagramme de Gantt interactif** - Glisser-déposer pour déplacer une tâche (contrainte « début au plus tôt ») ou étirer son bord droit pour changer la durée ; recalcul automatique du planning
- **Édition en ligne** - Double-clic sur une cellule (nom, durée, avancement) du tableau pour l'éditer, création/suppression de tâches et de dépendances depuis l'interface
- **Gestion des dépendances** - Fin→Début, Début→Début, Fin→Fin, Début→Fin avec délais
- **Calendriers flexibles** - Support multi-calendrier (entreprise, projet, équipe, sous-traitant)
- **Gestion des ressources** - Assignation, disponibilité, coût, charge par ressource
- **Templates réutilisables** - Créer et charger des modèles d'industrie (industriel, IT, pharma, etc.)
- **Bibliothèque de Work Packages** - Blocs de planning autonomes, réutilisables, versionnés et partageables en JSON (Basic Engineering, HAZOP, FAT, SAT, Commissioning, etc.)
- **Génération intelligente** - Assembler un planning complet en sélectionnant plusieurs Work Packages : WBS, tâches, jalons et dépendances générés automatiquement
- **Import WBS multi-format** - JSON (prioritaire), CSV, Excel, XML avec détection automatique de la hiérarchie et numérotation
- **Modes de démarrage** - Projet vide, template, Work Package, WBS existant, fichier Microsoft Project, Primavera P6 ou JSON PlanningEz
- **Export Microsoft Project & Primavera P6** - XML compatibles, plus une couche d'abstraction extensible pour d'autres formats
- **Calculs automatiques** - Chemin critique, marges totales et libres, durée projet
- **Bibliothèque de jalons** - Kick-off, PDR, CDR, FAT, SAT, etc.
- **Mode portable** - Exécution directe sans installation, toutes dépendances intégrées

## 🧱 Work Packages, WBS, import et export

```python
from planningez.core.services import (
    ProjectInitializer, StartMode, WorkPackageLibrary,
    PlanningGenerator, GenerationRules, ConnectMode,
)
from planningez.import_ import WBSImporter
from planningez import export

# 1. Importer un WBS structuré (JSON prioritaire)
wbs = WBSImporter().from_json('{"Projet": {"Engineering": {"Process": {}}}}')

# 2. Assembler un planning à partir de Work Packages
library = WorkPackageLibrary(storage_dir="~/planningez_library")
packages = [library.get_by_code("BE-001"), library.get_by_code("FAT-001")]
generator = PlanningGenerator(GenerationRules(connect_mode=ConnectMode.SEQUENTIAL))
project = generator.generate(packages, project_name="Plant X")

# 3. Exporter vers Microsoft Project, Primavera P6 ou JSON natif
export.export_project(project, "msproject", "plant_x.xml")
export.export_project(project, "primavera", "plant_x_p6.xml")
print(export.available_formats())  # ['json', 'msproject', 'primavera']
```

## 💾 Télécharger l'exécutable (sans Python ni Node)

La façon la plus simple d'utiliser PlanningEz : télécharger l'exécutable autonome
correspondant à votre système depuis la page
**[Releases](https://github.com/theodynl/PlanningEz/releases)**.

| Système | Fichier |
|---|---|
| Windows | `PlanningEz-windows.exe` |
| macOS   | `PlanningEz-macos` |
| Linux   | `PlanningEz-linux` |

Il suffit de le lancer : l'application démarre un serveur local et ouvre
automatiquement votre navigateur sur PlanningEz. Aucune installation de Python
ou de Node n'est nécessaire.

> **Note (binaires non signés)** : au premier lancement, Windows SmartScreen
> (« Informations complémentaires → Exécuter quand même ») ou macOS Gatekeeper
> (clic droit → « Ouvrir ») peut afficher un avertissement, car les
> exécutables ne sont pas signés. Sous macOS/Linux, rendez le fichier
> exécutable si besoin : `chmod +x PlanningEz-macos`.

Les exécutables sont produits automatiquement par GitHub Actions
(`.github/workflows/build-executables.yml`) sur chaque tag de version.

## 🚀 Démarrage rapide (développement)

PlanningEz est une **webapp** : un backend **FastAPI** (Python) qui expose le cœur de planification en API REST, et un frontend **React + TypeScript** avec un diagramme de Gantt interactif.

### Prérequis

- Python 3.12 ou supérieur (backend)
- Node.js 18 ou supérieur (frontend)

### Installation

```bash
# Cloner le repository
git clone https://github.com/theodynl/planningez.git
cd planningez

# Backend : environnement virtuel + dépendances
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -e .

# Frontend : dépendances Node
cd frontend && npm install && cd ..
```

### Lancer en développement (deux serveurs)

```bash
# Terminal 1 — API FastAPI (http://127.0.0.1:8000)
python -m planningez

# Terminal 2 — serveur de dev Vite (http://127.0.0.1:5173)
cd frontend && npm run dev
```

Ouvrez ensuite **http://127.0.0.1:5173** ; le serveur Vite relaie automatiquement les appels `/api` vers le backend.

### Lancer en production (un seul serveur)

```bash
# Construire le frontend
cd frontend && npm run build && cd ..

# Lancer le serveur : il sert l'API ET le frontend compilé
python -m planningez
```

Ouvrez **http://127.0.0.1:8000**. La documentation interactive de l'API est disponible sur **http://127.0.0.1:8000/docs**.

## 🏗️ Architecture

```
planningez/                  # Backend Python
├── core/
│   ├── models/              # Modèles (Project, Task, Resource, WBS, WorkPackage…)
│   ├── services/            # Moteur de planification, génération, initialiseur, bibliothèque
│   └── exceptions/          # Exceptions personnalisées
├── api/                     # Application FastAPI (routes REST + store en mémoire)
├── export/                  # Couche d'abstraction + JSON / MS Project / Primavera
├── import_/                 # Import WBS (JSON/CSV/Excel/XML), MS Project, Primavera
└── utils/                   # Sérialisation, logging

frontend/                    # Frontend React + TypeScript (Vite)
├── src/
│   ├── components/          # GanttChart, TaskTable, NewProjectWizard
│   ├── api.ts               # Client de l'API
│   ├── types.ts             # Types partagés
│   └── App.tsx              # Application principale
└── dist/                    # Build de production (servi par FastAPI)

tests/                       # Tests unitaires + API (pytest)
```

### Principaux points d'entrée de l'API

| Méthode | Route | Rôle |
|---|---|---|
| `GET`  | `/api/health` | Sonde de vie |
| `GET`  | `/api/meta` | Énumérations (disciplines, formats d'export, modes…) |
| `POST` | `/api/projects` | Créer un projet (modes : vide / WBS / Work Package / JSON) |
| `POST` | `/api/projects/generate` | Générer un planning depuis des Work Packages |
| `GET`  | `/api/projects/{id}/schedule` | Calculer le chemin critique et les dates |
| `GET`  | `/api/projects/{id}/export/{format}` | Télécharger (json / msproject / primavera) |
| `POST` | `/api/wbs/preview` | Prévisualiser un WBS importé |
| `GET`  | `/api/work-packages` | Bibliothèque de Work Packages |

## 📋 Fonctionnalités planifiées (v0.1+)

### MVP (v0.1)
- [ ] Interface de base (fenêtre principale, menu)
- [ ] Création/édition de projets
- [ ] Gestion des tâches (ajout, modification, suppression)
- [ ] Hiérarchie WBS simple
- [ ] Diagramme de Gantt basique
- [ ] Export MS Project XML

### v0.2
- [ ] Gestion des dépendances complète
- [ ] Calendriers multi-tâches
- [ ] Gestion des ressources
- [ ] Calcul du chemin critique
- [ ] Vue Tableau des tâches

### v0.3+
- [ ] Templates et bibliothèque de jalons
- [ ] Sauvegarde en format .planez
- [ ] Undo/Redo
- [ ] Import Excel/CSV
- [ ] Historique et versionning

## 🎨 Design

**Palette de couleurs :**
- Principal : Vert foncé (#1E4D3A) ou Vert clair (#2E7D5A)
- Secondaire : Orange (#F28C28)
- Accessible et WCAG compliant

**Style :**
- Interface épurée et professionnelle
- Beaucoup d'espaces
- Animations discrètes
- Mode clair (mode sombre prévu)

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=planningez

# Tests spécifiques
pytest tests/unit/
pytest tests/functional/
```

## 📦 Déploiement

PlanningEz se déploie comme une application web classique :

```bash
# 1. Construire le frontend
cd frontend && npm run build && cd ..

# 2. Lancer le serveur (sert l'API et le frontend compilé)
pip install -e .
python -m planningez            # écoute sur PLANNINGEZ_HOST:PLANNINGEZ_PORT (défaut 127.0.0.1:8000)
```

Pour un déploiement de production, servez l'application via un serveur ASGI
(par ex. `uvicorn planningez.api.app:app --host 0.0.0.0 --port 8000`) derrière
un reverse proxy (nginx, Caddy…). Le frontend compilé (`frontend/dist`) est
servi automatiquement par FastAPI lorsqu'il est présent.

## 📚 Documentation

- [Architecture détaillée](docs/architecture.md)
- [Guide de développement](docs/development.md)
- [API interne](docs/api.md)

## 🤝 Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

## 📝 Licence

MIT License - voir [LICENSE](LICENSE) pour les détails

## 📧 Contact

Pour toute question ou suggestion, ouvrez une [issue](https://github.com/theodynl/planningez/issues).

---

**PlanningEz** - *Simplifier la planification, maîtriser la complexité*
