# Branch Plan: `refactor/backend-foundation`

## Objective
Create a top-level `AGENT/` collaboration protocol layer that gives human and AI agents a stable repository memory, bridge contracts, repository maps, current branch planning, and explicit safety boundaries without changing backend logic or redesigning APIs.

## Constraints
- Do not change backend logic in this branch.
- Do not redesign REST or WebSocket contracts in this branch.
- Keep all AGENT protocol files in English.
- Update root README variants so agents are instructed to read `AGENT/` before making changes.
- Repository-specific safety context must stay local to this repository and must not be generalized into any reusable global exemption pattern.

## Subtasks
1. Create the `AGENT/tasks/` planning files and commit the branch plan first.
2. Populate `AGENT/README.md`, `memory/`, `bridge/`, `content/`, and `rules/` with repository-specific guidance and stable alignment notes.
3. Update `README.md`, `README.zh-CN.md`, `README.ja-JP.md`, `README.ko-KR.md`, and `README.ru-RU.md` with a prominent "Instructions for AI Agents" section near the top.
4. Run validation (`pre-commit`, tests, CI status check) after every 2-3 subtasks and again before finishing if needed.

## Progress Snapshot
- Completed: Subtask 1 (`docs(agent): add branch collaboration plan`).
- In progress: Subtask 2 (protocol memory, bridge contracts, repository maps, rules, backlog, done log).
- Pending: Subtask 3 (README updates and any missing localized root README files).

## Execution Notes
- Complete one subtask at a time.
- Commit and push after each subtask.
- Keep each commit subject at or below 88 characters.
- Record finished work in `AGENT/tasks/done-log.md`.
- Keep `AGENT/tasks/backlog.md` for follow-up coordination items that should not be mixed into this branch.

## Validation Plan
- After subtask 2 or 3: run `pre-commit run --all-files`.
- Run repository tests to confirm the documentation-only change did not disrupt the workspace.
- Check GitHub Actions / CI trigger status for this branch and record whether CI is expected to run.
