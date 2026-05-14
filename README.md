# Claude Skills

A collection of custom skills for Claude — written by a product designer, for designers, frontend developers, and people applying to jobs.

Claude Skills are instruction sets you place in your Claude environment that teach Claude a specific, structured workflow. Instead of writing long prompts from scratch every time, a skill defines the process once, deeply, so Claude can follow it consistently across sessions.

These skills are built around real design and frontend work. They've been used in production — on personal portfolios, client projects, and live job applications — and refined from that experience.

---

## Skills

| Skill | What it does | Built for |
|---|---|---|
| [lay-ui](./lay-ui/) | Translates Figma designs into production-ready code using a three-station component-first workflow | Product designers, UI/UX designers |
| [roll-lint](./roll-lint/) | Audits and cleans CSS/SCSS files through seven dependency-ordered phases using systems-design thinking | Frontend developers, designers who write CSS |
| [run-candidacy](./run-candidacy/) | One job at a time. Tailored resume, application answers, and outreach contacts — generated from your own facts, written in your own voice | Anyone applying to design, product, or frontend roles |

---

## How Claude Skills Work

Skills live in your Claude environment as `.md` files. When Claude loads them, it follows the instructions inside to run a structured, multi-step process — rather than responding ad-hoc.

### Setup (claude.ai)

1. Open [claude.ai](https://claude.ai) and go to **Settings → Skills** (or your connected environment's skill directory)
2. Copy the `SKILL.md` file for the skill you want to use into your skills folder
3. Start a new conversation and trigger the skill using the phrases listed in each skill's README

### Setup (Claude Code / API)

If you're using Claude via the API or Claude Code, place the skill folder (`SKILL.md` plus any supporting files) into your skill directory as per your setup.

> **Note:** `lay-ui` requires the **Figma MCP server** to be connected. See the [lay-ui README](./lay-ui/README.md) for setup details.
>
> **Note:** `run-candidacy` requires a first-run setup pass — two paste-prompts you run in the AI you talk to most. See the [run-candidacy README](./run-candidacy/README.md) for the flow.

---

## Feedback

These skills are actively maintained. If something doesn't trigger correctly, a phase behaves unexpectedly, or you have a suggestion — open an issue or send a note to **utilities@niharbhagat.com**.

---

## License

MIT — free to use, adapt, and share. Attribution appreciated but not required.
