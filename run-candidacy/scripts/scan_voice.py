#!/usr/bin/env python3
"""
scan_voice.py

Voice scan for run-candidacy. Reads text input (resume bullets, cover letter,
application answers) and emits a structured voice-check report.

The scan enforces the universal floor documented in facts/voice.md
programmatically. Em dashes block the build. Everything else warns.

Universal floor (encoded below):
- Em dashes (BLOCK)
- Generic résumé clichés (WARN): leveraged, spearheaded, passionate about,
  world-class, best-in-class, results-driven, synergy, value-add, thought
  leader, ninja, rockstar, guru
- Conclusion-style bullet openers (WARN): transformed, drove, owned,
  championed, spearheaded, delivered, established, introduced, cultivated,
  executed, advocated for
- Pander language in cover letters (SOFT WARN): world-class team, incredible
  mission, truly remarkable, your mission resonates, love what you're
  building, inspired by your work

Extend by editing facts/voice.md and adding rules to this file. Keep the
universal floor — it's what makes the scan useful out of the box.

Usage:
    python3 scan_voice.py <input_path>
    python3 scan_voice.py --resume <data.json> --cover <application.md>
    cat text | python3 scan_voice.py -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ─── Universal floor ──────────────────────────────────────────────────────

# Blocker.
EM_DASH = "—"

# Generic résumé clichés. WARN anywhere they appear.
CLICHES = {
    "leveraged", "spearheaded", "passionate about", "world-class",
    "best-in-class", "results-driven", "synergy", "value-add",
    "thought leader", "ninja", "rockstar", "guru",
    "team player", "go-getter", "self-starter",
}

# Conclusion-style verbs. WARN when used as the leading verb of a bullet.
CONCLUSION_OPENERS = {
    "transformed", "drove", "owned", "championed", "spearheaded",
    "delivered", "established", "introduced", "cultivated", "executed",
    "advocated", "revolutionized", "optimized", "streamlined", "crafted",
    "evangelized",
}

# Pander language. SOFT WARN — cover letters shouldn't flatter.
PANDER_PATTERNS = {
    "world-class team", "incredible mission", "inspired by your work",
    "truly remarkable", "i've always admired", "your mission resonates",
    "amazing product", "incredible product", "love what you're building",
}

# Action-vs-claim: sentences ending in an abstract state read as claims.
# Soft heuristic — flag any sentence whose last content word is one of these.
STATE_NOUNS = {
    "instinct", "shape", "feel", "sense", "ability", "capacity",
    "understanding", "awareness", "culture", "trust", "confidence",
    "clarity", "experience", "rhythm", "cadence", "alignment",
}


# ─── Report types ─────────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str   # "block" | "warn" | "soft"
    rule: str
    line_no: int
    line: str
    match: str
    note: str = ""


# ─── Scan ─────────────────────────────────────────────────────────────────

WORD_RE = re.compile(r"\b[\w'-]+\b")


def _find(text: str, patterns: Iterable[str], lowercase: bool = True) -> list[tuple[int, str, str]]:
    """Return (line_no, line, matched_pattern) for each pattern hit in text."""
    hits: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        haystack = line.lower() if lowercase else line
        for pat in patterns:
            needle = pat.lower() if lowercase else pat
            if needle in haystack:
                hits.append((i, line.strip(), pat))
    return hits


def _find_conclusion_openers(text: str) -> list[tuple[int, str, str]]:
    """Flag lines whose leading verb is a conclusion-style opener."""
    hits = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # Strip leading bullet markers so we can see the real first word.
        stripped = re.sub(r"^[-*•·\d.)\s]+", "", stripped)
        if not stripped:
            continue
        m = WORD_RE.match(stripped)
        if m and m.group(0).lower() in CONCLUSION_OPENERS:
            hits.append((i, stripped, m.group(0)))
    return hits


def _find_state_endings(text: str) -> list[tuple[int, str, str]]:
    """Flag sentences whose last content word is an abstract state noun."""
    hits = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip().rstrip(".!?;:,")
        if not stripped:
            continue
        words = WORD_RE.findall(stripped)
        if not words:
            continue
        last = words[-1].lower()
        if last in STATE_NOUNS:
            hits.append((i, line.strip(), last))
    return hits


def scan(text: str) -> list[Issue]:
    issues: list[Issue] = []

    # Block: em dashes.
    for line_no, line, _ in _find(text, [EM_DASH], lowercase=False):
        issues.append(Issue("block", "em-dash", line_no, line, EM_DASH,
                            "Em dashes block the build. Use periods or commas."))

    # Warn: cliché phrases.
    for line_no, line, p in _find(text, CLICHES):
        issues.append(Issue("warn", "cliche", line_no, line, p,
                            "Generic résumé phrasing. Rewrite as the move."))

    # Warn: conclusion-style openers.
    for line_no, line, w in _find_conclusion_openers(text):
        issues.append(Issue("warn", "conclusion-opener", line_no, line, w,
                            "Bullet leads with a conclusion verb. Rewrite as the action."))

    # Warn: action-vs-claim (state endings).
    for line_no, line, w in _find_state_endings(text):
        issues.append(Issue("warn", "action-vs-claim", line_no, line, w,
                            "Sentence ends in a state. Likely claiming an effect — rewrite as the action."))

    # Soft warn: pander language.
    for line_no, line, p in _find(text, PANDER_PATTERNS):
        issues.append(Issue("soft", "pander", line_no, line, p,
                            "Reads as flattery. Stay direct."))

    return issues


# ─── Render ───────────────────────────────────────────────────────────────


def render_report(issues: list[Issue], source_label: str = "") -> str:
    if not issues:
        return f"voice-check: clean{(' · ' + source_label) if source_label else ''}\n"

    by_sev: dict[str, list[Issue]] = {"block": [], "warn": [], "soft": []}
    for it in issues:
        by_sev[it.severity].append(it)

    out = []
    header = "voice-check"
    if source_label:
        header += f" · {source_label}"
    counts = f"{len(by_sev['block'])} block · {len(by_sev['warn'])} warn · {len(by_sev['soft'])} soft"
    out.append(f"{header} · {counts}\n")

    for sev in ("block", "warn", "soft"):
        if not by_sev[sev]:
            continue
        out.append(f"\n[{sev.upper()}]")
        for it in by_sev[sev]:
            loc = f"L{it.line_no}" if it.line_no else "—"
            out.append(f"  {loc} · {it.rule} · {it.match!r}")
            if it.line:
                out.append(f"     {it.line}")
            if it.note:
                out.append(f"     ↳ {it.note}")
    out.append("")
    return "\n".join(out)


# ─── Inputs from data.json + application.md ───────────────────────────────


def _bullet_text(b) -> str:
    """Accept a bullet as a plain string or as a dict with a `text` key
    (per-bullet star form). Return the prose to scan."""
    if isinstance(b, dict):
        return b.get("text", "")
    return b or ""


def text_from_data_json(path: Path) -> str:
    """Pull all writer-authored prose out of a data.json file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[str] = []

    chunks.append(data.get("headline", ""))
    for role in data.get("roles", []):
        chunks.append(role.get("title", ""))
        for bullet in role.get("bullets", []):
            chunks.append(_bullet_text(bullet))
        for group in role.get("bullet_groups", []):
            chunks.append(group.get("label", ""))
            for b in group.get("bullets", group.get("items", [])):
                chunks.append(_bullet_text(b))
    return "\n".join(c for c in chunks if c)


# ─── CLI ──────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="Voice scan for run-candidacy.")
    ap.add_argument("path", nargs="?", help="Path to text file. Use '-' for stdin.")
    ap.add_argument("--resume", help="data.json — extract writer prose.")
    ap.add_argument("--cover", help="application.md — scan whole file.")
    ap.add_argument("--out", help="Write the report to this path. Default: stdout.")
    args = ap.parse_args()

    blocks: list[tuple[str, str]] = []

    if args.resume:
        blocks.append(("resume", text_from_data_json(Path(args.resume))))
    if args.cover:
        blocks.append(("cover", Path(args.cover).read_text(encoding="utf-8")))
    if args.path == "-":
        blocks.append(("stdin", sys.stdin.read()))
    elif args.path:
        blocks.append((args.path, Path(args.path).read_text(encoding="utf-8")))

    if not blocks:
        ap.print_help()
        return 2

    all_issues: list[Issue] = []
    sections: list[str] = []
    for label, text in blocks:
        issues = scan(text)
        all_issues.extend(issues)
        sections.append(render_report(issues, label))

    report = "\n".join(sections)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    else:
        print(report, end="")

    blockers = [i for i in all_issues if i.severity == "block"]
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
