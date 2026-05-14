# Prompt 2 of 2 — Voice extraction

Run this after prompt 1 lands. Paste it into the same AI that produced the facts. The AI should now have context on who the candidate is — this prompt asks it to describe how they write.

If the AI doesn't have prior writing samples from you, paste 2–4 real writing samples (a cover letter, a Slack post you're proud of, a blog post, an email) into the chat before pasting this prompt below. Voice cannot be inferred from rules alone — samples are required for the third block.

===

You are filling out two voice-spec files for the **run-candidacy** résumé skill. Your output goes directly into source files — keep to the schema, no commentary outside the fenced blocks.

**Rules**

- Voice rules describe *this candidate's* voice, not "good résumé writing in general." If you don't have evidence, write `TODO: ask the user`.
- The third block (voice samples) is mandatory. Three real sentences in the candidate's voice, each paired with a one-line note on what makes it on-voice. If you do not have writing samples, output `TODO: ask the user for 2-3 writing samples (Slack posts, emails, blog excerpts) and re-run this prompt` in place of the samples — do not invent.
- Output the two fenced markdown blocks below. Nothing else outside the blocks.

---

```voice.md
# voice.md

The voice the resume and application answers must speak in. Source of truth for tone.

## Precedence

Voice.md is the global default. Per-application `positioning.md` is the override for the lines it touches, with stated rationale.

## Writing constraints (universal floor — keep these)

- No invented metrics. If a number isn't real, don't write it.
- No conclusion-style verbs as bullet openers ("transformed," "drove," "owned," "championed"). Lead with the move, not the verdict.
- No generic AI / résumé clichés: "leveraged," "spearheaded," "passionate about," "world-class," "best-in-class," "results-driven."
- No flattery toward the company in cover letters. Direct, not pander.
- No em dashes. Use periods or commas.

## Writing constraints (candidate-specific)

<TODO: list the candidate's specific voice rules. Examples of the shape (do not copy literally — write the candidate's actual rules):
- Short sentences. No long clause chains.
- Conversational, not formal.
- Talks to the reader, not at them.
- Avoid X-shaped openers.
- Specific to this candidate's style.>

## Underselling vs. flattening

Compressing a receipt past the point where it disappears is worse than over-claiming. Name what the candidate actually did, not the role's job description.

## Show the action. Do not name the action.

Lines should describe what happened. The reader infers impact. The candidate does not declare impact.

**Wrong shape:**
- <TODO: 1–2 examples of "wrong" lines that read as conclusion / claim>

**Right shape:**
- <TODO: 1–2 examples of "right" lines that describe the action and let the reader infer>
```

```style.md
# style.md

Lexicon and formatting choices applied across every output.

## Spelling and case

Universal floor:

- Capitalize proper nouns canonically (React, TypeScript, PostgreSQL, etc.).
- Acronyms uppercase unless the brand spells them otherwise.

Candidate-specific:

- <TODO: lowercase/uppercase choices the candidate cares about — e.g. "web3 lowercase", "iOS lowercase i", "ChatGPT one word". List only the ones the candidate has a real preference on.>

## Punctuation

- No em dashes. Use periods or commas.
- En dashes for date ranges with spaces: `Jan 2025 – present`.
- Oxford comma in lists of three or more.

## Numbers

- Numerals for counts: "5 engineers", not "five engineers".
- Currency abbreviated: `$2M`, not `2 million dollars`.
- Qualitative reads ("cut time-to-value by half") often stronger than synthetic precision. Use real percentages only when the audience cares about exact figures.

## Spelling system

<TODO: American or British. Pick one and stick to it across a single application. The build script flags mixed usage.>

## Contact format on the résumé

- Phone: <TODO: candidate's preferred format, e.g. "+1 415 555 0199" with spaces between groupings>
- Email: <TODO: the email that should appear on the resume>
- Site: <TODO: site URL — render as live link in PDF>
```

```voice-samples.md
# voice-samples.md

Three real sentences in the candidate's voice with a one-line note on what makes each one on-voice. These are the model the skill writes against, not just the rules above.

## Sample 1

> <TODO: a real sentence written by the candidate — from a blog post, Slack message, email, cover letter, etc.>

**Why this is on-voice:** <TODO: one line — what about this sentence sounds like the candidate. E.g. "Short. States the move. No claim about impact.">

## Sample 2

> <TODO: second real sentence>

**Why this is on-voice:** <TODO>

## Sample 3

> <TODO: third real sentence>

**Why this is on-voice:** <TODO>
```

Three files. Voice rules, style rules, and three real voice samples. If you have to write `TODO: ask the user` anywhere, write it honestly — the skill prefers a missing field over an invented one.
