# Prompt Writing Rules

When handing work to another agent or writing a branch/task prompt, include enough context to avoid drift.

## Include
- branch name
- exact goal
- non-goals
- files or areas in scope
- contracts that must stay stable
- verification steps
- commit/push expectations
- whether AGENT must be updated

## Prefer
- concrete file paths over vague module names
- explicit refusal boundaries for out-of-scope security requests
- phrases like "preserve existing API and event contracts"
- branch-local constraints instead of generic policy claims

## Avoid
- vague prompts such as "refactor everything"
- instructions that imply a reusable global safety exception
- hidden contract changes
- unstated assumptions about backend payloads or WebSocket events

## Default Prompt Reminder
Tell the next agent to read `AGENT/` first and list the required reading order when the task is non-trivial.
