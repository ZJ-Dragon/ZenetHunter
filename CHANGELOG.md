

# Changelog

All notable changes to this project will be documented in this file.

This project **adheres to**:
- **Keep a Changelog 1.1.0** for structure and sections.  
- **Conventional Commits 1.0.0** for commit messages to enable automation.  
- **Semantic Versioning (SemVer)** for version numbers.

> Changelog entries are grouped by: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**, **Security** (plus optional **Build/CI**, **Docs**). Automation (e.g., `conventional-changelog`/`semantic-release`) can generate or augment entries from commit history. See references below.

---

## [Unreleased]

### Added
- _TBD_

### Changed
- _TBD_

### Deprecated
- _TBD_

### Removed
- _TBD_

### Fixed
- _TBD_

### Security
- _TBD_

### Docs
- _TBD_

### Build/CI
- _TBD_

---

## [0.1.0] - 2025-10-01

### Added
- **Backend**: FastAPI entrypoint with `/healthz`, CORS, and router scaffold (`app.main:app`).
- **Backend Tooling**: `pyproject.toml` with PEP 621 metadata; `ruff`/`black`/`pytest` config; minimal `tests/test_healthz.py`.
- **Frontend**: Vite + React + TypeScript scaffold (`index.html`, `vite.config.ts`, `src/main.tsx`, `src/App.tsx`), ESLint v9 Flat Config and Prettier setup, TS configs.
- **CI**: Monorepo-aware GitHub Actions workflow for backend (Python) & frontend (Node), with caching and pre-commit.
- **Repo Hygiene**: `.editorconfig`, `.gitignore`, `.dockerignore`, `.pre-commit-config.yaml`, `commitlint.config.cjs`.
- **Governance & Docs**: `README.md` (EN), backend README (EN/zh-CN), `CONTRIBUTING.md` (EN), `SECURITY.md` / `SECURITY.zh-CN`, `CODEOWNERS`, docs index, and `mkdocs.yml`.

---

## References
- Keep a Changelog 1.1.0 — sections and style: https://keepachangelog.com/en/1.1.0/
- Conventional Commits 1.0.0 — commit message convention enabling automation: https://www.conventionalcommits.org/en/v1.0.0/
- conventional-changelog tooling — generating changelogs from commits: https://github.com/conventional-changelog/conventional-changelog
- semantic-release — automated version, changelog, and publishing from CI: https://semantic-release.gitbook.io/

---

## Link references
> Update the repository owner if needed. These URLs assume GitHub hosting at `ZJ-Dragon/ZenetHunter`.

[Unreleased]: https://github.com/ZJ-Dragon/ZenetHunter/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ZJ-Dragon/ZenetHunter/releases/tag/v0.1.0
