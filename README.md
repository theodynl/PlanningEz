# PlanningEz

**PlanningEz** est un outil moderne de planification de projets conçu pour simplifier la création de plannings professionnels tout en restant compatible avec Microsoft Project.

## 🎯 Objectif

Réduire drastiquement le temps de création d'un planning initial. PlanningEz fonctionne comme un assistant de préparation de planning, permettant ensuite d'exporter le résultat vers Microsoft Project pour les utilisateurs qui le souhaitent.

## ✨ Caractéristiques principales

- **Interface moderne et intuitive** - Démarreur rapide et ergonomie pensée pour les chefs de projet
- **Diagramme de Gantt interactif** - Zoom, déplacement, drag-and-drop, barres colorées
- **Gestion des dépendances** - Fin→Début, Début→Début, Fin→Fin, Début→Fin avec délais
- **Calendriers flexibles** - Support multi-calendrier (entreprise, projet, équipe, sous-traitant)
- **Gestion des ressources** - Assignation, disponibilité, coût, charge par ressource
- **Templates réutilisables** - Créer et charger des modèles d'industrie (industriel, IT, pharma, etc.)
- **Export Microsoft Project** - Compatible avec MS Project XML pour une intégration transparente
- **Calculs automatiques** - Chemin critique, marges totales et libres, durée projet
- **Bibliothèque de jalons** - Kick-off, PDR, CDR, FAT, SAT, etc.
- **Mode portable** - Exécution directe sans installation, toutes dépendances intégrées

## 🚀 Démarrage rapide

### Prérequis

- Python 3.12 ou supérieur
- PySide6 (fourni avec les dépendances)

### Installation

```bash
# Cloner le repository
git clone https://github.com/theodynl/planningez.git
cd planningez

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer en mode développement
pip install -e .
```

### Lancer l'application

```bash
python -m planningez.ui.main
```

## 🏗️ Architecture

```
planningez/
├── core/
│   ├── models/          # Modèles de données (Project, Task, Resource, etc.)
│   ├── services/        # Moteur de planification, calendriers, ressources
│   └── exceptions/      # Exceptions personnalisées
├── ui/
│   ├── widgets/         # Composants réutilisables
│   ├── dialogs/         # Dialogues
│   └── styles/          # Styles et thèmes
├── templates/           # Templates de projets
├── export/              # Export Microsoft Project, Excel, PDF
├── import_/             # Import CSV, Excel, MS Project
├── resources/           # Ressources (icônes, images)
└── tests/               # Tests unitaires et fonctionnels
```

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

### Build PyInstaller

```bash
# Créer l'exécutable portable
python build_bundle.py

# Résultat dans dist_bundle/PlanningEz/
```

L'application finale sera fournie sous forme de dossier portable contenant :
- `PlanningEz.exe`
- Ressources
- Templates
- Configuration

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
