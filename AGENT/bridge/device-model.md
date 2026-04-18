# Device Model

## Canonical Backend Device
The canonical device model is defined by `backend/app/models/device.py` and assembled from persistence models in `backend/app/repositories/device.py`.

## Core Identity Fields
- `mac`
- `ip`
- `type`
- `status`
- `active_defense_status`
- `first_seen`
- `last_seen`

## Operator Metadata
- `alias`
- `tags`
- `manual_profile_id`
- `manual_profile`

## Recognition Fields
- `vendor`
- `model`
- `vendor_guess`
- `model_guess`
- `recognition_confidence`
- `recognition_evidence`

## Manual Override Fields
- `name_manual`
- `vendor_manual`
- `manual_override_at`
- `manual_override_by`

## UI Helper Fields
- `display_name`
- `display_vendor`
- `name_auto`
- `vendor_auto`

## Important Notes
- `display_name` and `display_vendor` are backend-computed presentation helpers and should remain consistent across pages
- `manual_profile` is a stronger source than legacy manual fields when present
- Frontend type definitions still contain some legacy fields (`attack_status`, `defense_status`, `active_defense_policy`) that are not the canonical backend source of truth
- Agents should avoid duplicating display-resolution rules in multiple places
