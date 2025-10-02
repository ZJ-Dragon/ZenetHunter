<!--
PRs use Conventional Commits for titles: `type(scope): short summary`
Spec: https://www.conventionalcommits.org/en/v1.0.0/
Link issues with keywords (e.g. closes #123): https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
Required status checks must be green before merge: https://docs.github.com/articles/about-status-checks
-->

## Summary
Explain the **what** and **why** in 2–5 sentences. Keep it small & focused.

## Linked issues
Use closing keywords so merge will close them automatically, e.g. `closes #123`, `fixes #456`, `resolves #789`.

## Type of change
- [ ] feat (new feature)
- [ ] fix (bug fix)
- [ ] docs (documentation)
- [ ] refactor (no functional change)
- [ ] perf (performance)
- [ ] test (add/update tests)
- [ ] build (build system, deps)
- [ ] ci (CI config)
- [ ] chore (maintenance)
- [ ] revert

## How was this tested?
Describe test coverage. Include commands, cases, and environments.
- [ ] unit tests
- [ ] integration
- [ ] e2e / manual
- [ ] screenshots / recordings attached

## Risks / rollout plan
Any breaking changes? migration steps? rollback strategy?

## Checklist
- [ ] PR title follows **Conventional Commits** (`type(scope): summary`).
- [ ] Updated docs / changelog if needed.
- [ ] I ran local checks and tests.
- [ ] I have considered security/privacy implications.

## Required status checks (must be green)
- [ ] **Lint Commit Messages / commitlint**
- [ ] **CI / ci (aggregate)**
- [ ] **Image Build Check / image-check**

## Notes for reviewers
Anything that would help reviewers (context, alternatives, follow-ups).
