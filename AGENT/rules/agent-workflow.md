# Agent Workflow

## Required Loop
1. Plan the work in `AGENT/tasks/current-branch-plan.md`
2. Implement one subtask at a time
3. Commit and push after each subtask
4. Keep each commit subject at or below 88 characters
5. After every 2-3 subtasks, run:
   - `pre-commit run --all-files`
   - relevant tests
   - CI status check

## Execution Expectations
- Read AGENT before changing the repository
- Prefer repository facts over assumptions
- Preserve existing contracts unless the task explicitly includes a coordinated contract change
- Keep branch-local coordination in `AGENT/tasks/`
- Update AGENT bridge/content docs when changing cross-module behavior

## Verification Expectations
- Documentation-only changes still require hygiene checks
- If CI does not trigger for the current branch, record that fact explicitly instead of assuming CI passed
- If tests are not run, say so clearly in the final report

## Commit Hygiene
- Use concise, descriptive commit subjects
- Do not amend or rewrite history unless explicitly asked
- Do not revert user work outside the current task
