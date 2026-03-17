# lay-ui

**Figma to production-ready code — component-first, no context switching.**

A Claude skill that translates Figma designs into clean HTML/CSS (or your chosen framework) using a structured three-station workflow. Built around how a designer actually thinks, not how code gets generated.

---

## The Problem It Solves

When you hand a Figma file to an AI and say "turn this into code," you get something that roughly resembles the design — but loses all the nuance. The spacing drifts. The typography doesn't follow the scale. The components aren't reusable. You spend as much time fixing as you saved.

The real issue isn't the AI — it's the process. Dumping everything into one prompt collapses all the decisions into one moment, which is too much for any system (human or AI) to handle cleanly.

`lay-ui` fixes this by breaking the work into three stations that match how a designer already thinks:

1. **Logistics** — clear the technical setup out of the way before creative work starts
2. **Components** — build every UI piece individually, get it approved, understand how pieces relate
3. **Layouts** — assemble approved components into full pages and fine-tune composition

At each station, you're only ever thinking about one kind of problem. No context switching. You stay in the creative director role throughout.

---

## Prerequisites

- [Claude](https://claude.ai) (claude.ai or Claude Code)
- **Figma MCP server** connected to your Claude environment
  - Set up via [Figma's MCP documentation](https://developers.figma.com/docs/figma-mcp-server/)
  - Required for `get_screenshot`, `get_design_context`, and `get_variable_defs` tool calls

---

## Installation

1. Copy [`SKILL.md`](./SKILL.md) into your Claude skills directory
   - On claude.ai: Settings → Skills → add new skill
   - On Claude Code: place in `/mnt/skills/user/lay-ui/SKILL.md`
2. Ensure your Figma MCP server is connected and authenticated
3. Start a new conversation

---

## How to Trigger It

Use any of these phrases to activate the skill:

- `lay-ui`
- `implement design`
- `lay out the UI`
- `build Figma design`
- `implement component`
- `generate code from Figma`

Or simply paste a Figma URL and ask for code output — the skill will activate automatically.

---

## What Happens in a Session

### Station 1 · Logistics
Claude collects everything it needs before touching any code: your Figma links, viewport targets, framework preference (or defaults to vanilla HTML/CSS), font loading, and file structure. Technical decisions are handled by Claude — you're only asked for genuine creative choices.

### Station 2 · Components
Claude inventories every component in your Figma file, classifies them into a main/sub-component hierarchy, and builds a live preview sheet. Each component is built individually and approved before the next one starts. A layer map (for z-index management) and a relationship map (how components control/trigger each other) are established before layouts begin.

### Station 3 · Layouts
Approved components are assembled into full page layouts. You review composition, proportion, and fine-tuning. Animation is deferred to a dedicated pass after everything is structurally approved.

Throughout all three stations, Claude uses a **breadcrumb system** — every message states the current station, what was just completed, and what's next. This keeps long sessions on track even across many rounds of iteration.

---

## Key Behaviours

**Vanilla-first** — Unless you specify a framework (Tailwind, React, etc.) in Station 1, all output is vanilla HTML/CSS. As atomic as possible.

**Component background context** — Components are always previewed against the same background they'll sit on in the final layout — not the default preview sheet color. This prevents incorrect contrast decisions.

**Mid-session design changes** — If you update your Figma file mid-session, the protocol is to create the update in a new frame and link that frame. This gives you version history in Figma and gives Claude an unambiguous reference for what changed.

**No technical decisions surfaced** — Claude handles all choices about ports, servers, tooling, and code architecture. You're only asked if there's a genuine conflict that requires your input.

---

## Tested With

- Claude Sonnet 4.6 on claude.ai
- Figma MCP server (as of March 2026)
- Vanilla HTML/CSS output; React output with explicit request

---

## Examples

See the [`examples/`](./examples/) folder for sample component sheets and layout outputs.

---

## Feedback

If something doesn't trigger correctly or a station behaves unexpectedly, open an issue or reach out at **utilities@niharbhagat.com**.
