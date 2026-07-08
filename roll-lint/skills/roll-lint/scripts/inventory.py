#!/usr/bin/env python3
"""
roll-lint census — inventory.py

Parses CSS/SCSS/LESS files and emits ONE JSON census object on stdout.
Counting lives here; judgment lives in the skill prose. The reader
interprets this JSON — it never re-counts.

Usage:
    python3 inventory.py <file-or-dir> [more paths...]

Python 3 stdlib only. No pip installs. Works standalone.

ΔE color thresholds live HERE and nowhere else (snap.py consumes the
bucket labels this script assigns):
    ΔE <  DELTA_E_NEAR   → "near-duplicate"  (auto-proposable merge)
    ΔE <  DELTA_E_AMBIG  → "ambiguous"       (flag-only)
    ΔE >= DELTA_E_AMBIG  → "distinct"        (untouched)
ΔE = euclidean distance in OKLab × DELTA_E_SCALE.
"""

import json
import math
import os
import re
import sys
from collections import OrderedDict

TOOL_VERSION = "2.0.0"

# ── Tunable constants (single source of truth) ─────────────────────────
DELTA_E_NEAR = 2.0
DELTA_E_AMBIG = 5.0
DELTA_E_SCALE = 100.0
MAX_LOCS = 40          # cap stored locations per value; count stays exact
ANOMALY_MAX_COUNT = 2  # values appearing <= this often are anomaly candidates

CSS_EXTS = (".css", ".scss", ".less")

SPACING_PROPS = re.compile(
    r"^(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$"
    r"|^(gap|row-gap|column-gap|grid-gap|grid-row-gap|grid-column-gap)$"
)
PHYSICAL_PROPS = re.compile(
    r"^(margin|padding|border)-(top|right|bottom|left)(-.*)?$|^(top|right|bottom|left)$"
)
LOGICAL_PROPS = re.compile(
    r"^(margin|padding|border|inset)-(inline|block)(-(start|end))?(-.*)?$|^inset$"
)
INTERACTIVE_EL = re.compile(r"(?<![\w.#\-\[])(a|button|input|select|textarea|summary)(?![\w\-])")
ROLE_BUTTON = re.compile(r"\[\s*role\s*[*^|~]?=\s*['\"]?(button|link)['\"]?\s*\]")
PSEUDO_STRIP = re.compile(r":(hover|focus(-visible|-within)?|active|visited)\b")
NUMERIC_SELECTOR = re.compile(
    r"(?<![\w\-])(table|thead|tbody|td|th)(?![\w\-])"
    r"|(price|amount|total|numeric|number|currency|stat|metric|count|qty|quantity|tabular)",
    re.IGNORECASE,
)
LENGTH_TOKEN = re.compile(r"^-?\d*\.?\d+(px|rem|em|%|vw|vh|vmin|vmax|ch|ex|pt|fr)?$")
DURATION_TOKEN = re.compile(r"(?<![\w.])(\d*\.?\d+)(ms|s)(?![\w])")
EASING_TOKEN = re.compile(
    r"(cubic-bezier\([^)]*\)|steps\([^)]*\)|linear\([^)]*\)"
    r"|\b(ease-in-out|ease-in|ease-out|ease|linear|step-start|step-end)\b)"
)

NAMED_COLORS = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0),
    "orange": (255, 165, 0), "purple": (128, 0, 128), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "silver": (192, 192, 192), "maroon": (128, 0, 0),
    "navy": (0, 0, 128), "teal": (0, 128, 128), "olive": (128, 128, 0),
    "aqua": (0, 255, 255), "cyan": (0, 255, 255), "fuchsia": (255, 0, 255),
    "magenta": (255, 0, 255), "lime": (0, 255, 0), "whitesmoke": (245, 245, 245),
    "lightgray": (211, 211, 211), "lightgrey": (211, 211, 211),
    "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169),
    "dimgray": (105, 105, 105), "dimgrey": (105, 105, 105),
    "gainsboro": (220, 220, 220), "tomato": (255, 99, 71),
    "rebeccapurple": (102, 51, 153), "transparent": None, "currentcolor": None,
    "inherit": None, "initial": None, "unset": None, "none": None,
}


# ── Comment/string-safe pre-pass ───────────────────────────────────────

def strip_comments(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
        elif c == "/" and i + 1 < n and text[i + 1] == "/" and (i == 0 or text[i - 1] != ":"):
            j = text.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(text[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ── Block parser ───────────────────────────────────────────────────────

def split_top_commas(s):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_file(path, relname):
    """Returns list of blocks:
    {selector, line, path(rule selectors), media, decls:[(prop,value,line,important)]}"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = strip_comments(f.read())
    blocks, stack, block_stack = [], [], []
    buf, buf_line, line = "", 1, 1

    def flush_decl(cur_line):
        s = buf.strip()
        if not s or not block_stack:
            return
        if ":" not in s or s.startswith("@"):
            return
        prop, _, value = s.partition(":")
        prop, value = prop.strip().lower(), value.strip()
        if not prop or not value:
            return
        important = "!important" in value.lower()
        value = re.sub(r"\s*!\s*important\s*$", "", value, flags=re.IGNORECASE)
        block_stack[-1]["decls"].append((prop, value, buf_line, important))

    for ch in text:
        if ch == "{":
            sel = " ".join(buf.split())
            kind = "media" if sel.startswith("@media") else ("at" if sel.startswith("@") else "rule")
            stack.append((kind, sel))
            blk = {
                "file": relname, "selector": sel, "line": line, "kind": kind,
                "path": [s for k, s in stack if k == "rule"],
                "media": [s[6:].strip() for k, s in stack if k == "media"],
                "decls": [],
            }
            blocks.append(blk)
            block_stack.append(blk)
            buf = ""
        elif ch == "}":
            flush_decl(line)
            buf = ""
            if stack:
                stack.pop()
            if block_stack:
                block_stack.pop()
        elif ch == ";":
            flush_decl(line)
            buf = ""
        else:
            if not buf.strip() and ch.strip():
                buf_line = line
            buf += ch
        if ch == "\n":
            line += 1
    return blocks


def resolve_selectors(path_sels):
    """Resolve SCSS-style nesting (incl. &) into full selectors."""
    full = [""]
    for seg in path_sels:
        parts = split_top_commas(seg) or [seg]
        nxt = []
        for base in full:
            for p in parts:
                if "&" in p:
                    nxt.append(p.replace("&", base).strip() if base else p.replace("&", "").strip())
                else:
                    nxt.append((base + " " + p).strip())
        full = nxt[:64]  # combinatorial safety
    return full


# ── Color math (sRGB → OKLab, WCAG luminance) ──────────────────────────

def _clamp01(x):
    return max(0.0, min(1.0, x))


def parse_color(tok):
    """Return (r, g, b, a) floats 0–1, or None if not a parseable color."""
    t = tok.strip().lower()
    if t in NAMED_COLORS:
        rgb = NAMED_COLORS[t]
        if rgb is None:
            return None
        return (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
    m = re.fullmatch(r"#([0-9a-f]{3,8})", t)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            h += "ff"
        if len(h) != 8:
            return None
        r, g, b, a = (int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
        return (r / 255, g / 255, b / 255, a / 255)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", t)
    if m:
        raw = re.split(r"[,\s/]+", m.group(1).strip())
        raw = [x for x in raw if x]
        if len(raw) < 3:
            return None
        def chan(x):
            return _clamp01(float(x[:-1]) / 100) if x.endswith("%") else _clamp01(float(x) / 255)
        try:
            r, g, b = (chan(x) for x in raw[:3])
            a = 1.0
            if len(raw) >= 4:
                x = raw[3]
                a = _clamp01(float(x[:-1]) / 100 if x.endswith("%") else float(x))
            return (r, g, b, a)
        except ValueError:
            return None
    m = re.fullmatch(r"hsla?\(([^)]*)\)", t)
    if m:
        raw = re.split(r"[,\s/]+", m.group(1).strip())
        raw = [x for x in raw if x]
        if len(raw) < 3:
            return None
        try:
            h = float(re.sub(r"deg$", "", raw[0])) % 360
            s = float(raw[1].rstrip("%")) / 100
            l = float(raw[2].rstrip("%")) / 100
            a = 1.0
            if len(raw) >= 4:
                x = raw[3]
                a = _clamp01(float(x[:-1]) / 100 if x.endswith("%") else float(x))
            c = (1 - abs(2 * l - 1)) * s
            x2 = c * (1 - abs((h / 60) % 2 - 1))
            mm = l - c / 2
            r, g, b = [(c, x2, 0), (x2, c, 0), (0, c, x2),
                       (0, x2, c), (x2, 0, c), (c, 0, x2)][int(h // 60) % 6]
            return (r + mm, g + mm, b + mm, a)
        except ValueError:
            return None
    return None


def srgb_to_oklab(r, g, b):
    def lin(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def oklch_to_oklab(tok):
    m = re.fullmatch(r"oklch\(([^)]*)\)", tok.strip().lower())
    if not m:
        return None
    raw = [x for x in re.split(r"[\s/]+", m.group(1).strip()) if x]
    if len(raw) < 3:
        return None
    try:
        L = float(raw[0].rstrip("%")) / (100 if raw[0].endswith("%") else 1)
        C = float(raw[1])
        H = math.radians(float(re.sub(r"deg$", "", raw[2])))
        return (L, C * math.cos(H), C * math.sin(H))
    except ValueError:
        return None


def delta_e(lab1, lab2):
    return DELTA_E_SCALE * math.dist(lab1, lab2)


def wcag_luminance(r, g, b):
    def lin(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(c1, c2):
    l1, l2 = wcag_luminance(*c1[:3]), wcag_luminance(*c2[:3])
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


COLOR_TOKEN = re.compile(
    r"(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\)"
    r"|oklab\([^)]*\)|color-mix\([^)]*\)"
    r"|(?<![\w\-.$@#])(" + "|".join(NAMED_COLORS) + r")(?![\w\-]))"
)


def color_format(tok):
    t = tok.lower()
    for fmt in ("color-mix", "oklch", "oklab", "hsl", "rgb"):
        if t.startswith(fmt):
            return fmt
    if t.startswith("#"):
        return "hex"
    return "named"


# ── Census tables ──────────────────────────────────────────────────────

def new_table():
    return {}


def add(table, key, loc):
    e = table.setdefault(str(key), {"count": 0, "locations": []})
    e["count"] += 1
    if len(e["locations"]) < MAX_LOCS:
        e["locations"].append(loc)


def finalize(table):
    out = OrderedDict()
    for k in sorted(table, key=lambda k: (-table[k]["count"], k)):
        e = table[k]
        o = {"count": e["count"], "locations": e["locations"]}
        if e["count"] > len(e["locations"]):
            o["locations_truncated"] = True
        out[k] = o
    return out


def shadow_angle(x, y):
    sx = (x > 0) - (x < 0)
    sy = (y > 0) - (y < 0)
    names = {
        (0, 0): "centered", (0, 1): "down", (0, -1): "up",
        (1, 0): "right", (-1, 0): "left",
        (1, 1): "down-right", (-1, 1): "down-left",
        (1, -1): "up-right", (-1, -1): "up-left",
    }
    return names[(sx, sy)]


def px(tok):
    m = re.fullmatch(r"(-?\d*\.?\d+)px", tok)
    return float(m.group(1)) if m else None


def num(tok):
    m = re.fullmatch(r"(-?\d*\.?\d+)([a-z%]*)", tok)
    return (float(m.group(1)), m.group(2)) if m else (None, None)


# ── Main census ────────────────────────────────────────────────────────

def collect_files(paths):
    files = []
    for p in paths:
        if os.path.isfile(p) and p.lower().endswith(CSS_EXTS):
            files.append((p, os.path.basename(p)))
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "dist", "build", "vendor")]
                for nname in sorted(names):
                    if nname.lower().endswith(CSS_EXTS):
                        fp = os.path.join(root, nname)
                        files.append((fp, os.path.relpath(fp, p)))
    return files


def census(paths):
    files = collect_files(paths)
    spacing, radius, font_size = new_table(), new_table(), new_table()
    lh_unitless, lh_px, lh_other = new_table(), new_table(), new_table()
    z_index, breakpoints, cursor_t = new_table(), new_table(), new_table()
    color_fmt, colors_t, easings, durations = new_table(), new_table(), new_table(), new_table()
    text_wrap_t, border_combos, id_selectors = new_table(), new_table(), new_table()
    important_locs, shadows = [], []
    cp_defined, cp_used = new_table(), new_table()
    physical, logical = new_table(), new_table()
    modern_fns = new_table()
    contrast_checked, contrast_unverifiable = [], []
    fvn_numeric_blocks, fvn_missing = [], []
    max_depth, depth_file = 0, None
    nesting = {"native_css_nested_rules": 0, "preprocessor_nested_rules": 0}
    interactive = {}   # base selector -> {"hover": bool, "focus": bool, "loc": loc}
    link_patterns = {}  # frozen pattern -> {count, example, locations}
    container_queries, media_blocks_per_file = new_table(), new_table()

    all_blocks = []
    for fp, rel in files:
        try:
            all_blocks.extend(parse_file(fp, rel))
        except OSError as e:
            print(f"warning: cannot read {fp}: {e}", file=sys.stderr)

    # pass 1: selector-level facts + hover/focus registry
    for blk in all_blocks:
        loc = f"{blk['file']}:{blk['line']}"
        if blk["kind"] == "media":
            add(media_blocks_per_file, blk["file"], loc)
            for m in re.finditer(r"\(\s*(min|max)-(width|height)\s*:\s*([^)]+?)\s*\)", blk["selector"]):
                add(breakpoints, f"{m.group(1)}-{m.group(2)}: {m.group(3)}", loc)
            continue
        if blk["kind"] == "at":
            if blk["selector"].startswith("@container"):
                add(container_queries, blk["selector"], loc)
            continue
        depth = len(blk["path"])
        if depth > max_depth:
            max_depth, depth_file = depth, loc
        if depth >= 2:
            key = "native_css_nested_rules" if blk["file"].lower().endswith(".css") else "preprocessor_nested_rules"
            nesting[key] += 1
        for rs in resolve_selectors(blk["path"]):
            if "#" in rs:
                for m in re.finditer(r"#[\w\-]+", rs):
                    add(id_selectors, m.group(0), loc)
            if INTERACTIVE_EL.search(rs) or ROLE_BUTTON.search(rs):
                base = " ".join(PSEUDO_STRIP.sub("", rs).split()).strip()
                if not base:
                    continue
                entry = interactive.setdefault(base, {"hover": False, "focus": False, "location": loc})
                if ":hover" in rs:
                    entry["hover"] = True
                if ":focus" in rs:
                    entry["focus"] = True

    # pass 2: declaration-level census
    for blk in all_blocks:
        if blk["kind"] != "rule":
            continue
        resolved = resolve_selectors(blk["path"])
        decl_map = {p: v for (p, v, _, _) in blk["decls"]}
        for prop, value, dline, important in blk["decls"]:
            loc = f"{blk['file']}:{dline}"
            vlow = value.lower()
            if important:
                important_locs.append({"property": prop, "location": loc})
            if prop.startswith("--"):
                add(cp_defined, prop, loc)
            for m in re.finditer(r"var\(\s*(--[\w\-]+)", vlow):
                add(cp_used, m.group(1), loc)
            if PHYSICAL_PROPS.fullmatch(prop):
                add(physical, prop, loc)
            if LOGICAL_PROPS.fullmatch(prop) or (prop == "text-align" and vlow in ("start", "end")):
                add(logical, prop, loc)
            for m in re.finditer(r"\b(oklch|oklab|color-mix|light-dark)\(", vlow):
                add(modern_fns, m.group(1) + "()", loc)
            for m in COLOR_TOKEN.finditer(value):
                tok = m.group(0)
                if tok.lower() in ("inherit", "initial", "unset", "none", "currentcolor"):
                    continue
                add(color_fmt, color_format(tok), loc)
                add(colors_t, tok.lower(), loc)
            if SPACING_PROPS.fullmatch(prop):
                for tok in value.split():
                    if LENGTH_TOKEN.fullmatch(tok):
                        add(spacing, tok, loc)
            elif prop == "border-radius" or prop.endswith("-radius"):
                for tok in value.split():
                    if LENGTH_TOKEN.fullmatch(tok):
                        add(radius, tok, loc)
            elif prop == "font-size":
                add(font_size, vlow, loc)
            elif prop == "line-height":
                n, unit = num(vlow)
                if n is None:
                    add(lh_other, vlow, loc)
                elif unit == "":
                    add(lh_unitless, vlow, loc)
                elif unit == "px":
                    e = lh_px.setdefault(vlow, {"count": 0, "locations": [], "block_font_sizes": []})
                    e["count"] += 1
                    if len(e["locations"]) < MAX_LOCS:
                        e["locations"].append(loc)
                        e["block_font_sizes"].append(decl_map.get("font-size"))
                else:
                    add(lh_other, vlow, loc)
            elif prop == "z-index":
                add(z_index, vlow, loc)
            elif prop == "cursor":
                add(cursor_t, vlow, loc)
            elif prop == "text-wrap":
                add(text_wrap_t, f"{vlow} on {resolved[0] if resolved else blk['selector']}", loc)
            elif prop in ("box-shadow", "text-shadow") and vlow not in ("none",):
                for part in split_top_commas(value):
                    toks, depth_p, cur = [], 0, ""
                    for chp in part:
                        if chp in "(":
                            depth_p += 1
                        elif chp == ")":
                            depth_p -= 1
                        if chp.isspace() and depth_p == 0:
                            if cur:
                                toks.append(cur)
                            cur = ""
                        else:
                            cur += chp
                    if cur:
                        toks.append(cur)
                    lengths = [t for t in toks if LENGTH_TOKEN.fullmatch(t)]
                    ctoks = [t for t in toks if COLOR_TOKEN.fullmatch(t)]
                    if len(lengths) < 2:
                        continue
                    x, _ = num(lengths[0])
                    y, _ = num(lengths[1])
                    blur = num(lengths[2])[0] if len(lengths) > 2 else 0.0
                    spread = num(lengths[3])[0] if len(lengths) > 3 else 0.0
                    shadows.append({
                        "property": prop, "raw": part.strip(),
                        "x": x, "y": y, "blur": blur, "spread": spread,
                        "angle": shadow_angle(x or 0, y or 0),
                        "inset": "inset" in [t.lower() for t in toks],
                        "color": ctoks[0].lower() if ctoks else None,
                        "location": loc,
                    })
            elif prop.startswith("border") and "radius" not in prop and prop.count("-") <= 1:
                toks = value.split()
                width = next((t for t in toks if LENGTH_TOKEN.fullmatch(t)), None)
                style = next((t for t in toks if t.lower() in (
                    "solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset", "none", "hidden")), None)
                cm = COLOR_TOKEN.search(value)
                if width or style:
                    combo = f"{width or '?'} {style or '?'} {cm.group(0).lower() if cm else '?'}"
                    add(border_combos, combo, loc)
            if prop in ("transition", "transition-duration", "animation", "animation-duration"):
                for m in DURATION_TOKEN.finditer(vlow):
                    ms = float(m.group(1)) * (1000 if m.group(2) == "s" else 1)
                    add(durations, f"{ms:g}ms", loc)
            if prop in ("transition", "transition-timing-function", "animation", "animation-timing-function"):
                for m in EASING_TOKEN.finditer(vlow):
                    add(easings, m.group(0), loc)

        # block-level: contrast pairs
        if "color" in decl_map and ("background-color" in decl_map or "background" in decl_map):
            fg_tok = decl_map["color"]
            bg_val = decl_map.get("background-color") or decl_map["background"]
            bgm = COLOR_TOKEN.search(bg_val)
            bg_tok = bgm.group(0) if bgm else None
            loc = f"{blk['file']}:{blk['line']}"
            sel = resolved[0] if resolved else blk["selector"]
            fg, bg = parse_color(fg_tok), parse_color(bg_tok) if bg_tok else None
            reason = None
            if fg is None or bg is None:
                reason = "unparseable color (var()/gradient/keyword)"
            elif fg[3] < 1 or bg[3] < 1:
                reason = "alpha channel present"
            elif "opacity" in decl_map or "filter" in decl_map:
                reason = "opacity/filter on same block"
            if reason:
                contrast_unverifiable.append({"selector": sel, "color": fg_tok, "background": bg_val,
                                              "reason": reason, "location": loc})
            else:
                contrast_checked.append({"selector": sel, "color": fg_tok, "background": bg_tok,
                                         "ratio": round(contrast_ratio(fg, bg), 2), "location": loc})

        # block-level: font-variant-numeric on numeric-ish selectors
        for rs in resolved:
            if NUMERIC_SELECTOR.search(rs):
                rec = {"selector": rs, "location": f"{blk['file']}:{blk['line']}"}
                if "font-variant-numeric" in decl_map or "font-feature-settings" in decl_map:
                    fvn_numeric_blocks.append({**rec, "declares": decl_map.get(
                        "font-variant-numeric", decl_map.get("font-feature-settings"))})
                else:
                    fvn_missing.append(rec)
                break

        # block-level: link treatment patterns (plain `a` targets, no pseudo)
        for rs in resolved:
            if re.search(r"(?<![\w.#\-\[])a(?![\w\-])", rs) and not PSEUDO_STRIP.search(rs):
                pat = tuple(sorted(
                    (p, v) for p, v in decl_map.items()
                    if p in ("color", "text-decoration", "text-decoration-line", "text-decoration-color",
                             "text-decoration-thickness", "text-underline-offset", "border-bottom",
                             "background-image", "font-weight")
                ))
                if pat:
                    e = link_patterns.setdefault(pat, {"count": 0, "example_selector": rs, "locations": []})
                    e["count"] += 1
                    if len(e["locations"]) < MAX_LOCS:
                        e["locations"].append(f"{blk['file']}:{blk['line']}")
                break

    # ── Color clustering in OKLab ──
    parsed_colors, unparsed, alpha_colors = [], [], []
    for tok, e in colors_t.items():
        lab = oklch_to_oklab(tok)
        a = 1.0
        if lab is None:
            c = parse_color(tok)
            if c is None:
                unparsed.append({"value": tok, "count": e["count"]})
                continue
            a = c[3]
            lab = srgb_to_oklab(*c[:3])
        rec = {"value": tok, "count": e["count"], "oklab": [round(v, 4) for v in lab],
               "locations": e["locations"][:MAX_LOCS]}
        (alpha_colors if a < 1 else parsed_colors).append(rec)
    parsed_colors.sort(key=lambda r: -r["count"])
    clusters = []
    for rec in parsed_colors:
        placed = False
        for cl in clusters:
            d = delta_e(rec["oklab"], cl["members"][0]["oklab"])
            if d < DELTA_E_AMBIG:
                bucket = "near-duplicate" if d < DELTA_E_NEAR else "ambiguous"
                cl["members"].append({**rec, "delta_e_to_representative": round(d, 2), "bucket": bucket})
                placed = True
                break
        if not placed:
            clusters.append({"representative": rec["value"], "members": [dict(rec, delta_e_to_representative=0.0, bucket="representative")]})
    multi = [c for c in clusters if len(c["members"]) > 1]

    # ── Affordance summary ──
    uncovered_hover = [{"selector": s, "location": e["location"]} for s, e in sorted(interactive.items()) if not e["hover"]]
    uncovered_focus = [{"selector": s, "location": e["location"]} for s, e in sorted(interactive.items()) if not e["focus"]]

    return OrderedDict([
        ("meta", OrderedDict([
            ("tool", "roll-lint inventory.py"), ("version", TOOL_VERSION),
            ("files_scanned", [rel for _, rel in files]),
            ("delta_e_thresholds", {"near_duplicate": DELTA_E_NEAR, "ambiguous": DELTA_E_AMBIG,
                                    "scale": f"OKLab euclidean x {DELTA_E_SCALE:g}"}),
            ("anomaly_max_count", ANOMALY_MAX_COUNT),
        ])),
        ("spacing", finalize(spacing)),
        ("radius", finalize(radius)),
        ("font_size", finalize(font_size)),
        ("line_height", OrderedDict([
            ("unitless", finalize(lh_unitless)),
            ("px_based", OrderedDict(sorted(lh_px.items(), key=lambda kv: -kv[1]["count"]))),
            ("other", finalize(lh_other)),
        ])),
        ("z_index", finalize(z_index)),
        ("media_breakpoints", finalize(breakpoints)),
        ("container_queries", finalize(container_queries)),
        ("media_blocks_per_file", {k: v["count"] for k, v in media_blocks_per_file.items()}),
        ("custom_properties", OrderedDict([
            ("defined", finalize(cp_defined)),
            ("used", finalize(cp_used)),
            ("defined_but_unused", sorted(set(cp_defined) - set(cp_used))),
        ])),
        ("important", {"count": len(important_locs), "instances": important_locs}),
        ("id_selectors", finalize(id_selectors)),
        ("max_nesting_depth", {"depth": max_depth, "deepest_at": depth_file}),
        ("nesting_syntax", nesting),
        ("color_formats", finalize(color_fmt)),
        ("colors", OrderedDict([
            ("total_unique", len(parsed_colors) + len(alpha_colors)),
            ("clusters_with_multiple_members", multi),
            ("distinct_singletons", len(clusters) - len(multi)),
            ("alpha_colors_excluded_from_clustering", alpha_colors),
            ("unparsed", unparsed),
        ])),
        ("shadows", OrderedDict([
            ("count", len(shadows)),
            ("angles", {a: sum(1 for s in shadows if s["angle"] == a)
                        for a in sorted({s["angle"] for s in shadows})}),
            ("entries", shadows),
        ])),
        ("border_combos", finalize(border_combos)),
        ("durations_ms", finalize(durations)),
        ("easings", finalize(easings)),
        ("cursor", finalize(cursor_t)),
        ("affordance", OrderedDict([
            ("interactive_selectors_total", len(interactive)),
            ("hover_covered", sum(1 for e in interactive.values() if e["hover"])),
            ("focus_covered", sum(1 for e in interactive.values() if e["focus"])),
            ("uncovered_hover", uncovered_hover),
            ("uncovered_focus", uncovered_focus),
            ("link_treatment_patterns", [
                {"count": e["count"], "example_selector": e["example_selector"],
                 "declarations": [f"{p}: {v}" for p, v in pat], "locations": e["locations"]}
                for pat, e in sorted(link_patterns.items(), key=lambda kv: -kv[1]["count"])
            ]),
        ])),
        ("logical_vs_physical", OrderedDict([
            ("physical", finalize(physical)),
            ("logical", finalize(logical)),
            ("mixed", bool(physical) and bool(logical)),
        ])),
        ("text_wrap", finalize(text_wrap_t)),
        ("font_variant_numeric", OrderedDict([
            ("numeric_selectors_with_it", fvn_numeric_blocks),
            ("numeric_selectors_missing_it", fvn_missing),
        ])),
        ("contrast_pairs", OrderedDict([
            ("checked_count", len(contrast_checked)),
            ("checked", contrast_checked),
            ("unverifiable", contrast_unverifiable),
            ("disclosure", f"Checked {len(contrast_checked)} color pairs declared together in source; "
                           "remaining combinations require rendered output to verify."),
        ])),
        ("modern_color_functions", finalize(modern_fns)),
    ])


def main():
    paths = sys.argv[1:] or ["."]
    result = census(paths)
    json.dump(result, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
