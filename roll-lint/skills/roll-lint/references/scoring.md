# After the Lint Roll: Score, Blueprint, Baseline

Read this only after all seven phases are complete. Three deliverables, in order: the score, the Blueprint, and `roll-lint.baseline.json`.

## The Score

Rate the codebase from **−2 to +3**, whole integers only. Not a grade — a position on a journey. Give one score for before the audit (from the Phase 1 inventory) and one for after (from what Phases 2–7 fixed).

```
-2  Survival       Values are arbitrary, nothing is consistent, specificity wars
                   everywhere, no custom properties, no intentional system at all.
                   The CSS works, but only by accident.

-1  Patched        Some patterns exist but drift constantly. A few variables defined
                   but not used consistently. Breakpoints are present but ad-hoc.
                   Someone tried to create order but it didn't hold.

 0  Ground Floor   Everything is consistent within its own logic. Spacing lands on a
                   grid. Radii follow the nested math. Type sizes fit a scale.
                   Line-heights are unitless. Selectors are flat. The CSS is clean —
                   but it's all hard-coded values. No token layer yet.
                   This is where roll-lint gets you.

+1  Seeded         The repeated values from the cleanup have been extracted into CSS
                   custom properties. A global token layer exists: spacing, radii,
                   type scale, colors. Components reference tokens instead of raw
                   values. The system is explicit and self-documenting.

+2  Systematic     Tokens follow a tiered architecture: global primitives → semantic
                   aliases → component-specific references. Theming is possible by
                   remapping the alias layer. New components can be built from
                   existing tokens alone.

+3  Thriving       The design system is governed: versioned, documented, enforced via
                   linting. Token changes propagate across platforms. Ad-hoc values
                   can't leak in without review. The system scales with the team.
```

**Scoring rules:**

- **Score charter (permanent).** The score is computed from the original core dimensions only: spacing, radius, type scale, line-height, z-index, color format, specificity/!important/nesting, breakpoints, and custom-property usage. Newer checks — shadows, dividers, durations/easing, affordances, tabular numerals, contrast, text-wrap, logical/physical mix — are advisory and never move the score. This keeps scores comparable across runs, which matters now that the baseline file gives them history.
- A codebase that already has custom properties for spacing, radii, and color before the audit enters at +1.
- Whole integers only; between floors, round down (a floor requires all its criteria fully met).
- The delta is what matters most. Even −1 → 0 is real ground covered.

## The Blueprint

The seed for the next floor — not a token system, the starting point for one, derived from the cleanup.

**Blueprint charter (permanent).** The Blueprint contains only tokenizable value scales — things that could become a custom property: spacing scale (with usage counts), radius scale (nested math verified), type scale, color palette grouped by role, z-index map, elevation ladder + light angle, divider spec, duration rungs + easing set. Diagnostics — affordance counts, contrast results, coverage percentages — go in reports, never the Blueprint.

Present each scale as a simple list with counts, e.g.:

```
8px   (used 12×)
16px  (used 34×)
24px  (used 41×)
```

Frame it as a reference card, not a mandate: "These are your values. If you wanted tokens, this is the set." The developer can build a token system from it or leave the codebase as-is — clean and consistent is a fine place to stop.

## roll-lint.baseline.json

After presenting the Blueprint, write it machine-readably to the project root. **Full audits write this file; touch-up runs never do.** Schema — all sections optional, include only what was actually derived:

```json
{
  "version": 1,
  "generated": "ISO date",
  "commit": "git HEAD if available",
  "spacing_grid": { "base": 8, "values": [8, 16, 20, 24, 32] },
  "spacing_grid_micro": { "base": 4, "values": [4, 8, 12] },
  "radius_set": [4, 8, 16, 24],
  "type_scale": [12, 14, 16, 20, 24, 32],
  "line_height_policy": "unitless",
  "z_tiers": [-1, 0, 1, 10, 100],
  "color_palette": { "by_role": {} },
  "elevation_ladder": [ { "tier": 1, "blur": 4, "spread": 0 } ],
  "shadow_light_angle": "down-right",
  "divider_spec": { "width": 1, "style": "solid", "color": "#e5e5e5" },
  "duration_rungs": [150, 250],
  "easing_set": ["ease-in-out"],
  "score": { "before": -1, "after": 0 }
}
```

`spacing_grid_micro` is present only when the user chose to keep two spacing tiers. Get `commit` from `git rev-parse HEAD` if the project is a git repo; omit otherwise. This same schema (minus `score`) is what Phase 4 feeds to `scripts/snap.py`.

## What This Skill Doesn't Do

Roll-lint gets you to ground floor. It does not build the token architecture, set up theming, create a component library or docs, enforce tokens via CI, or handle cross-platform token distribution. Those are the next floors; the Blueprint is a correct foundation for them.
