#!/usr/bin/env python3
"""Fit empirical marginal sensitivities from a Black Magic backup JSON.

Reads a `black-magic-backup-YYYY-MM-DD.json` (version 2 — carries beans,
brews, AND settings.sens) and asks: what do the recorded brews say each
sensitivity-table cell should be, and does that agree with what's stored?

Method
------
For each bean, the REFERENCE recipe is its current best recipe. A TEST CUP
is any brew of that bean whose flavor variables (grind / water / contact /
agitate / pour-decay / target) differ from the reference in EXACTLY ONE
variable. Intent doesn't matter: an early default-recipe cup on a bag later
dialed elsewhere is a valid contrast — the fit only needs paired recipes
close in time.

Each cup's outcome-corrected ("implied") values use the app's own rules:
    impliedDose  = dose  * aim_ref / TDS          (dose ~ TDS, 1st order)
    impliedBloom = bloom + lastPour/30 * TimeDelta (end-flow-rate rule)
TDS aim is NOT a deviation variable: implied dose is normalized to the
bean's reference aim, so cups brewed to a different strength still pair.

The baseline for a test cup is the CONTEMPORANEOUS estimate of the
reference recipe's implied dose/bloom: reference-signature cups weighted
by 0.5^(|days from test cup| / 14) — the app's 14-day half-life, but
SYMMETRIC in time (retrospective fitting may use cups after the test;
the app's live estimator can only look back). This removes the bag-age
bloom drift that biases a naive fit against today's best values.

Empirical cell delta = mean over test cups of (implied_test - baseline),
pooled per (variable, ref_level -> test_level). Compared against the
stored table's piecewise-linear delta over the same interval.

Noise floor per cup (from CLAUDE.md): TDS sigma ~0.015 -> dose sigma
~0.21 g; contact sigma ~5 s -> bloom sigma ~lastPour/30*5 ~4 ml. Reported
uncertainty = per-cup noise (test + baseline) propagated; when n >= 3 the
sample scatter is shown too.

Usage
-----
    python3 analysis/fit_sens.py [backup.json] [--md report.md]

With no path, uses the newest black-magic-backup-*.json found in
~/Documents/Black Magic Export Restore (the phone's iCloud export folder)
or ~/Downloads.
"""

import glob
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

HALF_LIFE_DAYS = 14.0          # matches the app's EST_HALF_LIFE_DAYS
TDS_SIGMA = 0.015              # per-cup TDS noise
CONTACT_SIGMA_S = 5.0          # per-cup contact-time noise
MIN_BASELINE_NEFF = 1.5        # skip contrasts with a flimsier baseline

# flavor variables that can deviate (brew key, bean best-key, display name)
FLAVOR_VARS = [
    ("grind", "bestGrind", "grind"),
    ("water", "bestWater", "water"),
    ("contact", "bestContact", "contact"),
    ("agitate", "bestAgitate", "agitate"),
    ("decay", "bestDecay", "pour-decay"),
    ("brewTarget", "bestTarget", "target"),
]
TABLED = {"grind", "water", "contact"}  # variables with a stored sens table


def num(x, dflt=None):
    try:
        v = float(x)
        return v if math.isfinite(v) else dflt
    except (TypeError, ValueError):
        return dflt


def when_ms(brew):
    """savedAt as epoch ms; tolerates one legacy ISO-string record."""
    s = brew.get("savedAt", 0)
    if isinstance(s, str):
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000
        except ValueError:
            return 0.0
    return float(s or 0)


def last_pour_ml(target, decay_pct, contact_s):
    """Final pour of the geometric schedule (ml)."""
    r = decay_pct / 100.0
    n = max(1, int(round(contact_s / 30.0)))
    if abs(1 - r) < 1e-9:
        return target / n
    first = target * (1 - r) / (1 - r ** n)
    return first * r ** (n - 1)


def implied(brew, aim_ref):
    """(impliedDose, impliedBloom, lastPour) — either implied may be None."""
    dose, bloom, tds = num(brew.get("dose")), num(brew.get("bloom")), num(brew.get("tds"))
    tadj = num(brew.get("timeAdj"), 0.0)
    target = num(brew.get("brewTarget"), 350)
    decay = num(brew.get("decay"), 90)
    contact = num(brew.get("contact"), 270)
    lp = last_pour_ml(target, decay, contact)
    i_dose = dose * aim_ref / tds if (dose and tds) else None
    i_bloom = bloom + lp / 30.0 * tadj if bloom is not None else None
    return i_dose, i_bloom, lp


def ref_recipe(bean, default_recipe):
    """The bean's best recipe with blanks filled from the Tools default."""
    out = {}
    for bk, bestk, _ in FLAVOR_VARS:
        out[bk] = num(bean.get(bestk), num(default_recipe.get(bk)))
    return out


def deviations(brew, ref):
    """[(var_key, ref_level, brew_level)] where the brew differs from ref."""
    devs = []
    for bk, _, _ in FLAVOR_VARS:
        v = num(brew.get(bk))
        rv = ref.get(bk)
        if v is not None and rv is not None and abs(v - rv) > 1e-9:
            devs.append((bk, rv, v))
    return devs


def decayed_baseline(ref_cups, t_ms, aim_ref):
    """Symmetric 14d-half-life weighted mean of implied dose/bloom at t.

    Returns (dose_mean, bloom_mean, n_eff_dose, n_eff_bloom, lastPour)."""
    wd, wsum_d, wb, wsum_b, w2d, w2b, lp_any = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None
    for cup in ref_cups:
        dt_days = abs(t_ms - when_ms(cup)) / 86400000.0
        w = 0.5 ** (dt_days / HALF_LIFE_DAYS)
        i_dose, i_bloom, lp = implied(cup, aim_ref)
        lp_any = lp
        if i_dose is not None:
            wd += w * i_dose; wsum_d += w; w2d += w * w
        if i_bloom is not None:
            wb += w * i_bloom; wsum_b += w; w2b += w * w
    dose_mean = wd / wsum_d if wsum_d else None
    bloom_mean = wb / wsum_b if wsum_b else None
    neff_d = wsum_d ** 2 / w2d if w2d else 0.0
    neff_b = wsum_b ** 2 / w2b if w2b else 0.0
    return dose_mean, bloom_mean, neff_d, neff_b, lp_any


def table_interp(table, x):
    """Piecewise-linear value of a stored sens row at level x, clamped."""
    levels = table["levels"]

    def interp(vals):
        if x <= levels[0]:
            return vals[0]
        if x >= levels[-1]:
            return vals[-1]
        for i in range(len(levels) - 1):
            if levels[i] <= x <= levels[i + 1]:
                f = (x - levels[i]) / (levels[i + 1] - levels[i])
                return vals[i] + f * (vals[i + 1] - vals[i])
    return interp(table["dose"]), interp(table["bloom"])


def stored_delta(sens, var, frm, to):
    """Stored table's (Δdose, Δbloom) over frm->to, or (None, None)."""
    table = sens.get(var)
    if not table:
        return None, None
    d0, b0 = table_interp(table, frm)
    d1, b1 = table_interp(table, to)
    return d1 - d0, b1 - b0


def fmt(v, unit="", digits=2, sign=True):
    if v is None:
        return "—"
    s = f"{v:+.{digits}f}" if sign else f"{v:.{digits}f}"
    return s + unit


def find_backup():
    for folder in (os.path.expanduser("~/Documents/Black Magic Export Restore"),
                   os.path.expanduser("~/Downloads")):
        hits = sorted(glob.glob(os.path.join(folder, "black-magic-backup-*.json")))
        if hits:
            return hits[-1]
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    md_out = None
    if "--md" in sys.argv:
        md_out = sys.argv[sys.argv.index("--md") + 1]
    path = args[0] if args else find_backup()
    if not path or not os.path.exists(path):
        sys.exit("no backup file found — pass a path to black-magic-backup-*.json")

    data = json.load(open(path))
    beans = {b["id"]: b for b in data.get("beans", [])}
    brews = data.get("brews", [])
    settings = data.get("settings", {})
    sens = settings.get("sens", {})
    default_recipe = settings.get("defaultRecipe", {})

    lines = []
    say = lines.append
    say(f"# Sensitivity fit — {os.path.basename(path)}")
    say(f"beans {len(beans)} · brews {len(brews)} · half-life {HALF_LIFE_DAYS:g}d (symmetric)")
    say("")

    # ---- classify every brew against its bean's reference recipe ----------
    by_bean_ref = defaultdict(list)      # reference-signature cups per bean
    tests = []                           # (bean, brew, var, frm, to)
    skipped = defaultdict(int)
    for brew in brews:
        # v11 rating scale: 0 = ignore (keep the record, drop the datapoint).
        # Pre-v11 backups used 1–5 and never 0, so this is safe on old files.
        if str(brew.get("brewRating")) == "0":
            skipped["rated 0 (ignore)"] += 1
            continue
        bean = beans.get(brew.get("beanId"))
        if not bean:
            skipped["no live bean"] += 1
            continue
        ref = ref_recipe(bean, default_recipe)
        devs = deviations(brew, ref)
        if not devs:
            by_bean_ref[bean["id"]].append(brew)
        elif len(devs) == 1:
            tests.append((bean, brew, *devs[0]))
        else:
            skipped[f"{len(devs)}-variable deviation"] += 1

    # ---- fit each test cup against its contemporaneous baseline -----------
    cells = defaultdict(list)  # (var, frm, to) -> contrast dicts
    for bean, brew, var, frm, to in tests:
        aim_ref = num(bean.get("tdsAim"), num(sens.get("tdsTarget"), 1.72))
        ref_cups = by_bean_ref.get(bean["id"], [])
        t = when_ms(brew)
        base_d, base_b, neff_d, neff_b, base_lp = decayed_baseline(ref_cups, t, aim_ref)
        i_dose, i_bloom, lp = implied(brew, aim_ref)

        c = {"bean": bean.get("name", "?"), "date": datetime.fromtimestamp(t / 1000).strftime("%m/%d"),
             "rating": brew.get("brewRating"), "d_dose": None, "d_bloom": None,
             "sig_dose": None, "sig_bloom": None}
        dose_sigma = TDS_SIGMA / 1.70 * 24.0   # ~0.21 g per cup
        bloom_sigma = lp / 30.0 * CONTACT_SIGMA_S
        if i_dose is not None and base_d is not None and neff_d >= MIN_BASELINE_NEFF:
            c["d_dose"] = i_dose - base_d
            c["sig_dose"] = dose_sigma * math.sqrt(1 + 1 / neff_d)
        if i_bloom is not None and base_b is not None and neff_b >= MIN_BASELINE_NEFF:
            c["d_bloom"] = i_bloom - base_b
            c["sig_bloom"] = bloom_sigma * math.sqrt(1 + 1 / neff_b)
        if c["d_dose"] is None and c["d_bloom"] is None:
            skipped["baseline too thin"] += 1
            continue
        cells[(var, frm, to)].append(c)

    # ---- report per cell ---------------------------------------------------
    say("## Fitted cells (empirical vs stored)")
    say("")
    say("| variable | interval | n | Δdose fit | Δdose stored | Δbloom fit | Δbloom stored | beans |")
    say("|---|---|---|---|---|---|---|---|")

    def pooled(rows, key, sig_key):
        vals = [(r[key], r[sig_key]) for r in rows if r[key] is not None]
        if not vals:
            return None, None, 0
        wts = [1 / s ** 2 for _, s in vals]
        mean = sum(v * w for (v, _), w in zip(vals, wts)) / sum(wts)
        sem = math.sqrt(1 / sum(wts))
        if len(vals) >= 3:
            m0 = sum(v for v, _ in vals) / len(vals)
            scatter = math.sqrt(sum((v - m0) ** 2 for v, _ in vals) / (len(vals) - 1) / len(vals))
            sem = max(sem, scatter)
        return mean, sem, len(vals)

    detail = []
    for (var, frm, to), rows in sorted(cells.items()):
        dmean, dsem, dn = pooled(rows, "d_dose", "sig_dose")
        bmean, bsem, bn = pooled(rows, "d_bloom", "sig_bloom")
        sd, sb = stored_delta(sens, var, frm, to)
        beans_in = "·".join(sorted({r["bean"].split()[0] for r in rows}))
        dose_cell = f"{fmt(dmean, ' g')} ± {dsem:.2f}" if dmean is not None else "—"
        bloom_cell = f"{fmt(bmean, ' ml', 1)} ± {bsem:.1f}" if bmean is not None else "—"
        say(f"| {var} | {frm:g} → {to:g} | {len(rows)} | {dose_cell} | {fmt(sd, ' g')} "
            f"| {bloom_cell} | {fmt(sb, ' ml', 0)} | {beans_in} |")
        for r in rows:
            detail.append(f"  {var} {frm:g}→{to:g}  {r['date']} {r['bean']} (★{r['rating']}): "
                          f"Δdose {fmt(r['d_dose'], ' g')}  Δbloom {fmt(r['d_bloom'], ' ml', 1)}")
    say("")
    say("Fit = implied(test cup) − contemporaneous decayed baseline of the bean's")
    say("reference cohort. Stored = piecewise-linear delta of the Tools table over")
    say("the same interval. Variables without a table (agitate/decay/target) show —.")
    say("")

    say("## Per-cup contrasts")
    say("```")
    lines.extend(detail if detail else ["  (none)"])
    say("```")
    say("")

    # ---- data gaps ---------------------------------------------------------
    say("## Data support per stored table level")
    say("")
    support = defaultdict(float)  # (var, level) -> n of test cups at that level
    for (var, frm, to), rows in cells.items():
        support[(var, to)] += len(rows)
    for var in ("grind", "water", "contact"):
        table = sens.get(var)
        if not table:
            continue
        parts = []
        for lv in table["levels"]:
            n = support.get((var, lv), 0)
            anchored = any(abs(num(ref_recipe(b, default_recipe).get(var), -1) - lv) < 1e-9
                           for b in beans.values())
            tag = "anchor" if anchored and n == 0 else f"n={n:g}"
            parts.append(f"{lv:g}:{tag}")
        say(f"- **{var}**: " + " · ".join(parts))
    say("")
    gaps = [(var, lv) for var in ("grind", "water", "contact")
            for lv in sens.get(var, {}).get("levels", [])
            if support.get((var, lv), 0) == 0
            and not any(abs(num(ref_recipe(b, default_recipe).get(var), -1) - lv) < 1e-9
                        for b in beans.values())]
    if gaps:
        say("Unconstrained levels (no test cups, not a current anchor): "
            + ", ".join(f"{v} {lv:g}" for v, lv in gaps))
    say("")

    # ---- roast-age drift (within reference cohorts) ------------------------
    say("## Roast-age drift (reference cohorts, within-bean OLS)")
    say("")
    say("| bean | age span (d) | n | bloom ml/wk | dose g/wk |")
    say("|---|---|---|---|---|")
    pooled_drift = {"bloom": [], "dose": []}
    for bean in beans.values():
        rd = bean.get("roastDate")
        if not rd:
            continue
        try:
            roast_ms = datetime.fromisoformat(rd).timestamp() * 1000
        except ValueError:
            continue
        aim_ref = num(bean.get("tdsAim"), num(sens.get("tdsTarget"), 1.72))
        pts = []  # (age_days, implied_dose, implied_bloom)
        for cup in by_bean_ref.get(bean["id"], []):
            i_dose, i_bloom, _ = implied(cup, aim_ref)
            pts.append(((when_ms(cup) - roast_ms) / 86400000.0, i_dose, i_bloom))
        row = {"bloom": "—", "dose": "—"}
        span = "—"

        def ols(xy):
            n = len(xy)
            if n < 3:
                return None
            mx = sum(x for x, _ in xy) / n
            my = sum(y for _, y in xy) / n
            sxx = sum((x - mx) ** 2 for x, _ in xy)
            if sxx < 1e-9:
                return None
            slope = sum((x - mx) * (y - my) for x, y in xy) / sxx
            resid = [y - (my + slope * (x - mx)) for x, y in xy]
            se = math.sqrt(sum(r * r for r in resid) / (n - 2) / sxx)
            return slope, se, n
        for key, idx, digits in (("bloom", 2, 2), ("dose", 1, 3)):
            xy = [(a, p) for a, d, b in pts for p in [b if key == "bloom" else d] if p is not None]
            fit = ols(xy)
            if fit:
                slope, se, n = fit
                pooled_drift[key].append((slope, se))
                row[key] = f"{slope * 7:+.{digits}f} ± {se * 7:.{digits}f}"
        if pts:
            ages = [a for a, _, _ in pts]
            span = f"{min(ages):.0f}–{max(ages):.0f}"
        say(f"| {bean.get('name', '?')} | {span} | {len(pts)} | {row['bloom']} | {row['dose']} |")
    for key, unit, digits in (("bloom", "ml/wk", 2), ("dose", "g/wk", 3)):
        fits = pooled_drift[key]
        if fits:
            w = [1 / se ** 2 for _, se in fits]
            m = sum(s * wi for (s, _), wi in zip(fits, w)) / sum(w)
            se = math.sqrt(1 / sum(w))
            say(f"| **pooled {key}** | | | **{m * 7:+.{digits}f} ± {se * 7:.{digits}f} {unit}** "
                f"(z = {m / se:+.1f}) | |" if key == "bloom" else
                f"| **pooled {key}** | | | | **{m * 7:+.{digits}f} ± {se * 7:.{digits}f} {unit}** (z = {m / se:+.1f}) |")
    say("")
    say("Within a bag, roast age / days-open / calendar time are collinear — this")
    say("slope is 'the bag's drift per week', whatever the mechanism. Bags observed")
    say("at different age spans hint at curvature (fast early, flattening later).")
    say("")

    if skipped:
        say("Skipped brews: " + ", ".join(f"{k} ×{n}" for k, n in sorted(skipped.items())))
        say("")

    report = "\n".join(lines)
    print(report)
    if md_out:
        with open(md_out, "w") as f:
            f.write(report + "\n")
        print(f"\n[written to {md_out}]")


if __name__ == "__main__":
    main()
