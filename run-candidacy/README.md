# run-candidacy

**One job at a time. Tailored resume, application answers, outreach contacts — generated from your own facts, written in your own voice.**

A Claude skill for anyone applying to jobs. Paste a JD, get back a positioning doc, a tailored resume (HTML and optionally PDF), an `application.md` with one section per form field, and a short list of decision-makers worth reaching out to. Every line is checked against a voice scan that blocks em dashes and warns on generic résumé clichés.

---

## The Problem It Solves

Most resume tools either generate generic output that sounds like every other resume, or require you to write everything yourself and just format it. Neither helps with the actual hard part: deciding what to emphasize for *this* role, in *your* voice, without drifting into cliché.

`run-candidacy` separates the work into layers:

1. **Your facts** live in `facts/` — identity, roles, receipts, voice rules, lexicon. Source of truth, written once, refined over time.
2. **Per-application positioning** lives in `examples/<slug>/positioning.md` — inferred fresh from the JD, decides the headline pattern, what to lead with, what to compress.
3. **Generated output** lives next to the positioning doc — resume, application answers, contacts. Re-generates on every revision pass.

The skill never invents facts. If the JD asks for something your `facts/` don't carry, it asks before fabricating.

---

## First-run setup

The skill ships with placeholder facts. Before your first real run, populate `facts/` by running two prompts in the AI you talk to most (the one that knows your writing and history).

1. Open [`skills/run-candidacy/prompts/01-facts-extraction.md`](./skills/run-candidacy/prompts/01-facts-extraction.md). Copy everything below the `===` line. Paste it into your home AI. Paste the AI's response back into Claude with `run-candidacy` active — it will write your identity, roles, receipts, logistics, and approved phrasings into `facts/`.

2. Open [`skills/run-candidacy/prompts/02-voice-extraction.md`](./skills/run-candidacy/prompts/02-voice-extraction.md). Same flow — paste, run, paste back. This fills your voice rules, lexicon, and three real voice samples.

3. Answer four short workflow questions in Claude (output folder, PDF default, app-log on/off, spelling system). The skill stores them in `.skill-config.json`.

If your home AI doesn't have writing samples from you, paste 2–4 of them (a Slack post, a blog excerpt, a cover letter, an email) into the chat before running prompt 2. Voice can't be inferred from rules alone.

---

## Prerequisites

- [Claude](https://claude.ai) with Claude Code or a compatible Claude environment
- Python 3.9+ for the build script
- `jinja2` (required), `openpyxl` (optional, for application logging), `weasyprint` (optional, for PDF rendering)

Install Python deps:

```
pip install --break-system-packages jinja2 openpyxl weasyprint
```

WeasyPrint additionally needs system libraries (Pango, Cairo). See its [install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) if PDF rendering fails. HTML output works without it.

---

## Installation

### Quick install (Claude Code, via marketplace)

```
/plugin marketplace add niharya/claude-skills
/plugin install run-candidacy@skill-shelf
```

Then open a new conversation, run the first-run setup above, and paste a JD or say "run candidacy".

### Manual install (fallback)

1. Copy the [`skills/run-candidacy/`](./skills/run-candidacy/) folder (which contains `SKILL.md` plus `prompts/`, `facts/`, `templates/`, `scripts/`, and `examples/`) into your Claude skills directory.
   - On claude.ai: Settings → Skills → add new skill, point at `SKILL.md`
   - On Claude Code (without the marketplace): place at `~/.claude/skills/run-candidacy/` (or your project's skill path)
2. Open a new conversation. Run setup (above).
3. Paste a JD or say "run candidacy".

---

## How to Trigger It

- `/run-candidacy`
- `run candidacy`
- `tailor my resume for <company>`
- `draft my application for <company>`
- Or paste a JD URL / text and ask Claude to handle it.

---

## What Happens in a Session

### 1. JD ingestion
The skill detects the JD source. LinkedIn, Glassdoor, Indeed, Wellfound — Chrome required, since these are sign-in walls. Public Ashby / Greenhouse / Lever / Workday postings — fetched from the public API where possible. The cleaned JD lands in `examples/<slug>/jd.txt`.

### 2. Pre-flight
Three soft questions before generation: have you used the product, have you seen their public work, do you know the recipient name. Each "no" is a signal that lands softer in the cover letter — the skill adjusts framing accordingly.

### 3. Positioning
The skill writes `positioning.md`: role-type, audience, screening test, strategic frame, headline pattern, register, vocabulary emphasis. This is the per-application decision document — every downstream output is shaped by it.

### 4. Resume + application
`data.json` is generated from `facts/` and shaped by `positioning.md`. The build script renders `resume.html`, runs the voice scan, runs a parse-check on the HTML text content, runs the NDA name check, and surfaces a JD-keyword-presence signal. `application.md` is generated alongside, with one H1 section per form field (cover letter included as one of those sections).

### 5. Outreach
After v1 of resume + application is ready, the skill auto-fires a people-search: head of design, design director, founders, team leads at the company. Returns 3–5 candidates with names, titles, LinkedIn URLs where surfaceable, and one-line evidence notes. On confirmation, writes `contacts.md` with tailored outreach drafts per contact.

### 6. Multi-pass revisions
Multi-pass is first-class. Send revision notes; the skill regenerates `data.json` and `application.md`, overwrites `resume.html` (and `resume.pdf` if rendered), and appends a timestamped entry to `notes.md`.

### 7. On "applied"
When you confirm the application has been submitted, the skill logs it to `applications.xlsx` (if app-log was enabled in setup) and asks if any phrasings or role-type patterns from this run should be promoted back to `facts/` for future applications.

---

## Default template

The default template at [`skills/run-candidacy/templates/resume.html`](./skills/run-candidacy/templates/resume.html) follows the principles in Matthew Butterick's [résumé chapter from *Typography for Lawyers*](https://typographyforlawyers.com/resumes.html):

- **Substance gets visual weight.** Employer / school names in serif (Georgia), slightly heavier. Section labels in quieter sans (Helvetica), small and lowercase. The reader scans for the names you've worked with first — give them the weight.
- **Two pages are fine.** No one-page squeeze. Generous margins, breathable line length, gentle dot bullets.
- **System fonts only.** Georgia + Helvetica/Arial. No web fonts to bundle, no rendering surprises across machines or PDF engines.

If you want a different look, edit [`skills/run-candidacy/templates/resume.html`](./skills/run-candidacy/templates/resume.html) directly. The Jinja data shape is documented in [`skills/run-candidacy/SKILL.md`](./skills/run-candidacy/SKILL.md).

---

## File layout

```
run-candidacy/
├── README.md                 this file (kept at plugin root for GitHub display)
├── .claude-plugin/
│   └── plugin.json           plugin manifest (marketplace install)
└── skills/
    └── run-candidacy/
        ├── SKILL.md          the instructions Claude follows
        ├── prompts/          paste-prompts for first-run setup
        ├── facts/            your single source of truth
        ├── templates/        default resume template
        ├── scripts/          build + voice scan + application log
        └── examples/         one folder per application
```

---

## Privacy

The `facts/` folder (at [`skills/run-candidacy/facts/`](./skills/run-candidacy/facts/)) contains your identity, contact info, work history, and voice samples. It stays on your machine. The skill never uploads it anywhere. If you fork this repo to use the skill, gitignore these three before pushing anything public:

```
run-candidacy/skills/run-candidacy/facts/
run-candidacy/skills/run-candidacy/examples/
run-candidacy/skills/run-candidacy/applications.xlsx
```

(If you've copied the skill out to a standalone `~/.claude/skills/run-candidacy/` location, the gitignore-able paths are just `facts/`, `examples/`, and `applications.xlsx`.)

---

## Tested With

- Claude Sonnet 4.6 on Claude Code
- Python 3.11
- HTML output across browsers; PDF output via WeasyPrint

---

## Feedback

If a step doesn't behave as expected or a generated line reads wrong, open an issue or reach out at **utilities@niharbhagat.com**.
