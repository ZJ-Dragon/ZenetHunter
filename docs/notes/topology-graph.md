# Topology Graph Notes

Render lifecycle
- The graph waits for a non-zero container size (ResizeObserver) before mounting the canvas. Layout refresh runs when data changes, container resizes, or the page becomes visible, and `zoomToFit` is invoked once nodes exist.
- A manual `Fit` control and double-click centering call the same refresh helpers to avoid the “first render blank” issue seen when the tab was hidden.

Layout
- Router/gateway nodes are anchored at the origin (`fx/fy = 0`). Satellites receive deterministic initial positions on a radial ring to reduce startup overlap; a collide force (26px) adds spacing.
- Links are low-contrast by default; hover/selection highlights only the connected edges.

Semantic zoom
- Zoomed out (<0.6 scale): show icons and dots only (router still shows its label).
- Mid zoom (>=0.6): show primary label (display_name → auto name → IP), truncated with ellipsis.
- Zoomed in (>=1.2): add a vendor badge; richer evidence/keywords stay in the details drawer, not on the canvas.

Priorities
- Display fields honor manual overrides first (`display_name/display_vendor`), then automatic guesses, then IP/vendor fallbacks. Secondary info (IP/MAC/vendor/confidence) is kept in tooltips/drawer to avoid on-canvas clutter.
