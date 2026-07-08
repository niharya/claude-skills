#!/usr/bin/env python3
"""
roll-lint change-table generator — snap.py

Takes the confirmed baseline (Phase 2 output / roll-lint.baseline.json)
plus the census from inventory.py and emits the Phase 4 change table:

    file:line | property | current | proposed | reason | bucket

bucket ∈ {auto, flag} per the appearance-material guard:
  auto — imperceptible corrections: grid/scale snaps, unitless line-height
         conversion, sub-threshold (ΔE < near-duplicate) color merges.
  flag — anything that visibly alters appearance: shadow-angle
         normalization, ambiguous color merges, divider consolidation,
         duration rung snaps, z-index moves, anomalies.

Usage:
    python3 snap.py <census.json> <baseline.json> [--json]

Python 3 stdlib only. ΔE thresholds are imported from inventory.py —
they live in exactly one place.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inventory import (  # noqa: E402  (single source of truth for color math)
    DELTA_E_AMBIG, DELTA_E_NEAR, ANOMALY_MAX_COUNT,
    delta_e, oklch_to_oklab, parse_color, srgb_to_oklab, px,
)


def to_lab(tok):
    lab = oklch_to_oklab(tok)
    if lab is not None:
        return lab, 1.0
    c = parse_color(tok)
    if c is None:
        return None, None
    return srgb_to_oklab(*c[:3]), c[3]


def nearest(value, candidates):
    return min(candidates, key=lambda c: abs(c - value)) if candidates else None


def rows_for_scale(census_table, allowed, base, prop_label, reason, rows, unit="px"):
    """Snap px values in a census table to an allowed set / base grid."""
    allowed = sorted(set(allowed or []))
    for raw, entry in (census_table or {}).items():
        v = px(raw)
        if v is None or v == 0:
            continue
        on_grid = v in allowed or (base and v % base == 0)
        if on_grid:
            continue
        target = nearest(v, allowed) if allowed else (round(v / base) * base if base else None)
        if target is None or target == v:
            continue
        anomaly = entry["count"] <= ANOMALY_MAX_COUNT
        for loc in entry["locations"]:
            rows.append({
                "location": loc, "property": prop_label, "current": raw,
                "proposed": f"{target:g}{unit}",
                "reason": reason + (" — anomaly (appears "
                                    f"{entry['count']}x), confirm intent" if anomaly else ""),
                "bucket": "flag" if anomaly else "auto",
            })


def build_rows(census, baseline):
    rows = []

    # ── spacing (supports optional micro tier) ──
    sg = baseline.get("spacing_grid") or {}
    micro = baseline.get("spacing_grid_micro") or {}
    values = list(sg.get("values", [])) + list(micro.get("values", []))
    bases = [b for b in (sg.get("base"), micro.get("base")) if b]
    spacing = census.get("spacing", {})
    allowed = sorted(set(values))
    for raw, entry in spacing.items():
        v = px(raw)
        if v is None or v == 0:
            continue
        if v in allowed or any(v % b == 0 for b in bases):
            continue
        target = nearest(v, allowed) if allowed else None
        if target is None:
            continue
        anomaly = entry["count"] <= ANOMALY_MAX_COUNT
        for loc in entry["locations"]:
            rows.append({"location": loc, "property": "spacing", "current": raw,
                         "proposed": f"{target:g}px",
                         "reason": "snap to spacing grid" + (f" — anomaly (appears {entry['count']}x), "
                                                             "confirm intent" if anomaly else ""),
                         "bucket": "flag" if anomaly else "auto"})

    # ── radius / type scale ──
    rows_for_scale(census.get("radius"), baseline.get("radius_set"), None,
                   "border-radius", "nearest in radius set", rows)
    rows_for_scale(census.get("font_size"), baseline.get("type_scale"), None,
                   "font-size", "snap to type scale", rows)

    # ── line-height policy ──
    if baseline.get("line_height_policy") == "unitless":
        for raw, entry in census.get("line_height", {}).get("px_based", {}).items():
            lh = px(raw)
            if lh is None:
                continue
            for i, loc in enumerate(entry["locations"]):
                fs_raw = (entry.get("block_font_sizes") or [None] * (i + 1))[i]
                fs = px(fs_raw) if fs_raw else None
                if fs:
                    rows.append({"location": loc, "property": "line-height", "current": raw,
                                 "proposed": f"{round(lh / fs, 3):g}",
                                 "reason": f"unitless ({fs_raw} base)", "bucket": "auto"})
                else:
                    rows.append({"location": loc, "property": "line-height", "current": raw,
                                 "proposed": "(unitless equivalent)",
                                 "reason": "px-based; no same-block font-size — needs context",
                                 "bucket": "flag"})

    # ── z-index tiers ──
    tiers = baseline.get("z_tiers") or []
    for raw, entry in census.get("z_index", {}).items():
        try:
            v = int(raw)
        except ValueError:
            continue
        if tiers and v not in tiers:
            t = nearest(v, tiers)
            for loc in entry["locations"]:
                rows.append({"location": loc, "property": "z-index", "current": raw,
                             "proposed": str(t), "reason": "off the z-index tier map",
                             "bucket": "flag"})

    # ── duration rungs (flag-only: motion timing is perceptible) ──
    rungs = baseline.get("duration_rungs") or []
    for raw, entry in census.get("durations_ms", {}).items():
        v = px(raw.replace("ms", "px"))
        if v is None or not rungs or v in rungs:
            continue
        for loc in entry["locations"]:
            rows.append({"location": loc, "property": "duration", "current": raw,
                         "proposed": f"{nearest(v, rungs):g}ms",
                         "reason": "falls between your duration rungs", "bucket": "flag"})

    # ── easing set ──
    eset = baseline.get("easing_set") or []
    for raw, entry in census.get("easings", {}).items():
        if eset and raw not in eset:
            for loc in entry["locations"]:
                rows.append({"location": loc, "property": "easing", "current": raw,
                             "proposed": eset[0], "reason": "outside your easing set",
                             "bucket": "flag"})

    # ── color merges (buckets pre-assigned by inventory.py) ──
    for cl in census.get("colors", {}).get("clusters_with_multiple_members", []):
        rep = cl["representative"]
        for m in cl["members"]:
            if m["bucket"] == "representative" or m["value"] == rep:
                continue
            bucket = "auto" if m["bucket"] == "near-duplicate" else "flag"
            reason = (f"near-duplicate of {rep} (dE {m['delta_e_to_representative']})"
                      if bucket == "auto"
                      else f"ambiguous vs {rep} (dE {m['delta_e_to_representative']}) — side-by-side review")
            for loc in m.get("locations", []):
                rows.append({"location": loc, "property": "color", "current": m["value"],
                             "proposed": rep, "reason": reason, "bucket": bucket})

    # ── shadow angle + elevation ladder (never auto) ──
    dominant = baseline.get("shadow_light_angle")
    ladder = baseline.get("elevation_ladder") or []
    for s in census.get("shadows", {}).get("entries", []):
        if s.get("inset"):
            continue
        if dominant and s["angle"] not in (dominant, "centered"):
            rows.append({"location": s["location"], "property": s["property"],
                         "current": s["raw"],
                         "proposed": f"mirror offsets to {dominant}",
                         "reason": f"lit by two suns — dominant light is {dominant}",
                         "bucket": "flag"})
        elif ladder and not any(abs(s.get("blur") or 0) == t.get("blur") and
                                (s.get("spread") or 0) == t.get("spread", 0) for t in ladder):
            tiers_txt = ", ".join(f"blur {t.get('blur')}/spread {t.get('spread', 0)}" for t in ladder)
            rows.append({"location": s["location"], "property": s["property"],
                         "current": s["raw"], "proposed": "(nearest elevation tier)",
                         "reason": f"bespoke shadow — fits no tier ({tiers_txt})",
                         "bucket": "flag"})

    # ── divider consolidation ──
    spec = baseline.get("divider_spec") or {}
    if spec:
        spec_txt = f"{spec.get('width')}px {spec.get('style')} {spec.get('color')}"
        spec_lab, _ = to_lab(str(spec.get("color", "")))
        for combo, entry in census.get("border_combos", {}).items():
            parts = combo.split()
            if len(parts) != 3 or "?" in parts:
                continue
            w, style, color = parts
            if combo == spec_txt or f"{w} {style} {color}" == spec_txt:
                continue
            same_shape = (px(w) == spec.get("width") and style == spec.get("style"))
            lab, alpha = to_lab(color)
            if same_shape and lab is not None and spec_lab is not None and alpha == 1.0:
                d = round(delta_e(lab, spec_lab), 2)
                if d < DELTA_E_NEAR:
                    bucket, reason = "flag", (f"divider voice near-identical to spec (dE {d}) — "
                                              "consolidation is appearance-material")
                elif d < DELTA_E_AMBIG:
                    bucket, reason = "flag", f"divider color ambiguous vs spec (dE {d}) — review side by side"
                else:
                    continue  # distinct border, not a divider drift
            elif same_shape:
                continue
            else:
                bucket, reason = "flag", "border shape differs from divider spec — confirm it is not a divider"
            for loc in entry["locations"]:
                rows.append({"location": loc, "property": "border", "current": combo,
                             "proposed": spec_txt, "reason": reason, "bucket": bucket})

    # Guard precedence: divider consolidation (flag) beats a plain color
    # merge (auto) at the same location — drop the color row so an
    # appearance-material change can't slip through as auto.
    border_locs = {r["location"] for r in rows if r["property"] == "border"}
    rows = [r for r in rows if not (r["property"] == "color" and r["location"] in border_locs)]

    rows.sort(key=lambda r: (r["location"].rsplit(":", 1)[0],
                             int(r["location"].rsplit(":", 1)[1]) if r["location"].rsplit(":", 1)[1].isdigit() else 0))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    with open(args[0]) as f:
        census = json.load(f)
    with open(args[1]) as f:
        baseline = json.load(f)
    rows = build_rows(census, baseline)
    if as_json:
        json.dump({"rows": rows,
                   "summary": {"total": len(rows),
                               "auto": sum(1 for r in rows if r["bucket"] == "auto"),
                               "flag": sum(1 for r in rows if r["bucket"] == "flag")}},
                  sys.stdout, indent=1)
        print()
        return
    if not rows:
        print("No drift against the baseline. Nothing to change.")
        return
    print("| file:line | property | current | proposed | reason | bucket |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['location']} | {r['property']} | {r['current']} | "
              f"{r['proposed']} | {r['reason']} | {r['bucket']} |")
    auto = sum(1 for r in rows if r["bucket"] == "auto")
    print(f"\n{len(rows)} proposed changes — {auto} auto-applicable, {len(rows) - auto} flagged for review.")


if __name__ == "__main__":
    main()
