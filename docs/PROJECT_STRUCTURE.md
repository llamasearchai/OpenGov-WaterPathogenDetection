# Project Structure

This document describes the clean, organized structure of OpenGov-WaterPathogenDetection.

## Directory Layout

```
OpenGov-WaterPathogenDetection/
│
├── .github/                      # GitHub configuration
│   └── workflows/
│       └── ci.yml               # CI/CD pipeline
│
├── src/opengovwaterpathogendetection/  # Main source code
│   ├── __init__.py
│   ├── cli.py                   # CLI application
│   ├── py.typed                 # Type checking marker
│   │
│   ├── agents/                  # Agent modules
│   │   └── __init__.py
│   │
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── database.py         # Database operations
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── item.py             # Item models
│   │   └── pathogen.py         # Pathogen models
│   │
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── agent_service.py    # AI agent service
│   │   ├── analytics.py        # Advanced analytics
│   │   ├── compliance.py       # Regulatory compliance
│   │   ├── notifications.py    # Alert notifications
│   │   ├── ollama_service.py   # Local LLM service
│   │   └── risk_assessment.py  # Risk assessment
│   │
│   ├── storage/                 # Data storage layer
│   │   ├── __init__.py
│   │   ├── item_storage.py     # Item storage
│   │   ├── pathogen_storage.py # Pathogen storage
│   │   └── water_sample_storage.py  # Sample storage
│   │
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── batch_import.py     # CSV batch import
│   │   ├── demo.py             # Demo system
│   │   ├── export.py           # Data export
│   │   └── logging.py          # Logging utilities
│   │
│   └── web/                     # Web API
│       ├── __init__.py
│       └── app.py              # FastAPI application
│
├── tests/                       # Test suite (222 tests)
│   ├── conftest.py             # Test configuration
│   ├── test_*.py               # Test modules
│   └── ...                     # Additional test files
│
├── docs/                        # Documentation
│   ├── QUICKSTART.md           # Quick start guide
│   ├── FEATURES_COMPLETE_v1.2.md  # Feature documentation
│   ├── DEPLOYMENT_READY.md     # Deployment guide
│   └── ...                     # Historical docs
│
├── data/                        # Database files (gitignored)
│   └── *.db                    # SQLite databases
│
├── .gitignore                   # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit hooks
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── FINAL_RELEASE_v1.2.0.md    # Final release notes
├── LICENSE                     # MIT License
├── PUBLICATION_CONFIRMED.md    # Publication status
├── README.md                   # Main documentation
├── RELEASE_NOTES_v1.2.0.md    # Release notes
├── pyproject.toml              # Project configuration
└── requirements.txt            # Python dependencies
```

## File Organization

### Root Level Files
- **README.md** - Main project documentation
- **CHANGELOG.md** - Version history and changes
- **CONTRIBUTING.md** - Contribution guidelines
- **LICENSE** - MIT License
- **pyproject.toml** - Python project configuration
- **requirements.txt** - Python dependencies
- **RELEASE_NOTES_v1.2.0.md** - Current release notes
- **FINAL_RELEASE_v1.2.0.md** - Final release documentation
- **PUBLICATION_CONFIRMED.md** - Publication confirmation

### Source Code (`src/opengovwaterpathogendetection/`)
- **cli.py** - Command-line interface (10 commands)
- **core/** - Core system functionality
- **models/** - Pydantic data models
- **services/** - Business logic and services
- **storage/** - Data persistence layer
- **utils/** - Utility functions and helpers
- **web/** - REST API (FastAPI)

### Tests (`tests/`)
- **222 comprehensive tests** covering all functionality
- **conftest.py** - Shared test fixtures
- **test_*.py** - Individual test modules

### Documentation (`docs/`)
- **QUICKSTART.md** - 5-minute getting started guide
- **FEATURES_COMPLETE_v1.2.md** - Complete feature list
- **DEPLOYMENT_READY.md** - Production deployment guide
- Historical status reports and documentation

### Data (`data/`)
- SQLite database files (created at runtime)
- Automatically created and gitignored

## Clean Structure Benefits

### 1. **Clear Separation of Concerns**
- Source code in `src/`
- Tests in `tests/`
- Documentation in `docs/`
- Data in `data/`

### 2. **Easy Navigation**
- Logical folder hierarchy
- Consistent naming conventions
- Clear module purposes

### 3. **Professional Organization**
- No temporary files
- No test artifacts
- Clean git history
- Proper gitignore

### 4. **Maintainable Codebase**
- Type hints throughout
- Comprehensive tests
- Good documentation
- Standard Python structure

### 5. **Production Ready**
- No development artifacts
- Clean dependencies
- Proper configuration
- Professional layout

## File Naming Conventions

### Python Files
- **snake_case.py** - All Python files
- **test_*.py** - All test files
- **__init__.py** - Package markers

### Documentation
- **UPPERCASE.md** - Major docs (README, LICENSE)
- **PascalCase.md** - Feature docs
- **lowercase.md** - Supporting docs

### Configuration
- **.lowercase** - Dot files (.gitignore, .env)
- **lowercase.yaml** - YAML configs
- **lowercase.toml** - TOML configs

## Gitignore Rules

The following are excluded from version control:
- `__pycache__/` - Python cache
- `*.pyc`, `*.pyo` - Compiled Python
- `.venv/`, `venv/` - Virtual environments
- `*.db`, `*.db-journal` - Databases
- `.pytest_cache/` - Test cache
- `.coverage`, `htmlcov/` - Coverage reports
- `data/` - Runtime data
- `.env`, `.env.local` - Environment files

## Best Practices

### 1. **Keep It Clean**
- No temporary files in repo
- No personal configs
- No sensitive data
- No build artifacts

### 2. **Organize Logically**
- Related files together
- Clear folder purposes
- Consistent structure

### 3. **Document Everything**
- README for project
- Docstrings for code
- Comments for complexity
- Guides for users

### 4. **Test Thoroughly**
- Test all features
- High coverage
- Integration tests
- Performance tests

### 5. **Version Properly**
- Semantic versioning
- Clear changelogs
- Tagged releases
- Migration guides

---

This clean structure ensures the project remains maintainable, professional, and easy to navigate for all contributors and users.

