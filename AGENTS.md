# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## Project Overview

datalab is a research data management platform for materials chemistry. It consists of:
- **pydatalab**: Flask-based Python REST API server (`pydatalab/`)
- **webapp**: Vue.js 3 frontend application (`webapp/`)
- **MongoDB**: Database backend for storing annotations and connections

## Development Commands

You should normally assume the user has a development set up already, with API and frontend running locally.

You should not typically perform any deployment related operations unless explicitly instructed.

### Python Backend (pydatalab)

```bash
cd pydatalab

# Install dependencies (use uv)
uv sync --all-extras --dev --locked

# Run development server
uv run flask --app 'pydatalab.main' run --reload --port 5001

# Run tests
uv run pytest

# Run single test file
uv run pytest tests/server/test_items.py

# Run single test
uv run pytest tests/server/test_items.py::test_function_name -v

# Regenerate JSON schemas (when models change)
uv run invoke dev.generate-schemas
```

### Frontend (webapp)

```bash
cd webapp

# Install dependencies
yarn install

# Run development server (serves at localhost:8081)
yarn serve

# Build for production
yarn build

# Run linting
yarn lint

# Run unit tests
yarn test:unit

# Run e2e tests (requires backend at localhost:5001)
yarn test:e2e
yarn test:e2e --headless
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (run from repo root)
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

### Docker (production)

```bash
# Start all services
docker compose --profile prod up

# Start only database (for local development)
docker compose up database
```

## Architecture

### Backend Structure (pydatalab/src/pydatalab/)

- `main.py` - Flask app entry point
- `config.py` - Server configuration (loaded from JSON file or env vars prefixed with `PYDATALAB_`)
- `routes/v0_1/` - REST API endpoints organized by resource type:
  - `items.py` - Main CRUD operations for samples, cells, starting materials
  - `auth.py` - OAuth authentication (GitHub, ORCID)
  - `blocks.py` - Data block operations
  - `collections.py` - Collection management
  - `files.py` - File uploads and remote filesystem sync
- `models/` - Pydantic models for database entities (items, people, files, relationships)
- `blocks/` - Base classes for data blocks (`DataBlock` base class in `base.py`)
- `apps/` - Characterisation technique blocks (XRD, NMR, echem, Raman, TGA, etc.)
  - Each app provides a `DataBlock` subclass for visualising/analysing specific data types
  - Apps are loaded dynamically; missing dependencies are gracefully handled
  - Plugins can register via `pydatalab.apps.plugins` entrypoint

### Frontend Structure (webapp/src/)

- `main.js` - Vue app entry point
- `App.vue` - Root component
- `router/` - Vue Router configuration
- `store/` - Vuex state management
- `views/` - Page components
- `components/` - Reusable UI components
- `server_fetch_utils.js` - API client utilities
- `resources.js` - Resource type definitions

### Key Concepts

- **Items**: Core entities (samples, cells, starting_materials, equipment) with hierarchical relationships
- **Blocks**: Modular data visualisation/analysis units attached to items
- **Collections**: Groups of items for organisation
- **Relationships**: Graph connections between items (synthesised_from, is_part_of, etc.)
- **Refcodes**: Unique identifiers for items (format configured in server config)

## Code Style

### Python
- Formatting: ruff (line length 100) via pre-commit
- Type hints: Required, using Pydantic v1 models
- Logging: Use `pydatalab.logger.LOGGER`
- Tests: pytest with fixtures in `conftest.py`

### JavaScript/Vue
- Formatting: Prettier + ESLint via pre-commit
- Vue 3 composition API
- Component testing with @testing-library/vue
- E2E testing with Cypress


## Database and Test Guidelines

- **Avoid database migrations** for new features or functionality unless absolutely necessary. New optional fields (with `None` defaults) are preferred so that existing documents remain valid without migration.
- **Extend tests, don't modify existing assertions.** When adding new functionality, add new assertions or new test functions rather than changing existing expected values. If existing test values must change, do so deliberately and explain the reason.

## Environment Variables

Key environment variables (can also be set in config.json):
- `PYDATALAB_MONGO_URI` - MongoDB connection string
- `PYDATALAB_CONFIG_FILE` - Path to JSON config file (default: /app/config.json)
- `PYDATALAB_TESTING` - Disable auth when set to "true"
