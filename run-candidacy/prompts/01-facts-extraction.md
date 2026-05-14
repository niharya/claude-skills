# Prompt 1 of 2 — Facts extraction

Copy everything below the `===` line into the AI you talk to most (the one that knows your work, your writing, your history). Reply to its output by pasting both blocks back into the run-candidacy skill.

If the AI doesn't know you well — fresh ChatGPT, no memory, no prior chats — paste in 1–2 writing samples and a quick bio before the prompt below, or it will guess.

===

You are helping me set up a résumé skill called **run-candidacy**. Your job is to fill out the candidate facts files exactly to the schema below. The skill will paste your reply directly into source-of-truth files, so structure matters.

**Rules**

- Fill every section. If you do not know an answer, write `TODO: ask the user` on that line. Do not invent.
- Use the candidate's own phrasing wherever you have evidence of it. Avoid generic résumé phrasing ("leveraged," "spearheaded," "passionate about," "world-class").
- Keep bullets factual. Describe the move, not the conclusion. Prefer "wrote the intake form and shipped it in 4 days" over "drove operational excellence."
- No em dashes. Use periods or commas.
- Output the five fenced markdown blocks below, in order, with the exact filenames as fenced labels. Nothing else outside the blocks.

---

```identity.md
# identity.md

Self-framing, current state, and contact. The header of every resume is built from this file.

## Display name

<TODO: full name as it should appear on the resume>

## Title line

**Default:** <TODO: the title the candidate uses by default, e.g. "Product Designer">

JD-tailored swaps (titles the candidate can credibly hold, listed from junior to senior):

- <TODO: list 2–4 acceptable title swaps, e.g. "Senior Product Designer", "Design Lead", "Head of Design">

Default fallback: <TODO: the safest default>.

## Location

<TODO: city, country. If open to remote, note it on its own line below.>

## Contact

- Email: <TODO>
- Phone: <TODO, formatted with spaces, e.g. "+1 415 555 0199">
- Site: <TODO: portfolio URL, or remove this line if none>
- LinkedIn: <TODO: linkedin.com/in/handle>

## Pronouns

<TODO: pronouns, or "Not included" if the candidate omits them>

## Current period

**Period:** <TODO: e.g. "March 2024 – present">

**Label:** <TODO: e.g. "Independent practice", "Freelance", "Sabbatical", or current employer + role>

What the period contains:

- <TODO: 2–4 bullets — what the candidate is doing right now>

What shipped:

- <TODO: notable artifacts from this period, or "Nothing public yet" if applicable>

What the candidate is looking for next:

> <TODO: 1–2 sentence forward-looking statement, in the candidate's voice. Used in cover letters.>

## Headline paragraph (optional)

The opening of the resume. Used only if `positioning.md` requests it for a given application. Off by default.

Default chronology form (factual, no thesis):

> <TODO: 2–3 sentences of factual chronology, most recent first. No claims, no thesis. Example shape: "I do X today. Before that I worked at Y as a Z. Before that I co-founded W.">

Optional thesis form (used for senior / lead / director roles):

> <TODO: 1–2 sentences leading with a strategic frame, then chronology underneath. Example shape: "I design X for Y while the systems themselves are still evolving. At Z, that meant …">
```

```roles.md
# roles.md

Per-role facts. The resume body is built from this. List most recent first.

Each role gets one H2 (`##`) with the fields below. If a role has no public bullets (NDA, fresh job, etc.), say so explicitly under that role rather than omitting it.

## <TODO: most recent company>

- **Title:** <TODO>
- **Dates:** <TODO: en dash between, e.g. "Jan 2023 – Mar 2024">
- **Location:** <TODO, or "Remote">
- **Audience:** <TODO: who used the work — e.g. "internal sales team", "self-serve users", "developers integrating SDK">
- **Scale markers:** <TODO: real numbers the candidate has, e.g. "$2M ARR", "12 engineers", "8 PMs", "200k MAU". Skip if unknown.>
- **System / artifacts shipped:** <TODO: what concretely got built, owned, written>

Bullets (3–6, factual, action-described not impact-declared):

- <TODO: bullet 1>
- <TODO: bullet 2>
- <TODO: bullet 3>

## <TODO: prior company>

(repeat the same shape)

## <TODO: earliest relevant role>

(repeat the same shape)
```

```receipts.md
# receipts.md

Cross-cutting evidence the candidate carries across roles. Not every receipt appears on every resume — `positioning.md` chooses which to feature per application.

## Talks, writing, public output

- <TODO: talk title or post title, venue, year. Or "None yet" if applicable.>

## Named clients (safe to list publicly)

- <TODO: client name, what was done. Mark NDA-only clients in nda-names.txt instead — never list them here.>

## References available on request

- <TODO: number of available references, or "Available on request" generic line>

## Side projects

- <TODO: name, one-line description, link or "private". Or "None".>

## Recognition / awards

- <TODO: anything notable. Or "None".>
```

```logistics.md
# logistics.md

Things a recruiter or hiring manager needs to know that don't fit on the résumé body but affect the conversation.

## Location

<TODO: city, country>

## Time zone

<TODO: e.g. "IST, GMT+5:30">

## Working arrangement

<TODO: open to one or more of: in-office, hybrid, remote. Geographic constraints if any.>

## Visa / work authorization

<TODO: e.g. "Citizen of <country>. Need sponsorship for: <list>. No sponsorship needed for: <list>." Or "Open to discuss.">

## Notice period / start date

<TODO: e.g. "Available immediately", "30 days notice", "Starting <date>">

## Compensation range (private — only for recruiter calls)

<TODO: range, currency, base+variable+equity if relevant. Or "Open to discuss." Stays in this file, never goes on the resume.>
```

```phrasings.md
# phrasings.md

Verbatim language the candidate uses. The skill prefers these phrases verbatim over paraphrases. Three tags: APPROVED (use freely), NEUTRAL (use if it fits), KILLED (never use, even if the AI generated it).

## APPROVED — phrases the candidate has used and would use again

- <TODO: phrase or sentence the candidate has actually used in past writing, with a one-line note on the context>

## NEUTRAL — phrases the candidate is fine with but doesn't lean on

- <TODO: as above>

## KILLED — phrases that sound wrong for this candidate

- <TODO: any phrasing the candidate has explicitly rejected, or that doesn't sound like them>
```

That's the schema. Five files. Fill every TODO honestly — `TODO: ask the user` is fine for anything you don't know. The skill will surface those gaps and ask the candidate directly on its next run.
