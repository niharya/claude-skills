# Hook Recipe: Auto Touch-Up on Stylesheet Edits

A documented `settings.json` snippet for Claude Code that fires roll-lint's **touch-up mode** whenever Claude edits a `.css`, `.scss`, or `.less` file. Shipped as documentation rather than skill frontmatter on purpose: you can read exactly what it does before installing it, and the skill stays portable to agents that don't support hooks.

**Why touch-up and never the full audit:** the hook runs after every stylesheet edit, potentially many times a session. The full audit re-derives the baseline, asks intake questions, scores, and writes `roll-lint.baseline.json` — running it on every edit would be slow, chatty, and worse, would let a drifting edit *rewrite the baseline it should be checked against*. Touch-up is the right shape: it reads the baseline (never writes it), scopes to changed files, and reports only new drift. If no baseline exists yet, it says so and offers the full audit once.

## The snippet

Add to `.claude/settings.json` in the project (or `~/.claude/settings.json` for all projects):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json,sys; d=json.load(sys.stdin); p=(d.get('tool_input') or {}).get('file_path',''); print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse','additionalContext':'A stylesheet was just edited ('+p+'). Run the roll-lint skill in touch-up mode: read roll-lint.baseline.json and report only new drift in the changed files. Do not run the full audit and do not write the baseline.'}})) if p.endswith(('.css','.scss','.less')) else None\""
          }
        ]
      }
    ]
  }
}
```

## Notes

- The matcher fires on every `Edit`/`Write`/`MultiEdit`; the command itself filters by file extension and stays silent for non-stylesheets (no output = no-op).
- Uses `python3` for the JSON handling since roll-lint already assumes Python 3 is present for its scripts. If you prefer `jq`:

```bash
jq -r 'select((.tool_input.file_path // "") | test("\\.(css|scss|less)$")) | {hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:"A stylesheet was just edited (\(.tool_input.file_path)). Run the roll-lint skill in touch-up mode against roll-lint.baseline.json. Do not run the full audit and do not write the baseline."}}' 
```

- The hook only *suggests* touch-up via `additionalContext`; Claude still decides when to act, so mid-refactor edit bursts don't trigger a lint after every keystroke-sized change.
- Hook support and payload shape are Claude Code–specific (see ASSUMPTIONS.md). On agents without hooks, invoke touch-up manually: "roll-lint touch-up".
