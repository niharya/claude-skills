# roll-lint

**A systems-design-aware CSS/SCSS auditor — for designers who write code.**

A Claude skill that audits and cleans up stylesheets through seven dependency-ordered phases. It reads your codebase as a systems designer would: finding the patterns you already chose, making them airtight, and flagging the places where they drift.

---

## What's New in v2

- **Touch-up mode** — after a full audit writes `roll-lint.baseline.json` to your project, say "touch-up" (or "quick pass") anytime and roll-lint checks only the files you've changed against your stored baseline. Seconds, not a full re-audit.
- **Hook recipe** — a documented `settings.json` snippet that fires touch-up automatically whenever Claude edits a stylesheet. Your baseline becomes a standing guard. See [`skills/roll-lint/references/hook-recipe.md`](./skills/roll-lint/references/hook-recipe.md).
- **Scripts do the counting** — a real census now runs in Python (`scripts/inventory.py`), so frequencies, ΔE color clustering in OKLch, shadow angles, and WCAG contrast pairs are computed, not eyeballed. Claude interprets; the script counts.
- **Designer-eye checks** — light-source coherence ("lit by two suns"), an elevation ladder derived from your own shadows, "seventeen grays" color clustering with numeric merge thresholds, divider-language consolidation, duration rungs derived from your own timings, affordance coverage counts, tabular numerals, and cascade-free contrast pairs.
- **A Design Charter** — four permanent governance rules written into the skill: checks must detect the codebase disagreeing with itself (no imported taste), reports surface exceptions only, appearance-changing fixes are never auto-applied, and the score stays comparable across runs forever.

---

## The Problem It Solves

CSS accumulates drift. A 19px margin where you meant 20px. A border-radius that breaks the nested math. A z-index pulled from nowhere. An `!important` that nobody can explain. Individually, none of these are catastrophic — but together, they erode the consistency that makes a UI feel intentional.

Most CSS linters catch syntax errors and style guide violations. They don't understand *design systems*. They don't know that `19px` is wrong because your spacing grid is `4px`-based. They don't catch that a nested element's border-radius should be `outer - padding`. They don't notice that your section gaps are smaller than your element gaps, which creates visual imbalance.

`roll-lint` audits CSS the way a systems designer would: by understanding the rules you chose and finding where they break.

---

## The Ironing Metaphor

Think of it as ironing a shirt. The shirt already exists — `roll-lint` doesn't redesign it. It presses out the wrinkles so the existing design comes through cleanly.

After the ironing, you get a **blueprint**: the spacing scale, radius set, type scale, and color palette that survived the cleanup — ready to become CSS custom properties or a formal token system if you want to go further.

---

## Prerequisites

- [Claude](https://claude.ai) (claude.ai or Claude Code)
- CSS, SCSS, or LESS files to audit — no browser required

---

## Installation

### Quick install (Claude Code, via marketplace)

```
/plugin marketplace add niharya/claude-skills
/plugin install roll-lint@skill-shelf
```

Then start a new conversation and share your CSS/SCSS files.

### Manual install (fallback)

1. Copy [`skills/roll-lint/SKILL.md`](./skills/roll-lint/SKILL.md) into your Claude skills directory
   - On claude.ai: Settings → Skills → add new skill
   - On Claude Code (without the marketplace): place in `~/.claude/skills/roll-lint/SKILL.md`
2. Start a new conversation and share your CSS/SCSS files

---

## How to Trigger It

Use any of these phrases:

- `roll-lint`
- `CSS cleanup` / `CSS audit`
- `stylesheet audit`
- `design lint`
- `CSS hygiene`
- `style consistency`
- `fix my spacing`
- `clean up my CSS`

---

## The Seven Phases

Each phase follows the same cycle: **scan → report → fix**. Phases are dependency-ordered — no work gets thrown away or redone.

| Phase | Name | What it does |
|---|---|---|
| 1 | Inventory | Runs the census script over all files: spacing, radius, type, z-index, breakpoints, colors (ΔE-clustered), shadows, dividers, durations, affordance coverage. Identifies the developer's intended system and where it drifts. |
| 2 | Foundation | Establishes the consistency baseline — spacing grid (macro/micro tiers), radius set, type scale, elevation ladder, light angle, divider spec, duration rungs. Derived from your values, or validated against your existing tokens. |
| 3 | Dead Weight | Removes unused selectors, duplicate rules, outdated prefixes; flags logical/physical property mixing and nesting-syntax mixing. |
| 4 | Values | Generates the change table (auto vs flagged) and snaps values to the Phase 2 baseline. Fixes nested border-radius math. Makes line-heights unitless. Proposes color and divider merges by ΔE bucket. |
| 5 | Layout & Proportion | Reviews section gaps vs element gaps, narrative order, breakpoint uniformity, and affordance grammar (hover/focus coverage, cursor census, link treatments). |
| 6 | Accessibility | Floor checks: touch targets, focus states, `prefers-reduced-motion`, fluid type, CLS, tabular numerals, and cascade-free contrast pairs — with an honest disclosure of what source-only analysis can't verify. |
| 7 | Naming & Code Quality | Reviews class names for role vs appearance semantics, property ordering, DRY extraction candidates, comments, and collects the optimization suggestions from all phases. |

---

## Three Modes

**Interactive (default)** — At each phase, Claude presents the report and proposed fixes, then waits for your approval before editing files.

**Autonomous** — Say "go through all phases," "just do it all," or "full audit" and Claude runs all seven phases without stopping. Each phase report is still shown (the reports are the audit trail), with judgment calls noted inline. Even here, appearance-changing fixes (shadow angles, color merges, divider consolidation) are only ever proposed — never silently applied.

**Touch-up** — Say "touch-up," "quick pass," or "check against baseline." Reads `roll-lint.baseline.json`, scopes to files changed since the audit (via git when available), and reports only new drift. Never re-derives, never re-scores, never rewrites your baseline.

---

## What You Get at the End

After all seven phases, Claude steps back and gives you:

- **A score** — where the codebase was before the audit and where it is now, on a scale from `-2` (survival) to `+3` (thriving). The delta is what matters. The score is computed from the same core dimensions in every version of roll-lint, so your history stays comparable.
- **A blueprint** — the spacing scale, radius set, type scale, color palette, z-index map, elevation ladder, divider spec, and duration rungs that emerged from the cleanup. A clean starting point if you want to build a token system.
- **A baseline file** — `roll-lint.baseline.json`, the machine-readable blueprint that powers touch-up mode and the edit hook.
- **A clear boundary** — what `roll-lint` does and doesn't do. It gets you to Ground Floor (consistent, clean, no arbitrary values). The next floors (tokens, theming, component libraries) are yours to build on top.

---

## What It Doesn't Do

- Build a token architecture (global → alias → component tiers)
- Set up theming (dark mode, brand variants)
- Create a component library or design system documentation
- Enforce tokens via CI/CD or linting rules
- Handle cross-platform token distribution

These are the next floors. `roll-lint` gives you a correct foundation to build them on.

---

## Tested With

- Claude Sonnet 4.6 on claude.ai (v1); Claude Fable 5 in Cowork (v2 build verification)
- Vanilla CSS and SCSS files
- Projects ranging from single-page portfolios to multi-file SaaS dashboards

---

## Changelog

### 2.0.0 — 2026-07-08

- Added `scripts/inventory.py` (full JSON census; Python 3 stdlib, runs standalone) and `scripts/snap.py` (Phase 4 change table with auto/flag buckets)
- Added touch-up mode + `roll-lint.baseline.json` (written by full audits only)
- Added `references/hook-recipe.md` — PostToolUse hook that fires touch-up on stylesheet edits
- Added designer-eye checks: light-source coherence + elevation ladder, ΔE color clustering (OKLch; thresholds 2.0/5.0, pending validation on first eval run), divider language, duration rungs + easing ladder (external ms ranges removed), affordance grammar (numeric proxies only), tabular numerals, caged contrast pairs (same-block only, with kill criterion pending first eval)
- Added the Design Charter (admission test, exception-only reporting, appearance-material guard, score & Blueprint charters) to SKILL.md
- Restructured for progressive disclosure: scoring ladder + Blueprint spec + baseline schema moved to `references/scoring.md`; SKILL.md now ~210 lines
- New frontmatter: `argument-hint`, `allowed-tools`; `$ARGUMENTS` seeds scope and domain context
- Added `ASSUMPTIONS.md` — every environmental assumption with a source, for freshness monitoring
- Cut: heading-level integrity (fails the admission test). Parked (not approved): typographer's set, layout set

### 1.0.0

- Initial release: seven-phase audit, interactive/autonomous modes, −2…+3 score, Blueprint

---

## Examples

See the [`skills/roll-lint/examples/`](./skills/roll-lint/examples/) folder for sample audit reports and before/after diffs.

---

## Feedback

If something doesn't trigger correctly or a phase behaves unexpectedly, open an issue or reach out at **utilities@niharbhagat.com**.
