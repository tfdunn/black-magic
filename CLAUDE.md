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
1. **Header** — `Bean` (top-left), "Black Magic" title + live date/time, `History`
   (top-right). `Bean`/`History` are amber text buttons.
2. **Coffee selector** — full-width `Select a coffee ⌄` row (taps to pick a saved bean)
3. **Stats grid** — 2 rows × 4 columns of editable fields
4. **Timer dial** — analog clock face (amber sweep hand). Center stacks the pour
   target over a **▶/⏸/↺ status symbol**; **tapping the dial** cycles start → stop →
   reset (no visible button).
5. **Results row** — 4 cells aligned under the recipe grid: **Timer** (live elapsed,
   black) · **Time +/−** · **TDS** · **Rating** (last three editable, amber)
6. **Notes** — auto-growing textarea
7. **Save/New button** — black pill that toggles **save brew ⇄ new brew**

## Stats grid fields and their input types

| Field | Type | Constraints |
|---|---|---|
| Dose | number input | 0–99, step 0.1; shows "g" suffix |
| Grind | number input | 0–99, step 0.1; shows a small grey "#" suffix |
| Agitate | select (overlay) | 0–4 → none/min/mid/low/high; renders as bold number + small grey word (see below) |
| Contact | select | 30-second intervals, 1:00–10:00 |
| Water | number input | 0–999, integer; shows "°F" suffix (label is "Water") |
| Bloom | number input | 0–999, integer, shows "ml" suffix |
| Decay | number input | 0–100, integer, shows "%" suffix |
| Target | number input | 0–9999, integer, shows "ml" suffix (label is "Target") |

Agitate keeps a real native `<select>` (so iOS shows its picker) but the select is
transparent and layered over a `#agitate-num` (bold) + `#agitate-word` (small grey)
display via `.select-wrap` / `.select-overlay`; `syncAgitate()` keeps them in step.

Results row (4 cells, aligned under the recipe grid): Timer (live elapsed `m:ss`,
read-only, black), TIME +/− (editable; auto-set by stop, hand-editable for brews
logged without the timer), TDS (number, 2dp), Rating (integer 0–100). TIME +/−, TDS,
and Rating render in amber; Timer stays black.

## Timer logic

### Clock face
- Fixed 4-minute scope (CLOCK_SCOPE = 240 s), regardless of Contact time
- 8 tick marks (30-second), 1-minute ones heavier; the 12-o'clock mark is a bold
  `--ink` anchor (cycle start/end). No numeric labels.
- Outer arc fills over 4 minutes; wraps to a new cycle if brew is longer
- Amber sweep hand sweeps once per 30-second pour cycle (floats in the outer ring,
  so the center stays clear)
- **Progress arc colour** (set per-frame in `render()`): dark grey `#555` for the
  first 4 minutes, **black** `#000` once past 4:00. The sweep hand is amber; amber is
  otherwise used only on Bean/History/TDS/Rating/TIME.
- Center stacks the **cumulative pour target in ml** over the **▶/⏸/↺ status symbol**
  (not elapsed seconds). Live elapsed time shows as **Timer** in the results row below.

### Pour schedule
Geometric decay series. Individual pour amounts: x, x·r, x·r², … for n cycles, where:
- n = Contact / 30 (number of 30-second cycles)
- r = Decay / 100
- x = BrewTarget · (1−r) / (1−rⁿ)   [special case: equal distribution when r≈1]

Cumulative target at cycle k: x · (1−r^(k+1)) / (1−r)

The center of the clock shows the **cumulative** pour target for the current cycle (step function — jumps at each 30s boundary), not a running interpolation.

Recalculated automatically when Contact, Decay, or Brew Target changes. Timer also resets on any of those changes.

### Timer — tap the dial (cycles start → stop → reset)
No visible button: the whole clock dial is the tap target (click listener on
`.timer-circle-wrap`). The `#t-sym` glyph under the pour target shows the current
action — ▶ start · ⏸ stop · ↺ reset.
- **start** (▶): 3-second audio countdown (rising tones G4→A4→C5, then G5 "GO"), then runs
- **stop** (⏸): freezes timer, writes `round(elapsed − TOTAL) − 2` to TIME +/−
  (−2 reaction-time correction). Symbol becomes ↺.
- **reset** (↺): zeroes the clock back to start. **Does NOT touch TIME +/−** — only
  "new brew" clears that, so an evaluated brew isn't lost to an accidental reset.
- The timer **counts up past TOTAL** (no cap) so long brews record a positive TIME +/−.
- Pressing during the countdown cancels it (and its queued tones).
- `#t-timer` shows total elapsed `m:ss` (live), as the first cell of the results row;
  it counts past TOTAL. (The earlier in-dial POUR countdown was removed.)

### Save / New button (single pill: save brew ⇄ new brew)
- **save brew**: snapshots the form to history and changes nothing on screen; flips
  the button to **new brew**.
- **new brew**: resets the timer + TIME/TDS/Rating for the next cup, leaving the
  coffee + recipe unchanged (for brewing many cups in a row). Flips back to **save brew**.

### Sound (Web Audio API, no files)
- Countdown: 392 Hz, 440 Hz, 523 Hz (one per second); GO tone 784 Hz; 30-s marks 880 Hz.
- All countdown tones are **scheduled on the AudioContext clock at the start gesture**
  (via `tone(freq, dur, when, vol)`), not fired from `setTimeout`, for reliable iOS
  playback. `getAudio()` resumes a suspended/interrupted context and recreates a
  closed one. **Caveat:** the iOS hardware Ring/Silent switch can still mute Web
  Audio — no web API overrides it (a silent-`<audio>` unmute hack is a possible
  future add).

## Key CSS patterns
- `.value-input` — shared style for editable stat inputs/selects; hides spinners,
  centers text (`text-align-last: center` for `<select>`). 21px/600 tabular.
- `.unit-wrap` / `.unit-label` — flex wrapper for a unit affix (11px `--tertiary`).
  `.unit-pre` puts the affix *before* the value (the Grind "#").
- `.unit-wrap .value-input.wide` — 4ch width for Target (4-digit values)
- `.select-wrap` / `.select-overlay` — transparent native `<select>` over a
  formatted number+word display (Agitate)

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
Refined via a Claude Design pass; tokens live in `:root` in `index.html`.
White background, black text, with **one** restrained accent.

- **Tokens:** `--ink #0B0B0C` · `--secondary rgba(60,60,67,.6)` ·
  `--tertiary rgba(60,60,67,.34)` · `--hairline rgba(60,60,67,.13)` ·
  `--accent #9A5A2B` (warm amber). **Amber is used on Bean/History (nav), the
  TIME +/− / TDS / Rating values, and the clock's sweep hand** — not on the progress
  arc, the status symbol, or the save button.
- Font: `var(--font)` system stack; all numerals `font-variant-numeric: tabular-nums`.
- Type scale: title 23/700, big pour number 54/700, metric value 21/600, selector &
  save 17, nav 16, metric label 10/600 uppercase (0.07em), unit 11/500, POUR/TIMER 15.
- Status symbols (▶/⏸/↺) are inline SVGs coloured grey via `currentColor` — never
  emoji glyphs (those box-render on iOS).
- Grids use the hairline-gap trick: `gap: 0.5px; background: var(--hairline)` with
  white cells, so gaps render as 0.5px dividers.
- Save button uses full-radius (999px); the timer has no button (tap the dial).
- **Fits the screen:** `.app` is `width:100%` (max 440px) × `min-height:100dvh` with
  `env(safe-area-inset-*)` padding, tuned so the brew screen fits an iPhone 17 Pro
  (402×874) without scrolling. Dial is 235px; shrink the pour number with it to keep
  3-digit targets clear of the sweep hand.
- Keep it a single HTML file until complexity justifies splitting.
