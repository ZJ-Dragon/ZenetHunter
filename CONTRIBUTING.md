# Contributing to **ZenetHunter**

Thanks for taking the time to contribute! This guide covers **collaboration workflow, branch naming, commit message conventions**, and the basic local checks you should run before opening a pull request (PR). It’s written for an international team and aims to keep contributions small, consistent, and easy to review.

> TL;DR — **Trunk‑Based Development + short‑lived feature branches**, PRs into a protected `main`, commit messages follow **Conventional Commits**, and all PRs must pass CI and pre‑commit checks.  
> References: Trunk‑Based Development and GitHub Flow.

---

## 0) Code of Conduct & Security
Please collaborate professionally and respectfully. If you need to report a security issue, use the private channel described in `/SECURITY.md`.

---

## 1) Branching Strategy (Trunk‑Based + GitHub Flow)
- **Protected branch**: `main` (merge via PR only).  
- **Work style**: create **short‑lived feature branches** from `main`, keep the diff small, and merge back quickly. This reduces integration risk and supports continuous integration.
- **Branch naming**: `<area>/<feature>-<short>` — all lowercase, hyphen‑separated. Examples:
  - `foundation/repo-scaffold`
  - `backend-core/scanner-api`
  - `defender/synproxy`
  - `frontend/topology`
  - `ai-scheduler/policy-core`
  - `ops/dockerfile-prod`
- **Pull Requests**:
  - Keep them focused and well‑described (what/why). Link issues when relevant (`Closes #123`).
  - Must pass CI (lint/tests/build) and pre‑commit hooks.
  - At least one reviewer must approve before merge (avoid self‑merge).  
  - Follow the GitHub Flow cycle: branch → commits → PR → review → merge → delete branch.

---

## 2) Commit Message Convention (Conventional Commits)
We enforce **Conventional Commits 1.0.0** using commitlint. The format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type** (common): `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- **scope** (optional): subsystem or area, e.g. `scanner`, `defender`, `frontend`, `ops`.
- **subject**: one line, in the imperative, no trailing period.
- **BREAKING CHANGE**: put a clear explanation in the body or footer.

Examples:
```
feat(scanner): add subnet discovery endpoint
fix(defender): handle tc shaping fallback on startup
docs(readme): add English quick start and repo layout
chore(gitignore): exclude venv and node_modules
```
References: Conventional Commits spec; commitlint configuration with `@commitlint/config-conventional`.

---

## 3) Pre‑commit Hooks (local hygiene)
Run the hooks locally before pushing. Quick start:

```bash
pip install pre-commit && pre-commit install
pre-commit run --all-files
```

This repository includes:
- Generic hygiene: `trailing-whitespace`, `end-of-file-fixer`.
- Python: `ruff` (lint+format) and `black` (format).
- (Optional) You may add project‑specific hooks over time (e.g., ESLint for the frontend) via `.pre-commit-config.yaml`.

Reference: pre‑commit quick start docs.

---

## 4) Dev & Test Baseline
- **Backend (FastAPI)**
  - Dev: `uvicorn app.main:app --reload`
  - Tests: `pytest -q`
- **Frontend (Vite + React + TS)**
  - Dev: `npm run dev`
  - Build: `npm run build`

See each subdirectory’s `README.md` for detailed instructions. Production/container deploys live under `deploy/`.

---

## 5) Versioning & Changelog
- Versioning follows **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`).
- Changes are tracked in `CHANGELOG.md`. The Conventional Commits structure enables tooling to generate or assist with release notes.

---

## 6) PR Checklist
- [ ] Commit messages follow **Conventional Commits**.
- [ ] Code passes local **pre‑commit** hooks and CI.
- [ ] API/behavior changes documented (docs updated).
- [ ] Config/security‑relevant changes reflected in `/SECURITY.md` and deploy docs.
- [ ] PR description is clear; attach screenshots/log snippets when helpful.

---

Happy contributing! If something is unclear, open an issue and we’ll refine this guide together.
