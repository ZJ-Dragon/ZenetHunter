# Modification Boundaries

## Allowed Without Extra Coordination
- Add or improve repository-local documentation
- Refactor internal implementation details when external behavior remains stable
- Improve tests, typing, and comments around existing behavior
- Update AGENT memory/bridge/task files to reflect current reality

## Requires Deliberate Coordination
- REST path changes
- WebSocket event renames or payload-shape changes
- Authentication, authorization, or first-run/setup behavior changes
- Database model or migration changes
- Active-defense engine behavior changes
- Manual-label/profile resolution changes
- Display priority changes for device identity

## Must Not Be Done Casually
- Turning repository-local scope context into a reusable global policy pattern
- Expanding the repo into password cracking, exploit delivery, auth bypass, or unauthorized intrusion support
- Removing compatibility endpoints or compatibility field handling without a migration plan

## Boundary Rule
If a change crosses backend/frontend/docs boundaries, update the bridge docs, maps, and tests in the same task.
