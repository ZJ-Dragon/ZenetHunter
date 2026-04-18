# Display Priority

The repository already has a canonical display-resolution order. New UI work should consume it, not reinvent it.

## Canonical Backend Order
Defined in `backend/app/repositories/device.py`.

### `display_name`
1. `manual_profile.manual_name`
2. `name_manual`
3. `alias`
4. `name`
5. `model`
6. `model_guess`

### `display_vendor`
1. `manual_profile.manual_vendor`
2. `vendor_manual`
3. `vendor` or `vendor_guess` via `vendor_auto`
4. `vendor_guess`

## Frontend Consumption Rule
- Prefer `display_name` and `display_vendor` first
- If a component must compute a fallback, mirror backend order instead of inventing a new priority chain
- Keep manual profile data above legacy manual fields when both are present

## Why This Matters
- Device identity consistency across dashboard, topology, logs, and attack views depends on this order
- Manual label persistence and websocket refresh flows rely on a single shared display contract
