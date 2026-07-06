# PlanningEz - Development Guide

## Project Overview

**PlanningEz** is a modern planning software for project management, designed to simplify the creation of professional project plans while maintaining compatibility with Microsoft Project.

- **Language:** Python 3.12+
- **GUI Framework:** PySide6 (Qt)
- **Architecture:** MVC/MVVM with clear separation of concerns
- **Status:** v0.1.0 (MVP in development)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
python -m planningez.ui.main
```

## Project Structure

```
planningez/
├── core/
│   ├── models/              # Data models (Project, Task, Resource, etc.)
│   ├── services/            # Business logic (PlanningEngine, CalendarService, etc.)
│   └── exceptions/          # Custom exceptions
├── ui/
│   ├── main.py             # Application entry point
│   ├── main_window.py      # Main window implementation
│   ├── widgets/            # Reusable UI components
│   ├── dialogs/            # Dialog windows
│   └── styles/             # Stylesheets and themes
├── templates/              # Project templates (JSON)
├── export/                 # Export functionality (MS Project XML, etc.)
├── import_/                # Import functionality (CSV, Excel, etc.)
├── resources/              # Static resources (icons, images)
├── utils/                  # Utility modules (logging, etc.)
└── tests/                  # Test suites
```

## Key Concepts

### Models
- **Project**: Container for all project data
- **Task**: Individual work items with duration, dependencies, responsible party
- **Resource**: People or equipment with skills, availability, costs
- **Dependency**: Links between tasks (FS, SS, FF, SF)
- **Calendar**: Working days/hours, holidays, specific to resources or projects

### Services
- **PlanningEngine**: Core calculation engine (critical path, slack, dates)
- **CalendarService**: Calendar operations, working day calculations
- **ResourceService**: Resource allocation and load leveling

### Core Types
- `TaskType`: task, milestone, phase, summary
- `TaskStatus`: not_started, in_progress, completed, on_hold
- `TaskPriority`: low, medium, high, critical
- `DependencyType`: FS (Finish-to-Start), SS, FF, SF
- `CalendarType`: company, project, team, resource, subcontractor

## Development Guidelines

### Code Standards
- Use **type hints** throughout
- Follow **PEP 8** style guide
- Minimum docstrings for public methods
- No comments for self-explanatory code

### Testing
- Unit tests in `tests/unit/`
- Functional tests in `tests/functional/`
- Run `pytest` before committing
- Aim for >80% coverage

### Git Workflow
1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes and test
3. Commit with clear messages
4. Push to branch
5. Create pull request

### Current Development Focus

**Phase 1 (v0.1 - MVP):**
- Core data models ✅ (completed)
- Basic UI framework
- Task management
- Simple Gantt view
- MS Project export (XML)

**Phase 2 (v0.2):**
- Dependency handling
- Multi-calendar support
- Resource management
- Critical path algorithm

**Phase 3 (v0.3+):**
- Templates and milestone library
- Undo/Redo
- Import capabilities
- Advanced views

## Important Files

- `pyproject.toml`: Project configuration and dependencies
- `requirements.txt`: Direct pip dependencies
- `.gitignore`: Git ignore patterns
- `README.md`: User-facing documentation

## Color Palette

- **Primary (Main)**: #2E7D5A (Green)
- **Primary (Dark)**: #1E4D3A (Dark Green)
- **Secondary**: #F28C28 (Orange)
- **Text**: #1F2937 (Dark Gray)
- **Background**: #F9FAFB (Light Gray)

## Design System

- Modern, minimal aesthetic
- Professional industrial software style
- Light mode by default (dark mode architecture prepared)
- WCAG AA compliance target
- Discrete animations, plenty of whitespace

## Dependencies

### Core
- **PySide6**: GUI framework
- **pydantic**: Data validation
- **python-dateutil**: Date utilities
- **pytz**: Timezone handling

### Optional (Export/Import)
- **lxml**: XML parsing
- **openpyxl**: Excel support
- **reportlab**: PDF generation

### Development
- **pytest**: Testing
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **pyinstaller**: Build/packaging

## Common Tasks

### Add a new model
1. Create file in `planningez/core/models/`
2. Define dataclass with proper validation
3. Update `planningez/core/models/__init__.py`

### Add a new service
1. Create file in `planningez/core/services/`
2. Implement service class
3. Update `planningez/core/services/__init__.py`

### Create a new UI component
1. Create file in `planningez/ui/widgets/`
2. Extend `QWidget` or appropriate Qt class
3. Use PySide6 patterns (signals, slots)

### Write tests
1. Create test file matching the module: `test_*.py`
2. Use pytest patterns
3. Mock external dependencies
4. Aim for clear test names describing behavior

## Branch Strategy

Working on branch: `claude/missing-recent-repo-6c08j7`

**Branch naming:**
- `feature/description`: New features
- `fix/description`: Bug fixes
- `refactor/description`: Code improvements
- `docs/description`: Documentation
- `claude/*`: Claude Code development branches

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Microsoft Project XML Schema](https://docs.microsoft.com/en-us/office-project/)

## Known Issues & TODOs

- [ ] Implement PlanningEngine (critical path calculation)
- [ ] Build complete UI framework
- [ ] Add Gantt chart widget
- [ ] Implement MS Project XML export
- [ ] Add unit tests for all models
- [ ] Create sample templates

## Contact & Questions

For development questions, see the main README.md for contact information.
