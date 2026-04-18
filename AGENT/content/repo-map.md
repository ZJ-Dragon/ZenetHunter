# Repository Map

## Top Level
- `AGENT/`
  - Collaboration protocol layer for human and AI agents
- `backend/`
  - FastAPI backend, domain logic, persistence, services, tests
- `frontend/`
  - React/Vite SPA, route pages, contexts, shared UI, locales
- `docs/`
  - Product and technical documentation
- `data/`
  - Repository-level data folder used by local runtime and experiments
- `.github/`
  - CI workflows and issue templates

## Operational Scripts and Metadata
- `start-local.sh`, `start-local.bat`
  - Local development startup helpers
- `README*.md`
  - Root-facing repository entrypoints
- `.pre-commit-config.yaml`, formatter/lint config, editor config
  - Shared hygiene and developer tooling

## Generated or Environment-Specific Areas
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/.venv/`
- cache directories such as `.pytest_cache/` and `.ruff_cache/`

Treat generated/runtime directories as outputs, not as hand-edited sources.
