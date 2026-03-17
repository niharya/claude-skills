# roll-lint

**A systems-design-aware CSS/SCSS auditor — for designers who write code.**

A Claude skill that audits and cleans up stylesheets through seven dependency-ordered phases. It reads your codebase as a systems designer would: finding the patterns you already chose, making them airtight, and flagging the places where they drift.

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

1. Copy [`SKILL.md`](./SKILL.md) into your Claude skills directory
   - On claude.ai: Settings → Skills → add new skill
   - On Claude Code: place in `/mnt/skills/user/roll-lint/SKILL.md`
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
| 1 | Inventory | Reads all files. Builds frequency tables for spacing, radius, type, z-index, breakpoints, color. Identifies the developer's intended system and where it drifts. |
| 2 | Foundation | Establishes the consistency baseline — spacing grid, radius set, type scale. Either derives these from raw values (if no token system exists) or validates against existing custom properties. |
| 3 | Dead Weight | Removes unused selectors, duplicate rules, dead media queries, and overridden declarations. |
| 4 | Values | Snaps spacing, radius, and type values to the baseline from Phase 2. Fixes nested border-radius math. Makes line-heights unitless. |
| 5 | Layout & Proportion | Reviews section gaps vs element gaps, touch target sizes, transition consistency. Checks mobile responsiveness. |
| 6 | Accessibility | Audits focus states, motion sensitivity (`prefers-reduced-motion`), color contrast, ARIA-affecting styles. |
| 7 | Naming & Code Quality | Reviews class names for role vs appearance semantics, property ordering, `!important` usage, nesting depth, and documentation comments. |

---

## Two Modes

**Interactive (default)** — At each phase, Claude presents the report and proposed fixes, then waits for your approval before editing files.

**Autonomous** — Say "go through all phases," "just do it all," or "full audit" and Claude runs all seven phases without stopping. Each phase report is still shown (the reports are the audit trail), with judgment calls noted inline.

---

## What You Get at the End

After all seven phases, Claude steps back and gives you:

- **A score** — where the codebase was before the audit and where it is now, on a scale from `-2` (survival) to `+3` (thriving). The delta is what matters.
- **A blueprint** — the spacing scale, radius set, type scale, color palette, and z-index map that emerged from the cleanup. A clean starting point if you want to build a token system.
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

- Claude Sonnet 4.6 on claude.ai
- Vanilla CSS and SCSS files
- Projects ranging from single-page portfolios to multi-file SaaS dashboards

---

## Examples

See the [`examples/`](./examples/) folder for sample audit reports and before/after diffs.

---

## Feedback

If something doesn't trigger correctly or a phase behaves unexpectedly, open an issue or reach out at **utilities@niharbhagat.com**.
