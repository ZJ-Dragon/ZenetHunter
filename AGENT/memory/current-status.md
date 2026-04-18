# Current Status

## Repository State
- Monorepo with a Python backend and a React/TypeScript frontend
- Backend package version: `0.1.0` (`backend/pyproject.toml`)
- Frontend package version: `0.2.0` (`frontend/package.json`)
- Mainline baseline currently sits at merge commit `fb6c09a`
- This branch, `refactor/backend-foundation`, is introducing the AGENT collaboration protocol layer only

## Runtime Shape
- Backend entrypoint: `backend/app/main.py`
- Frontend entrypoint: `frontend/src/main.tsx`
- REST API base (default): `http://localhost:8000/api`
- WebSocket endpoint (default): `ws://localhost:8000/api/ws`

## Current Collaboration Intent
This branch should not alter backend logic, frontend business behavior, REST contracts, or WebSocket contracts. The goal is to add durable collaboration guidance so later agents can change the codebase with less drift and fewer unsafe assumptions.

## Tested Areas Present In Repo
- Backend tests live under `backend/tests`
- Frontend tests currently use Vitest (`frontend/src/App.test.tsx`)
- Shared hygiene is enforced through `pre-commit`

## Active Coordination Facts
- AGENT is currently the source of repository-local memory and should be kept in sync with code and docs
- Frontend/backend alignment is functional but contains some legacy naming drift that must be treated carefully
- CI expectations should be checked against `.github/workflows/ci.yml` before assuming branch pushes will run automatically
