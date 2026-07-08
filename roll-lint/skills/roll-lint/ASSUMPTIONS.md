# ASSUMPTIONS.md

Every environmental assumption this skill makes, one per line, with a source. This file is the input contract for a future skill-freshness monitor — diff these claims against the linked docs/changelogs to detect rot. Last verified: 2026-07-08.

- `SKILL.md` frontmatter `name` + `description` drive auto-triggering in Claude Code, claude.ai, and Cowork — https://code.claude.com/docs/en/skills
- `allowed-tools` frontmatter is honored by Claude Code CLI; other surfaces (claude.ai, Cowork, Agent SDK) ignore it safely — https://code.claude.com/docs/en/skills
- `argument-hint` frontmatter and `$ARGUMENTS` substitution apply when the skill is invoked as a slash command (`/roll-lint <args>`); support outside Claude Code varies and unexpanded `$ARGUMENTS` text degrades gracefully — https://code.claude.com/docs/en/slash-commands
- Skills are exposed as slash commands and as model-invocable skills; `disable-model-invocation` is deliberately NOT set because auto-triggering is core to the skill's value — https://code.claude.com/docs/en/skills
- `context: fork` is deliberately NOT set because interactive mode's per-phase approvals require conversation continuity — https://code.claude.com/docs/en/skills
- Progressive disclosure: only SKILL.md loads at trigger time; `references/*.md` load only when the skill text points to them and the agent reads them — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- `scripts/inventory.py` and `scripts/snap.py` require Python 3 (3.8+) stdlib only, no pip installs, executed via the agent's shell tool — assumed present in Claude Code, the claude.ai/Cowork Linux VM, and buyers' local environments
- Scripts are executed, not read: their code never enters context, only their JSON/table output — https://code.claude.com/docs/en/skills (bundled-files guidance)
- `snap.py` imports color math and ΔE thresholds from `inventory.py`, so both files must stay in the same `scripts/` directory
- The skill's install location may be read-only (plugin cache); scripts write nothing to the skill directory — census/baseline files are written to the project or a temp path
- `roll-lint.baseline.json` is written to the audited project's root, assuming the agent has write access there
- Touch-up mode's changed-file scoping assumes `git` is available in the shell; without git it falls back to the user-given scope
- `references/hook-recipe.md` assumes Claude Code `PostToolUse` hooks: matcher on tool name, tool payload as JSON on stdin, `hookSpecificOutput.additionalContext` as the feedback channel — https://code.claude.com/docs/en/hooks
- The hook recipe assumes `python3` (or optionally `jq`) on the user's PATH at hook-execution time
- Distribution assumes the skill-shelf plugin-marketplace layout (`roll-lint/skills/roll-lint/` with `.claude-plugin/marketplace.json` at repo root) — https://code.claude.com/docs/en/plugins
- WCAG contrast math follows WCAG 2.x relative-luminance formulas — https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
- OKLab conversion uses Björn Ottosson's published sRGB↔OKLab matrices; ΔE is OKLab Euclidean distance × 100 (thresholds 2.0 / 5.0 pending validation on the first eval run) — https://bottosson.github.io/posts/oklab/
