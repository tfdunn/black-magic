# Black Magic — Pour Over Coffee Timer

## What this is
A single-page mobile web app for logging and timing pour over coffee brews. Designed to fit an iPhone screen (390px wide). No frameworks, no dependencies — pure HTML/CSS/JS in `index.html`.

The original design mockup is `Black Magic iPhone Mockup.pdf` (Adobe Illustrator). `timer-alternatives.html` is a scratchpad from phase 1 exploring three clock designs; it can be ignored going forward.

## File structure
```
index.html              — the entire app (HTML + CSS + JS)
manifest.webmanifest    — PWA manifest (relative paths; scope "./")
sw.js                   — service worker (network-first, caches app shell)
icon-180/192/512.png    — PWA / home-screen icons
CLAUDE.md               — this file
Black Magic iPhone Mockup.pdf   — original design reference
timer-alternatives.html — phase 1 exploration, not part of the app
```

## Deployment (GitHub Pages)
Live at **https://tfdunn.github.io/black-magic/** — served from the `main` branch
root of the public repo **https://github.com/tfdunn/black-magic** (owner `tfdunn`).
This is the permanent home; the old cloudflared tunnel is retired.

All PWA paths are **relative** (`./`, `manifest.webmanifest`, `sw.js`, `icon-*.png`),
so the app works under the `/black-magic/` subpath with no path rewrites — keep it
that way (never hard-code a leading `/` in asset/manifest/SW references).

**Deploy loop:** branch → edit → verify → merge to `main` → Pages auto-rebuilds
(~1–2 min). Bump the `CACHE` version in `sw.js` when changing cached assets so
clients pick up the update. `gh` CLI lives at `~/.local/bin/gh` (logged in as
`tfdunn`). `.claude/` is gitignored.

## App layout (top to bottom)
1. **Header** — "Black Magic" title, live date/time, `history` button (top-right)
2. **Brew name** — editable text input (defaults to "148 Passenger Isidro Geisha")
3. **Stats grid** — 2 rows × 4 columns of editable fields
4. **Timer circle** — analog clock face with floating second hand
5. **Start / Refresh buttons**
6. **Bottom row** — TIME +/−, TDS, Rating
7. **Notes** — free-text input
8. **Save brew** — black pill button; snapshots the form to history

## Stats grid fields and their input types

| Field | Type | Constraints |
|---|---|---|
| Dose | number input | 0–99, step 0.1, one decimal |
| Grind | number input | 0–99, step 0.1, one decimal |
| Agitate | select | Zero / Min / Low / Mid / High |
| Contact | select | 30-second intervals, 1:00–10:00 |
| Water F° | number input | 0–999, integer |
| Bloom | number input | 0–999, integer, shows "ml" suffix |
| Decay | number input | 0–100, integer, shows "%" suffix |
| Brew Target | number input | 0–9999, integer, shows "ml" suffix |

Bottom row: TIME +/− (read-only, set by stop button), TDS (number, 2dp), Rating (integer 0–100).

## Timer logic

### Clock face
- Fixed 4-minute scope (CLOCK_SCOPE = 240 s), regardless of Contact time
- 8 tick marks: 4 light (30-second) + 4 heavier (1-minute)
- No numeric labels on ticks
- Outer arc fills over 4 minutes; wraps to a new cycle if brew is longer
- Second hand sweeps once per 30-second pour cycle (one revolution = one pour interval)

### Pour schedule
Geometric decay series. Individual pour amounts: x, x·r, x·r², … for n cycles, where:
- n = Contact / 30 (number of 30-second cycles)
- r = Decay / 100
- x = BrewTarget · (1−r) / (1−rⁿ)   [special case: equal distribution when r≈1]

Cumulative target at cycle k: x · (1−r^(k+1)) / (1−r)

The center of the clock shows the **cumulative** pour target for the current cycle (step function — jumps at each 30s boundary), not a running interpolation.

Recalculated automatically when Contact, Decay, or Brew Target changes. Timer also resets on any of those changes.

### Start / Stop / Refresh
- **Start**: 3-second audio countdown (rising tones G4→A4→C5, then G5 "GO"), then timer runs
- **Stop**: freezes timer, writes `round(elapsed − TOTAL) − 2` to TIME +/− (−2 is a 2-second reaction-time correction)
- **Refresh**: recalculates schedule from current field values and resets timer to zero
- Pressing Start during countdown cancels it

### Sound (Web Audio API, no files)
- Countdown: 392 Hz, 440 Hz, 523 Hz (one per second)
- GO tone: 784 Hz, 0.4 s
- 30-second brew marks: 880 Hz, 0.18 s

## Key CSS patterns
- `.value-input` — shared style for all editable stat inputs and selects; hides spinners, centers text (`text-align-last: center` needed for `<select>`)
- `.unit-wrap` / `.unit-label` — flex wrapper for fields with a unit suffix (%, ml); unit is 10px, #aaa
- `.unit-wrap .value-input.wide` — 4ch width for Brew Target (4-digit values)

## Brew history (Phase 2 — implemented)

Saved brews persist in `localStorage` under the key `blackmagic.brews` — a JSON
array of records. No backend; data is per-browser.

### Record shape
Every field is captured: `id`, `savedAt` (ISO), `brewName`, `dose`, `grind`,
`agitate`/`agitateText`, `contact`/`contactText`, `water`, `bloom`, `decay`,
`brewTarget`, `timeAdj`, `tds`, `rating`, `notes`. The `*Text` fields store the
select's display label (e.g. "Low", "4:30") so history renders without re-mapping.

`id` comes from `nextId()` — `max(Date.now(), maxExistingId + 1)` — guaranteeing
strictly increasing, unique ids even for saves within the same millisecond (so
delete-by-id never removes the wrong record).

### History panel
- Opened via the header `history` button; slide-in overlay (`.history-overlay` /
  `.history-panel`), closed by ×, by tapping the dim backdrop, or after a load.
- Cards listed newest-first (sort by `id` desc). Each shows name, date, and a
  compact `dose · TDS · ★rating` line.
- Tapping a card toggles an expanded detail grid (taps on the action buttons are
  ignored so they don't also toggle).
- **load** writes the record back into the live form via `applyRecord()`, then
  recalculates the schedule and resets the timer, and closes the panel.
- **delete** removes that one record (confirm() guarded).

## Phase 3 ideas (not yet started)
- Chart TDS or Rating over time
- Compare brews side by side
- Export / import history (JSON) so it survives a browser change

## Design conventions
- White background, black text, no accent colors
- Font: system stack (`-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif`)
- Dividers: 1px `#e8e8e8`
- Stat labels: 9px, uppercase, #888
- Stat values: 16px, bold, #000
- Keep it a single HTML file until phase 2 complexity justifies splitting
