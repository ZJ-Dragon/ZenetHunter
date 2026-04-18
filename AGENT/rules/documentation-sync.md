# Documentation Sync

## Sync Rule
When a change affects repository behavior, update the closest matching documentation in the same task.

## Always Update AGENT When Changing
- project scope or repository-local safety boundaries
- REST or WebSocket contracts
- device display priority
- frontend/backend alignment assumptions
- repository layout or ownership of major modules

## Also Check
- `README.md` and localized root README variants for onboarding-impacting changes
- `docs/api/README*.md` for public contract changes
- feature docs under `docs/active-defense/`, `docs/active-probe/`, `docs/external-services/`, and `docs/guides/` when behavior changes there

## Branch Coordination Files
- `tasks/current-branch-plan.md` should reflect the intended execution plan
- `tasks/done-log.md` should record completed subtask milestones
- `tasks/backlog.md` should hold follow-up items that do not fit the current branch

## Documentation Standard
- Keep AGENT files factual, concise, and repository-specific
- Prefer describing what is true in the codebase today over aspirational architecture
