#!/usr/bin/env python3
"""
build.py

Renders the resume for one application, runs every guard rail, writes a
one-line summary at the end. Idempotent. Point it at a data.json under
examples/<slug>/ and everything lands in that folder next to it.

The primary deliverable is `resume.html`. The PDF render is opt-in behind
`--pdf`. Parse / NDA / JD-keyword checks all run on the HTML text content
(tags stripped) rather than on PDF extraction.

Usage:
    python3 build.py <slug>
    python3 build.py examples/<slug>/data.json
    python3 build.py <slug> --pdf            # also render resume.pdf

Outputs (under examples/<slug>/):
    resume.html           Primary deliverable. Open in browser, or paste
                          into another tool to hand-finish.
    resume.pdf            Optional, only when --pdf is passed.
    parse-check.txt       HTML text content (ATS sanity check).
    voice-check.txt       Voice scan report.
    build-summary.txt     One-line summary of the run.

Dependencies:
    Required: jinja2
    Optional: openpyxl (app log), weasyprint (--pdf render)
"""

from __future__ import annotations

import argparse
import html as html_lib
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
EXAMPLES_DIR = ROOT / "examples"
FACTS_DIR = ROOT / "facts"
SCRIPTS_DIR = ROOT / "scripts"

REQUIRED_DEPS = ["jinja2"]
OPTIONAL_DEPS = ["openpyxl", "weasyprint"]  # openpyxl: app log. weasyprint: --pdf.


# ─── Dependency check ────────────────────────────────────────────────────


def check_deps() -> None:
    """Verify required packages are importable. Print a friendly install line
    and exit cleanly if anything is missing."""
    missing_required = []
    for pkg in REQUIRED_DEPS:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing_required.append(pkg)

    if missing_required:
        print("build.py — missing required dependencies:")
        print(f"  pip install --break-system-packages {' '.join(REQUIRED_DEPS)}")
        sys.exit(0)


# ─── Slug + data resolution ──────────────────────────────────────────────


def resolve_paths(arg: str) -> tuple[str, Path, Path]:
    """Accept either a slug or a path-to-data.json. Return (slug, data_path, out_dir)."""
    p = Path(arg)
    if p.suffix == ".json" and p.exists():
        out_dir = p.resolve().parent
        slug = out_dir.name
        return slug, p.resolve(), out_dir
    slug = arg.strip("/")
    out_dir = (EXAMPLES_DIR / slug).resolve()
    data_path = out_dir / "data.json"
    return slug, data_path, out_dir


# ─── Render ──────────────────────────────────────────────────────────────


def render_html(data: dict) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("resume.html")
    return template.render(**data)


def render_pdf(html: str, out_path: Path) -> bool:
    """Render the HTML to PDF via WeasyPrint. Returns True on success, False
    if WeasyPrint isn't installed."""
    try:
        from weasyprint import HTML
    except ImportError:
        print("build.py — --pdf requested but weasyprint is not installed.")
        print("  pip install --break-system-packages weasyprint")
        return False
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(out_path))
    return True


# ─── HTML → text ─────────────────────────────────────────────────────────


_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_BLANK_RE = re.compile(r"\n{3,}")


def html_to_text(html: str) -> str:
    """Strip tags and decode entities. Crude on purpose — good enough for
    parse-check, NDA-name search, and JD-keyword presence."""
    s = _STYLE_RE.sub("", html)
    s = _SCRIPT_RE.sub("", s)
    s = _COMMENT_RE.sub("", s)
    s = re.sub(r"</(p|li|div|h[1-6]|header|article|section|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = _TAG_RE.sub("", s)
    s = html_lib.unescape(s)
    s = _WS_RE.sub(" ", s)
    s = _BLANK_RE.sub("\n\n", s)
    return s.strip()


# ─── Parse check ─────────────────────────────────────────────────────────


def parse_test(html_text: str, expected: list[str]) -> tuple[str, list[str]]:
    """Run the parse-check against HTML text content. Returns the extracted
    text and any expected strings not found."""
    extracted = html_to_text(html_text)
    extracted_lc = extracted.lower()
    missing = [s for s in expected if s.lower() not in extracted_lc]
    return extracted, missing


# ─── NDA name check ──────────────────────────────────────────────────────


def load_nda_names() -> list[str]:
    """Read facts/nda-names.txt. One name per line. Lines starting with # are
    comments. Empty lines ignored."""
    path = FACTS_DIR / "nda-names.txt"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def nda_check(text: str, names: list[str]) -> list[str]:
    text_lc = text.lower()
    return [n for n in names if n.lower() in text_lc]


# ─── JD keyword check ────────────────────────────────────────────────────


def extract_jd_keywords(jd_path: Path) -> list[str]:
    """Simple keyword extractor for a soft warning. Returns the top 12
    multi-character non-stopword tokens from the JD."""
    if not jd_path.exists():
        return []
    text = jd_path.read_text(encoding="utf-8").lower()
    tokens = re.findall(r"\b[a-z][a-z\-]{3,}\b", text)
    stop = {
        "the", "and", "for", "you", "your", "with", "our", "this", "that",
        "from", "have", "are", "will", "their", "they", "them", "but", "not",
        "any", "all", "who", "how", "what", "when", "where", "why", "into",
        "across", "while", "about", "also", "more", "than", "been", "such",
        "some", "other", "team", "work", "role", "company",
        "experience", "skills", "years", "year", "job", "position",
    }
    counts: dict[str, int] = {}
    for t in tokens:
        if t in stop:
            continue
        counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:12]]


def jd_keyword_presence(resume_text: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    text_lc = resume_text.lower()
    present = [k for k in keywords if k in text_lc]
    missing = [k for k in keywords if k not in text_lc]
    return present, missing


# ─── Spelling-system check ───────────────────────────────────────────────


BRITISH_FORMS = [
    "behaviour", "behaviours",
    "colour", "colours",
    "organisation", "organisations", "organise", "organised", "organising",
    "analyse", "analysed", "analysing",
    "realise", "realised", "realising",
    "centre", "centres",
    "favourite", "favourites", "favourable",
    "programme", "programmes",
    "defence",
    "licence", "licences",
    "recognise", "recognised", "recognising",
    "summarise", "summarised", "summarising",
    "characterise", "characterised",
    "prioritise", "prioritised", "prioritising",
    "optimise", "optimised", "optimising",
    "utilise", "utilised", "utilising",
    "minimise", "minimised",
    "maximise", "maximised",
    "learnt", "whilst", "amongst",
    "modelling", "modelled",
    "travelling", "travelled",
    "labelled", "labelling",
    "cancelled", "cancelling",
]


def british_spelling_check(text: str) -> list[str]:
    """Return British-spelled forms found in the text. Used as a soft heads-up
    so a single document doesn't mix systems — doesn't prefer one over the other."""
    text_lc = text.lower()
    found: list[str] = []
    seen: set[str] = set()
    for w in BRITISH_FORMS:
        if re.search(r"\b" + re.escape(w) + r"\b", text_lc):
            if w not in seen:
                found.append(w)
                seen.add(w)
    return found


# ─── Voice scan ──────────────────────────────────────────────────────────


def run_voice_scan(data_path: Path, application_path: Path | None, out_path: Path) -> tuple[int, str]:
    """Invoke scripts/scan_voice.py as a subprocess. Returns (exit_code, report)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / "scan_voice.py"),
           "--resume", str(data_path), "--out", str(out_path)]
    if application_path and application_path.exists():
        cmd.extend(["--cover", str(application_path)])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not out_path.exists():
        return result.returncode, result.stdout + result.stderr
    return result.returncode, out_path.read_text(encoding="utf-8") if out_path.exists() else ""


# ─── Page count (logical) ────────────────────────────────────────────────


def logical_page_count(data: dict) -> int:
    """One page + one per role flagged with page_break_after."""
    return 1 + sum(1 for r in data.get("roles", []) if r.get("page_break_after"))


# ─── Build ───────────────────────────────────────────────────────────────


def build(slug: str, data_path: Path, out_dir: Path, render_pdf_too: bool = False) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(data_path.read_text(encoding="utf-8"))

    summary: list[str] = [f"Built {slug}"]
    overall_status = 0

    # 1. Render HTML (primary).
    html = render_html(data)
    html_path = out_dir / "resume.html"
    html_path.write_text(html, encoding="utf-8")

    # 2. Optional PDF.
    if render_pdf_too:
        pdf_path = out_dir / "resume.pdf"
        if render_pdf(html, pdf_path):
            summary.append("pdf: ok")
        else:
            summary.append("pdf: skipped")
            overall_status = max(overall_status, 1)

    # 3. Parse-check on HTML text content.
    expected = [
        data.get("header", {}).get("name", ""),
        data.get("header", {}).get("email", ""),
        *(r.get("company", "") for r in data.get("roles", [])),
    ]
    expected = [e for e in expected if e]
    extracted, missing = parse_test(html, expected)
    (out_dir / "parse-check.txt").write_text(extracted, encoding="utf-8")

    pages = logical_page_count(data)
    summary.append(f"{pages} page{'s' if pages != 1 else ''}")

    if missing:
        summary.append(f"parse: {len(missing)} missing")
        overall_status = max(overall_status, 1)
    else:
        summary.append("parse: clean")

    # 4. Voice scan.
    voice_out = out_dir / "voice-check.txt"
    application_md = out_dir / "application.md"
    voice_code, _ = run_voice_scan(data_path, application_md if application_md.exists() else None, voice_out)
    if voice_code == 0:
        summary.append("voice: clean")
    else:
        summary.append("voice: blocked (see voice-check.txt)")
        overall_status = max(overall_status, 1)

    # 5. NDA name check on HTML text + application.md if present.
    nda_text = extracted
    if application_md.exists():
        nda_text += "\n" + application_md.read_text(encoding="utf-8")
    nda_hits = nda_check(nda_text, load_nda_names())
    if nda_hits:
        summary.append(f"NDA: HIT ({', '.join(nda_hits)})")
        overall_status = max(overall_status, 2)
    else:
        summary.append("NDA: clean")

    # 6. JD keyword presence (soft).
    jd_path = out_dir / "jd.txt"
    keywords = extract_jd_keywords(jd_path)
    if keywords:
        present, missing_kw = jd_keyword_presence(extracted, keywords)
        if missing_kw:
            summary.append(f"JD signal: {len(present)}/{len(keywords)} present")
        else:
            summary.append(f"JD signal: full ({len(keywords)})")

    # 7. Spelling-system heads-up. Soft warn — pick one system per document.
    british = british_spelling_check(extracted)
    if application_md.exists():
        british_cover = british_spelling_check(application_md.read_text(encoding="utf-8"))
        for w in british_cover:
            if w not in british:
                british.append(w)
    if british:
        sample = ", ".join(british[:4])
        more = "" if len(british) <= 4 else f", +{len(british) - 4}"
        summary.append(f"british: {sample}{more}")

    # 8. Write summary.
    summary_line = " · ".join(summary)
    (out_dir / "build-summary.txt").write_text(summary_line + "\n", encoding="utf-8")
    print(summary_line)

    if missing:
        print()
        print("parse-check missing strings:")
        for s in missing:
            print(f"  - {s!r}")
    if british:
        print()
        print("british spellings found (confirm one system per application):")
        for w in british:
            print(f"  - {w}")

    return overall_status


def main() -> int:
    check_deps()

    ap = argparse.ArgumentParser(description="Build the resume + run all checks for one application.")
    ap.add_argument("arg", help="Slug name or path to data.json.")
    ap.add_argument("--pdf", action="store_true",
                    help="Also render resume.pdf via WeasyPrint. Off by default; HTML is primary.")
    args = ap.parse_args()

    slug, data_path, out_dir = resolve_paths(args.arg)
    if not data_path.exists():
        print(f"data.json not found at {data_path}", file=sys.stderr)
        return 2

    return build(slug, data_path, out_dir, render_pdf_too=args.pdf)


if __name__ == "__main__":
    raise SystemExit(main())
