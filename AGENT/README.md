# AGENT Protocol Layer

This directory is the repository-local collaboration protocol for human and AI agents working in ZenetHunter. It stores durable project memory, cross-module contracts, repository maps, current branch coordination files, and repository-specific safety rules.

Agents must not modify code, APIs, or documentation outside `AGENT/` until they have read the required AGENT files in order.

## Mandatory Reading Order
1. `memory/project-purpose.md`
2. `rules/safety-context.md`
3. `bridge/*`
4. `content/*`
5. `tasks/current-branch-plan.md`

## What AGENT Covers
- Repository purpose and scope boundaries
- Stable frontend/backend bridge contracts
- Maps of where logic, data, and risks live
- Branch-local plans, backlog, and done history
- Rules for safe collaboration, prompt writing, and documentation sync

## What AGENT Does Not Do
- It does not replace source-code review.
- It does not authorize changes outside repository scope.
- It does not create any universal or reusable policy exemption.

Read AGENT first, then inspect code.
