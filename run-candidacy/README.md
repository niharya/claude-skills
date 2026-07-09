# run-candidacy

**One job at a time. Tailored resume, application answers, outreach contacts — generated from your own facts, written in your own voice.**

A Claude skill for anyone applying to product, design, design-leadership, or frontend roles. Paste a JD, get back a structured strategic read of the role, a tailored resume (HTML and optionally PDF), an `application.md` with one section per form field (cover letter included), and a short list of decision-makers worth reaching out to. Every generated line is checked against a voice scan that blocks em-dashes, prestige adjectives, and pander phrases.

For the architectural reference — governing principles, tool boundaries, frozen decisions — see [`skills/run-candidacy/ARCHITECTURE.md`](./skills/run-candidacy/ARCHITECTURE.md).

---

## The problem it solves

Most résumé tools either generate generic output that sounds like every other résumé, or require you to write everything yourself and just format it. Neither helps with the actual hard part: deciding what to emphasize for *this* role, in *your* voice, without drifting into cliché.

`run-candidacy` separates the work into layers:

1. **Your facts** live under `facts/` — identity (`identity.yaml`), receipts (`receipts.json`, tagged against capability primitives), voice constraints (`voice_rules.yaml`). Source of truth, written once at setup, refined over time.
2. **Per-application signals** live in `examples/<slug>/signals.yaml` — a structured strategic read produced from the JD, schema-validated, with every field tagged for provenance (extracted vs. inferred vs. synthesized).
3. **Generated output** lives next to the signals — resume, `application.md`, contacts. Re-generates on every revision pass.

The skill never invents facts. If the JD asks for something your `facts/` don't carry, it asks before fabricating. Prestige adjectives never influence retrieval. Low-signal JDs produce sparse output rather than padded output.

---

## First-run setup

The skill ships with placeholder facts. Before your first real run, populate `facts/` by running two prompts in the AI you talk to most (the one that knows your writing and history).

1. Open [`skills/run-candidacy/prompts/01-facts-extraction.md`](./skills/run-candidacy/prompts/01-facts-extraction.md). Copy everything below the `===` line. Paste it into your home AI. Paste the AI's response back into Claude with `run-candidacy` active — it will write `identity.yaml`, `receipts.json`, and `data.base.json`.

2. Open [`skills/run-candidacy/prompts/02-voice-extraction.md`](./skills/run-candidacy/prompts/02-voice-extraction.md). Same flow — paste, run, paste back. This appends candidate-specific anti-patterns to `voice_rules.yaml` on top of the universal floor that ships with the skill, and writes `voice-samples.md` as a setup-only reference.

3. Answer four short workflow questions in Claude (output folder, PDF default, application-log on/off, spelling system). The skill stores them in `.skill-config.json`.

If your home AI doesn't have writing samples from you, paste 2–4 of them (a Slack post, a blog excerpt, a cover letter, an email) into the chat before running prompt 2. Voice cannot be inferred from rules alone.

---

## Prerequisites

- [Claude](https://claude.ai) with Claude Code or a compatible Claude environment
- Python 3.9+
- `pyyaml` (required, for voice rules), `jinja2` (required, for the resume template), `openpyxl` (optional, for application logging), `weasyprint` (optional, for PDF rendering)

Install Python dependencies:

```
pip install --break-system-packages pyyaml jinja2 openpyxl weasyprint
```

WeasyPrint additionally needs system libraries (Pango, Cairo). See its [install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) if PDF rendering fails. HTML output works without it.

---

## Installation

### Quick install (Claude Code, via marketplace)

```
/plugin marketplace add niharya/skills-drawer
/plugin install run-candidacy@skill-shelf
```

Then open a new conversation, run the first-run setup above, and paste a JD or say "run candidacy".

### Manual install (fallback)

1. Copy the [`skills/run-candidacy/`](./skills/run-candidacy/) folder (which contains `SKILL.md`, `ARCHITECTURE.md`, plus `prompts/`, `facts/`, `tools/`, `templates/`, `scripts/`, and `examples/`) into your Claude skills directory.
   - On claude.ai: Settings → Skills → add new skill, point at `SKILL.md`
   - On Claude Code (without the marketplace): place at `~/.claude/skills/run-candidacy/` (or your project's skill path)
2. Open a new conversation. Run setup (above).
3. Paste a JD or say "run candidacy".

---

## How to trigger it

- `/run-candidacy`
- `run candidacy`
- `tailor my resume for <company>`
- `draft my application for <company>`
- Or paste a JD URL / text and ask Claude to handle it.

---

## What happens in a session

The skill runs a five-tool default flow. Each tool has a strict contract documented in [`skills/run-candidacy/tools/`](./skills/run-candidacy/tools/).

### 1. ingest_jd
The skill detects the JD source. LinkedIn, Glassdoor, Indeed, Wellfound — uses Chrome (these are sign-in-walled JS apps). Public Ashby / Greenhouse / Lever / Workday postings — fetched from the public API where possible. The cleaned JD lands in `examples/<slug>/jd.txt`, with the application form fields preserved at the bottom when surfaceable.

### 2. analyze_role
The intelligence layer. Reads the JD, writes `examples/<slug>/signals.yaml` — a structured strategic read with provenance markers (META / EXTRACTED / INFERRED / SYNTHESIS) and hard caps on every list. Sets `signal_strength` (high / medium / low / noise), which scales every downstream step.

### 3. generate_resume
Adapts the baseline `data.base.json` against the signals — re-orders bullets, lightly rephrases up to 6 of them (fewer for lower signal_strength), mirrors operational JD terms truthfully. Renders `resume.html`. The build script runs the voice scan, the parse check, the NDA name check, and a spelling-system check. PDF rendering is opt-in (`--pdf`).

### 4. write_application
Produces `examples/<slug>/application.md` with one H1 section per text field the form asks for. The cover-letter section is short, grounded, names 2-3 receipts, addresses gaps honestly when signals flagged any, and closes with your default closing line from `voice_rules.yaml`. Length scales with `signal_strength`.

### 5. log_applied
When you confirm the application has been submitted, the skill appends a row to `applications.xlsx` (if logging was enabled in setup). Pure bookkeeping — no auto-analysis, no auto-rebuild.

### Opt-in tools

Three opt-in tools never auto-fire:

- **fit_note_signals** — when you want to write a personal fit note yourself, this surfaces signal-level fodder (anomalies, tensions, asymmetries, useful receipts, likely reader concerns). It does NOT draft prose.
- **pressure_test** — paste your own draft prose; the tool flags inflation, vagueness, consultant tone, pander, emotional overreach, strategic over-signaling, and identity drift. It does NOT rewrite.
- **people_search** — after you've applied, surfaces up to 3 decision-makers you could reach out to, with one-line evidence notes. Does NOT auto-draft outreach messages.

---

## Default template

The default template at [`skills/run-candidacy/templates/resume.html`](./skills/run-candidacy/templates/resume.html) follows the principles in Matthew Butterick's [résumé chapter from *Typography for Lawyers*](https://typographyforlawyers.com/resumes.html):

- **Substance gets visual weight.** Employer / school names in serif (Georgia), slightly heavier. Section labels in quieter sans (Helvetica), small and lowercase. The reader scans for the names you've worked with first — give them the weight.
- **Two pages are fine.** No one-page squeeze. Generous margins, breathable line length, gentle dot bullets.
- **System fonts only.** Georgia + Helvetica/Arial. No web fonts to bundle, no rendering surprises across machines or PDF engines.

If you want a different look, edit [`skills/run-candidacy/templates/resume.html`](./skills/run-candidacy/templates/resume.html) directly. The Jinja data shape is documented in [`skills/run-candidacy/SKILL.md`](./skills/run-candidacy/SKILL.md) and the contract for the underlying signals lives in [`skills/run-candidacy/signals.schema.yaml`](./skills/run-candidacy/signals.schema.yaml).

---

## File layout

```
run-candidacy/
├── README.md                 this file (kept at plugin root for GitHub display)
├── .claude-plugin/
│   └── plugin.json           plugin manifest (marketplace install)
└── skills/
    └── run-candidacy/
        ├── SKILL.md          the router Claude follows
        ├── ARCHITECTURE.md   governing principles + frozen decisions
        ├── signals.schema.yaml   contract for per-application signals.yaml
        ├── signals.example.yaml  illustrative reference
        ├── prompts/          paste-prompts for first-run setup
        ├── facts/            your single source of truth
        │   ├── identity.yaml
        │   ├── receipts.json
        │   ├── voice_rules.yaml
        │   ├── voice-samples.md  (setup-only reference)
        │   ├── atses.md
        │   └── nda-names.txt
        ├── tools/            per-tool contracts
        │   ├── ingest_jd.md
        │   ├── analyze_role.md
        │   ├── generate_resume.md
        │   ├── write_application.md
        │   ├── fit_note_signals.md
        │   ├── pressure_test.md
        │   ├── people_search.md
        │   └── log_applied.md
        ├── templates/        default resume template
        ├── scripts/          build + voice scan + application log
        └── examples/         one folder per application
```

---

## Privacy

The `facts/` folder (at [`skills/run-candidacy/facts/`](./skills/run-candidacy/facts/)) contains your identity, contact info, work history, and voice samples. It stays on your machine. The skill never uploads it anywhere. If you fork this repo to use the skill, gitignore these before pushing anything public:

```
run-candidacy/skills/run-candidacy/facts/
run-candidacy/skills/run-candidacy/examples/
run-candidacy/skills/run-candidacy/applications.xlsx
```

(If you've copied the skill out to a standalone `~/.claude/skills/run-candidacy/` location, the gitignore-able paths are just `facts/`, `examples/`, and `applications.xlsx`.)

---

## Tested with

- Claude Sonnet 4.6 / Opus 4.x on Claude Code
- Python 3.11
- HTML output across browsers; PDF output via WeasyPrint

---

## Feedback

If a step doesn't behave as expected or a generated line reads wrong, open an issue or reach out at **utilities@niharbhagat.com**.
