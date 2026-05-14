---
name: run-candidacy
description: Tailors a resume, application answers, and outreach contacts for one job at a time. Built for people applying to design, product, and frontend roles. Triggered by pasting a JD or saying "run candidacy". Run prompts/01 and prompts/02 in your home AI on first use to populate facts/ — the skill is source-linked, so facts/ files become your single source of truth across applications.
---

# run-candidacy

A candidacy skill whose single purpose is to **fill the application in the best way possible, in the candidate's voice, talking directly to the reader, no flattery.** Everything below serves that.

## When to invoke

When the user pastes a job description (text or URL) and asks to tailor a resume, draft application answers, or run candidacy. Slash trigger: `/run-candidacy`. Natural-language triggers: "run candidacy", "tailor my resume for X", "draft my application for X".

## First-run setup

**Check before anything else.** If `facts/identity.md` still contains the string `<TODO: filled by setup>`, the skill has not been set up for this user yet. Do not attempt to generate a resume. Instead, run the setup flow below.

### Setup flow

1. **Surface the two paste-prompts.** Tell the user there are two prompts to run in the AI they talk to most (the one that knows their writing and history). Show the paths: `prompts/01-facts-extraction.md` and `prompts/02-voice-extraction.md`. Suggest the user open prompt 1, paste it into their AI, and paste the AI's response back here.

2. **Parse prompt-1 response.** The AI's reply contains five fenced markdown blocks: `identity.md`, `roles.md`, `receipts.md`, `logistics.md`, `phrasings.md`. Extract each block and write it to `facts/<filename>`, overwriting the placeholder file.

3. **Surface prompt 2.** Once prompt 1 is in, ask the user to run prompt 2 the same way. Parse the AI's reply for three fenced blocks: `voice.md`, `style.md`, `voice-samples.md`. Write each to `facts/<filename>`.

4. **Surface remaining TODOs.** After both prompts land, grep `facts/` for `TODO: ask the user` markers and ask the user inline. One question at a time, conversational, not a bulk dump.

5. **Workflow questions** (4 questions, in the skill itself):
   - Where should application folders be written? Default: `<skill>/examples/<slug>/`. Allow override.
   - Render PDF by default, or just HTML? Default: HTML only. PDF on request via `--pdf`.
   - Enable applications.xlsx logging? Default: yes. If yes, ask for path (default `<skill>/applications.xlsx`, can override via `APP_LOG_PATH` env var).
   - Spelling system: American or British? Default: American.

   Save answers to `.skill-config.json` at the skill root.

6. **Confirm setup complete.** Tell the user the skill is ready. Suggest they paste a JD next.

If the user wants to skip first-run setup and run anyway (e.g., to test with a sample), tell them the resume will use placeholder data and won't be useful for an actual application.

## Inputs (regular run)

- A JD as pasted text or a URL.
- Optional: company name, role title, any context the user wants weighted.
- Optional: an external strategy memo from a hiring consultant, supplied either inline or as a path to a file. Treat consultant notes as a peer source of truth alongside `facts/`.

## Process

1. **Read every file under `facts/`.** Treat them as the source of truth — never invent, never paraphrase past what's there. `facts/voice.md`, `facts/style.md`, and `facts/voice-samples.md` are canonical for tone.

2. **Resolve the slug.** `<company>-<YYYY-MM-DD>` lowercased and dashed. If `examples/<slug>/` already exists, ask before overwriting; default to treating it as a revision pass and append to `notes.md`.

3. **Sibling-application lookup.** Before inferring positioning, read past `examples/*/positioning.md` files and surface the 2–3 closest precedents. "This looks like your <past-slug> run — pull from that data.json?" User decides whether to start from a sibling or fresh.

4. **Ingest the JD.** If a URL was supplied, route by host before fetching.

   **Auto-Chrome hosts.** If the URL host matches any of `linkedin.com`, `glassdoor.com`, `indeed.com`, `wellfound.com`, skip `web_fetch` entirely. Jump straight to the Chrome path below.

   **Otherwise, try `web_fetch` first.** If the response body is < 500 chars, contains JS-app placeholder markers (`<div id="root"></div>` with no content, `Loading…`, `Enable JavaScript`), or hits a sign-in wall string, fall back to Chrome.

   **Chrome path** (`mcp__Claude_in_Chrome__*`, if available):
   - `tabs_context_mcp` with `createIfEmpty: true`.
   - `navigate` to the URL on the returned tab.
   - `get_page_text` — works for static pages and many ATSes that hydrate text into the DOM.
   - If `get_page_text` errors with "page body too large" or "no semantic content", the page is a JS shell. Fall to the ATS API recipe in `facts/atses.md`.

   **ATS API preference.** If the URL points to a known ATS (Ashby, Greenhouse, Lever, Workday, Phenom), prefer the ATS API endpoint over the public page. See `facts/atses.md` for the per-ATS recipe.

   **Fallback of last resort.** If neither web_fetch nor Chrome can reach the content, ask the user to paste the JD body. Do not silently invent context from JD-shaped guessing. Do not use `curl` / `wget` / Python `requests` / any other HTTP path as a workaround.

   Save the cleaned JD as `examples/<slug>/jd.txt`.

   **Promote successful recipes.** When a new ATS shape works, record the recipe in `facts/atses.md`.

5. **Identify the application form fields.** Some applications are resume-only. Many ATSes have multiple custom text fields ("Why this company?", "Biggest project lately", "How do you think about X?", LinkedIn URL, etc.). Identify every field before generating, and produce one H1 section per field in `application.md`.

6. **Run the pre-flight prompt.** Before generating, ask the user three soft questions and surface what will land softer if any answer is no:
   - Have you used the product?
   - Have you seen their public work?
   - Do you know the recipient name?

7. **Write `examples/<slug>/positioning.md`.** Inferred fresh from the JD and consultant notes (if present). Shape:
   ```
   # Positioning: <Company / Role> — <Date>

   ## Role-type
   Free-text label (e.g. "Growth IC at scale", "Dev Tools senior IC").

   ## Audience
   Who reads first, what they care about, read time.

   ## Screening test
   Should read as: ...
   Should not read as: ...

   ## Strategic frame
   1–2 line thesis for this read. If a consultant memo is present, draw the
   strategic frame from there and note in `notes.md` what was applied.

   ## Headline pattern
   none | chronology | thesis. Default: none (off). Use chronology for
   Senior and below if turned on; thesis for Lead / Principal / Staff /
   Head of / Director if turned on.

   ## Register
   formal | direct | stripped — with reasoning.

   ## Vocabulary emphasis
   Emphasize: ...
   Avoid: ...

   ## Voice overrides
   Any voice.md defaults this application overrides, with rationale.

   ## Forward face
   Which receipts to lead with, compress, or drop.
   ```

8. **Generate `examples/<slug>/data.json`.** The resume data structure, drawn from `facts/` and shaped by `positioning.md`. Schema:
   ```json
   {
     "header": { "name", "location", "phone", "email", "site", "site_display" },
     "headline": "...",
     "roles": [
       {
         "company", "title", "dates",
         "bullets": [ "..." ],
         "bullet_groups": [
           { "label", "bullets": [ "...", { "text": "...", "star": true } ] }
         ]
       }
     ],
     "selected_work": [ { "name", "description" } ],
     "education": [
       { "school", "degree", "dates", "notes": [ "..." ] }
     ]
   }
   ```
   Notes:
   - `headline` is optional; only include if `positioning.md` requests it.
   - `bullet_groups` is optional per role (use when the role has weight to carry); `bullets` is the simple form.
   - Per-bullet `star: true` lifts a bullet via a heavier weight.
   - `selected_work` and `education` are opt-in.

9. **Generate `examples/<slug>/application.md`.** One H1 section per field the form asks for. Cover letter is one of those fields; treat it like any other. The register comes from `positioning.md`.

10. **Auto-invoke `python3 scripts/build.py <slug>`.** The build script renders `resume.html` (the primary deliverable), runs the voice scan, runs the parse check on the HTML text content, runs the NDA name check, runs the JD keyword presence check, runs a spelling-system heads-up, and prints a one-line summary. `resume.pdf` is rendered only if `--pdf` was passed.

11. **Self-critique pass.** Before showing v1 to the user, re-read the generated resume and application.md *as if a hiring consultant were reading it.* Rewrite obvious tells. Common ones: generic AI language, conclusion-style openers, sentences ending in a state, anything that fails the "would the user actually say this in a Slack message" test.

12. **Show outputs.** Surface paths to `resume.html`, `application.md`, and `positioning.md` (and `resume.pdf` if `--pdf` was passed). Summarize the build line (`X pages · voice clean · parse clean · NDA clean · JD signal X/Y`). If the spelling-system check surfaced anything, mention it.

13. **Fire the outreach module.** *After* v1 of resume + application.md is generated and shown, automatically run the people-search. Don't wait for the user to ask.

14. **Confirm bullet-group labels.** If the resume uses `bullet_groups`, surface the current labels and ask: "do these labels carry the thesis you want?"

15. **Wait for revision notes.** Multi-pass is first-class. When notes come in, regenerate. `resume.pdf` overwrites each run; `notes.md` accumulates a revision-log section with each pass timestamped at the top. The cover-letter portion of `application.md` is re-evaluated after any resume edit — flag any tone drift before showing.

16. **On "applied", log to applications.xlsx.** When the user confirms the application has been submitted, append a row via `python3 scripts/app_log.py applied <slug> <company> <role> <jd_url> [application_url]`. Skip if xlsx logging was turned off in setup.

17. **Feedback loop.** At the end of any run (or on "applied"), ask once: "Any of today's discoveries to promote back to facts/?" If yes, propose diffs to `facts/phrasings.md` (new approved/killed entries), `facts/voice.md` (new retired phrases), `facts/role-type-examples.md` (a sibling worth carrying forward). User accepts/rejects/edits.

## People search & outreach

Fires automatically after v1 of resume + application.md is generated. Find decision-makers the user can reach out to.

**Search strategy.** Use WebSearch with queries built from the company name and the role's likely surface:
- For larger orgs: `[Company] "head of design" OR "design director" OR "design lead" site:linkedin.com/in`
- For startups: `[Company] founder site:linkedin.com/in`, `[Company] design site:linkedin.com/in`
- For the specific team: `[Company] [team name] "manager" OR "lead" site:linkedin.com/in`

**Returns.** Parse 3–5 candidates from snippets with: name, role, LinkedIn URL (where surfaceable), and a one-line evidence note showing where the info came from.

**Caveat.** LinkedIn blocks direct scraping. WebSearch surfaces names + titles from snippets, which is usually enough. When a result is partial, surface what was found and ask the user to confirm or fill in.

**On user's confirmation:**
- Write `examples/<slug>/contacts.md` with each confirmed contact and a short tailored outreach draft per contact. Tune the draft to the role-type from `positioning.md` and the candidate's voice — direct, no pander.
- Append to `applications.xlsx` "Outreach" sheet via `python3 scripts/app_log.py outreach-from-json <slug> <contacts.json>` (or one-at-a-time with `app_log.py outreach`).

## Voice + style constraints

Every generated line obeys `facts/voice.md` and `facts/style.md`. The universal floor is enforced by the voice scan in `scripts/scan_voice.py`. Em dashes block. Generic clichés, conclusion-style openers, and pander language warn.

- **Per-application overrides** live in `positioning.md` → "Voice overrides" with stated rationale. `voice.md` governs every line the override doesn't touch.
- **Voice samples** in `facts/voice-samples.md` are the model the skill writes against. When generating prose, the skill should re-read the three samples before drafting bullets or cover-letter sentences — rules without samples produce bland output.

## Source-of-truth rule

Every fact comes from `facts/`. If a JD asks for a receipt the facts don't carry, ask the user before fabricating. Never inflate scale markers. Never list a client name not in `facts/roles.md`, `facts/receipts.md`, or the do-not-name list in `facts/nda-names.txt`.

## Outputs (per application)

Per `examples/<slug>/`:

- `positioning.md` — the per-application positioning doc (step 7).
- `jd.txt` — the cleaned JD.
- `data.json` — resume data structure.
- `application.md` — single file, one H1 per form field, including the cover letter.
- `resume.html` — primary deliverable. Opens standalone in a browser.
- `resume.pdf` — optional. Only when `--pdf` was passed to the build.
- `contacts.md` — outreach candidates with tailored drafts.
- `notes.md` — revision log (each pass timestamped) + a "Recruiter-call topics" section.
- `consultant.md` — optional. Strategy memos from a hiring consultant.
- `parse-check.txt`, `voice-check.txt`, `build-summary.txt` — generated by `build.py`.

## File map

```
run-candidacy/
├── SKILL.md                  this file
├── README.md                 user-facing intro + setup steps
├── .skill-config.json        workflow choices from first-run setup
├── prompts/
│   ├── 01-facts-extraction.md   paste into home AI on first run
│   └── 02-voice-extraction.md   paste into home AI on first run
├── facts/
│   ├── identity.md           name, contact, current period, headline
│   ├── roles.md              per-role facts: artifacts, audience, scale
│   ├── receipts.md           cross-cutting evidence
│   ├── voice.md              voice rules (universal floor + user)
│   ├── style.md              lexicon: spelling, punctuation, contact format
│   ├── voice-samples.md      three real sentences in the candidate's voice
│   ├── logistics.md          location, visa, timezone, working arrangement
│   ├── phrasings.md          tagged verbatim language (approved/killed/neutral)
│   ├── role-type-examples.md reference patterns from past runs
│   ├── atses.md              per-ATS ingestion recipes
│   └── nda-names.txt         names that must never appear in output
├── templates/
│   └── resume.html           default template — Butterick-style, system fonts
├── scripts/
│   ├── build.py              renders the resume + runs every check
│   ├── scan_voice.py         voice scan (called by build.py)
│   └── app_log.py            applications.xlsx management
└── examples/
    ├── default/              minimal reference run with placeholder data
    └── <slug>/               one folder per real application
        ├── positioning.md
        ├── jd.txt
        ├── data.json
        ├── application.md
        ├── resume.html
        ├── resume.pdf (optional, --pdf)
        ├── contacts.md
        ├── notes.md
        ├── consultant.md (optional)
        ├── parse-check.txt
        ├── voice-check.txt
        └── build-summary.txt
```

## Dependencies

- Python 3.9+
- `jinja2` (required) — template rendering
- `openpyxl` (optional) — applications.xlsx logging
- `weasyprint` (optional) — `--pdf` rendering. System libraries required (see [WeasyPrint install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)).

Install with:
```
pip install --break-system-packages jinja2 openpyxl weasyprint
```

## Customizing the template

The default template (`templates/resume.html`) follows Butterick's "Typography for Lawyers" résumé principles: substance in Georgia serif, structure in Helvetica sans, two pages allowed, generous margins, gentle bullets. System fonts only — no web fonts bundled.

If you want a different look, edit `templates/resume.html` directly. The Jinja variables it consumes are documented in step 8 of the Process section above.
