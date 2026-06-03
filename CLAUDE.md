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

**Auto-update:** the SW is network-first with `{cache:'no-store'}` (always fetches
fresh when online; cache is offline fallback only) and `skipWaiting()` +
`clients.claim()`. `index.html` calls `registration.update()` on load and on every
`visibilitychange`, and reloads once on `controllerchange` — so reopening the
installed PWA (while online) pulls the latest version on its own. A stuck old
install can still be reset by removing the home-screen icon and re-adding it
(⚠️ that may clear the PWA's `localStorage` — export brews/beans first).

## App layout (top to bottom)
1. **Header** — Brew screen: `Bean` (top-left), title + live date/time, `History`
   (top-right). Bean screen: `Brew` (top-left), title, **no History button**
   (removed — the Bean tab *is* the bean list). `Bean`/`Brew`/`History` are amber.
2. **Coffee selector** — full-width `Select a coffee ⌄` row. Tapping it opens the
   **Bean tab** (same as the `Bean` button); you pick a coffee by tapping it in the list.
3. **Stats grid** — 2 rows × 4 columns of editable fields
4. **Timer dial** — analog clock face (amber sweep hand + thick 4-min progress ring).
   Center stacks the live **Timer** (grey) over the pour-target number, with a small
   grey **↺ reset hint** below. **Hold the dial 2s to reset** (no tap action).
5. **Results row** — 4 cells aligned under the recipe grid: **Time +/−** · **TDS** ·
   **Brew★** · **Bean★** (all editable; render in amber)
6. **Notes** — auto-growing textarea
7. **Action button** — single black pill: **tap** = start / stop; **hold 2s** = save
   brew (then clears for the next cup). Quick taps never save.

## Fields & number entry (tap-to-edit)

Every editable field on the brew screen (recipe grid + results row) is a **tap-to-edit**
cell: the visible value is a `.field` button; tapping it opens one shared bottom-sheet
editor (`#ed-bg`) with a big −/+ stepper (hold-to-repeat), preset chips, and a
"type a value" escape for arbitrary entry. No on-screen keyboard in normal use, and the
stepper makes **TIME +/− negatives** possible (the iOS numeric keypad has no minus).

Under the hood each field keeps a **hidden `<input>`/`<select>`** as its data store (ids
unchanged: `dose grind agitate contact water bloom decay brew-target time-val tds
brew-rating bean-rating`) so the pour-schedule recalc, history, CSV, and ratings logic
read/write `.value` exactly as before. The editor writes the store, dispatches `change`
(firing recalc / bean-persist), then `renderField()` repaints the button. `FX` holds each
field's config; choice fields keep a hidden `<select>` so `selectedOptions[0].text` still
works for history.

| Field | Step | Presets | Notes |
|---|---|---|---|
| Dose | 0.1 | 23 / 24 / 25 / 72 | "g" |
| Grind | 0.5 | 7 / 8 / 9 / 10 | "#" |
| Agitate | 1 | 0–4 (none/min/low/mid/high) | choice |
| Contact | 30s | 4:00 / 4:30 / 5:00 / 6:30 (210/240/270/300/390) | m:ss |
| Water | 1 | 196 / 200 / 204 / 208 / 212 | "°F" |
| Bloom | 2 | 80 / 100 / 120 / 300 | "ml" |
| Decay | 1 | 85 / 90 / 95 / 100 | "%" |
| Target | 10 | 350 / 1050 | "ml" |
| Time +/− | 1 | −25 / −5 / 5 / 25 | signed; auto-set by stop |
| TDS | 0.01 | 1.70–1.74 | 2 dp |
| Brew★ | 1 | 1 1st / 2 dial / 3 test / 4 good / 5 best | per-brew; blanks on save+reset |
| Bean★ | 1 | 85 / 90 / 92 / 95 / 98 | **numeric 0–100** score; stored on the bean (below) |

TIME +/−, TDS, Brew★, Bean★ render in amber; a blank field shows "–". Live elapsed shows
as **Timer** (grey) inside the dial, not in the results row. All editor preset chips sit on
**one row** (`.ed-chips` is `nowrap`).

**Bean★** is a **numeric score (0–100)** stored *on the selected bean* (`bean.rating`), not
the brew: it prefills from the chosen coffee's saved rating and editing it overwrites that
bean's rating (`persistBeanRating()`); not cleared by save/reset. (Earlier it was a 1–5
word rating — switched to a number for finer future grading; old 1–5 values display as-is.)

**Notes = two soft-labeled fields** (`#notes-brew`, `#notes-bean`) styled as one block.
They **share a fixed ~4-line budget** (`growNotes()`, `NOTES_BUDGET_LINES`): each field
takes only the lines its content needs and the short one yields its slack to the long one
(exploits the Brew↔Bean anti-correlation — long Brew early, long Bean late). Only when
*both* exceed their half does either scroll. Total footprint is constant regardless of the
split, so the page stays one screen and the action button is never pushed off. Behaviour:
- **Brew** note is per-cup — saved to the brew record (`brewNote`), blanks on save/reset.
- **Bean** note persists on the selected bean as `bean.tastingNote` — prefills from the
  bean, and on a fresh save **overwrites** it (`persistBeanNote()`); the evolving verdict.
- **Guard:** a brew loaded from History sets `loadedFromHistory=true`; re-saving it then
  does **not** run `persistBeanRating()`/`persistBeanNote()`, so editing an old brew can't
  clobber the bean's current note/rating.
- CSV: brews `Comments` = brew note; beans `Comments` = tastingNote (+ any legacy myNotes).

**Draft autosave:** edits are stashed to `localStorage['blackmagic.draft']` (debounced) so
an unsaved brew survives a close/reopen — `loadDraft()` restores it on launch (recipe +
ratings + both notes + selected coffee, then recomputes the schedule); `clearDraft()` runs
on save and reset.

**Portrait lock:** manifest `orientation:"portrait"` (installed PWA) plus a CSS
counter-rotate fallback (landscape phone → rotate app −90°) so the brew screen always
renders portrait regardless of device rotation.

## Timer logic

### Clock face
- Fixed 4-minute scope (CLOCK_SCOPE = 240 s), regardless of Contact time
- 8 thin tick marks (30-second), 1-minute ones a touch heavier; 12-o'clock is a bold
  anchor. No numeric labels. (Kept thin — the prominent ring is the progress arc.)
- Thick outer **progress ring** fills over 4 minutes (arc stroke 3.2, track 2.6);
  wraps to a new cycle if the brew runs longer.
- **Progress arc colour** (set per-frame in `render()`): dark grey `#555` for the
  first 4 minutes, **black** `#000` once past 4:00.
- Amber sweep hand (stroke 3.2) sweeps once per 30-second pour cycle, floating in the
  outer ring so the center stays clear. Amber is otherwise used only on Bean/History
  and the TIME/TDS/Brew★/Bean★ values.
- Center stacks the live **Timer** (grey `m:ss`) over the **cumulative pour target in
  ml** (not elapsed seconds), with a small grey **↺ hint** below (hold the dial 2s to
  reset). No ▶/⏸ symbol — the bottom button's label carries the action.

### Pour schedule
Geometric decay series. Individual pour amounts: x, x·r, x·r², … for n cycles, where:
- n = Contact / 30 (number of 30-second cycles)
- r = Decay / 100
- x = BrewTarget · (1−r) / (1−rⁿ)   [special case: equal distribution when r≈1]

Cumulative target at cycle k: x · (1−r^(k+1)) / (1−r)

The center of the clock shows the **cumulative** pour target for the current cycle (step function — jumps at each 30s boundary), not a running interpolation.

Recalculated automatically when Contact, Decay, or Brew Target changes. Timer also resets on any of those changes.

### Timer + actions (one button + tap-vs-hold)
Quick taps drive the transient timer; a deliberate 2-second **hold** guards the two
data actions (save, reset), so during the ~1-hour stop→save window no single accidental
tap can save early or wipe the brew. `bindPressable(el, {onTap, onHold, holdWhen})`
distinguishes them; a hold shows a fill that **release-cancels**, and only a completed
hold fires `onHold`.

**Bottom button** (`#btn-save`; label `#btn-label` driven by `updateButtonLabel()`):
- idle → label **start**, tap → 3-second audio countdown (G4→A4→C5, G5 "GO") → runs.
- running → label **stop**, tap → freezes + writes `round(elapsed − TOTAL) − 2` to
  TIME +/− (−2 reaction-time). The timer **counts up past TOTAL** (no cap → long brews
  record a positive TIME +/−). Tap during the countdown cancels it.
- stopped → label **save brew**, **hold 2s** → `saveBrew()` (push to history, persist
  Bean★ to the bean, then `clearForNextBrew()`). A quick tap here only flashes
  "hold to save".

**Dial** — **hold 2s** → `clearForNextBrew()`: zero the clock and blank TIME +/− / TDS /
Brew★ for the next cup **without saving** (keeps coffee + recipe + Bean★). A tap does nothing.

`clearForNextBrew()` also runs right after a save. Recipe-field changes call the lighter
`resetTimer()` (clock only).

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

## Beans + Brew history (Phase 2 — implemented)

> Deep detail + rationale live in memory `bean-data-model.md`. Summary here.

### Data model — live reference, freeze on export
Beans in `localStorage['blackmagic.beans']`, brews in `['blackmagic.brews']` (JSON
arrays; per-browser, no backend). A brew links to its bean by `beanId`. While a
record is **unlocked**, a brew's bean identity (name/roaster/roastDate/brewName) is
resolved **live** from the current bean (`brewIdentity()`) — so fixing a bean typo
flows through to every unlocked brew; the snapshot fields on the brew are a fallback
for deleted beans. Records carry `locked` + `exportedAt`: **per-bean export freezes**
the bean's current values into its linked brews and locks both; locked records ignore
live lookup and refuse edits. `nextId()`/`nextBeanId()` = `max(Date.now(),
maxExisting+1)` → stable unique keys (also the Excel match key).

### Bean tab (list-first)
Reached by the header **Bean** button *or* by tapping the coffee bar (both →
`showScreen('bean')`). Opens to a reverse-chron bean list with **＋ create new bean**
pinned on top (`renderBeanHistory('manage', …)`).
- **Tap a bean** → selects it as the current coffee, returns to brew.
- **Hold 2s** → action sheet **Edit · Export · Delete** (Delete confirmed; Edit
  disabled on locked beans). Edit loads the form (`editingBeanId`, updates in place).
- Form fields: name, roaster, **country/region/process/varietal** (all free-text +
  learning autocomplete via `optionsFor()` = seed ∪ saved values; Process used to be
  a `<select>`), roast date, **Bag Size (g)** (chips 250/340/454) + **# Bags**,
  roaster notes, my notes. Bean★ + tasting note live on the bean, edited from the brew screen.

### Brew history (slide-up overlay — **Brew screen only**)
Header **History** opens `#history-overlay`; its head = **EXPORT · BACKUP · RESTORE · ×**.
- Cards newest-first, compact `dose · TDS · ★` line. **Tap does nothing; hold 2s →
  Edit · Delete** (Delete confirmed; Edit disabled on locked brews). `bindLongPress`
  (scroll-safe, ~500ms; no `preventDefault`, movement cancels) drives the hold; cards
  set `user-select:none`/`-webkit-touch-callout:none` so iOS doesn't hijack with text-select.
- **Edit** = in-place update (`editingBrewId`): loads the brew into the Brew tab with
  **bean identity + Bean★ + Bean note LOCKED** (dimmed `.locked-field`, read-only —
  protects the bean's evolving verdict); recipe + Time/TDS/Brew★/Brew-note editable.
  Bottom timer button swaps to a **Cancel · Save** row (`#edit-actions`).
- **Side-trip restore:** entering edit snapshots the in-progress cup
  (`captureBrewState`); **both Cancel and Save restore it** (`restoreBrewState`) so
  viewing/fixing an old brew never disturbs the cup you're brewing. `saveDraft` is
  suppressed while `editingBrewId` is set.

### Record shapes
Brew: `id, savedAt, brewName, beanId, beanName, beanRoaster, roastDate, dose, grind,
agitate(+Text), contact(+Text), water, bloom, decay, brewTarget, timeAdj, tds,
brewRating, beanRating, brewNote, beanNote, locked, exportedAt, updatedAt`.
Bean: `id, savedAt, name, roaster, country, region, process, varietal, roastDate,
bagSize, bagCount, roasterNotes, myNotes, rating, tastingNote, locked, exportedAt, updatedAt`.

### Export model (three paths)
- **EXPORT** (overlay) — full dump of **both** `brews.csv` + `beans.csv`, all records,
  **no locking**, re-runnable (staggered 700ms for iOS). The Excel feed.
- **Per-bean Export** (bean hold sheet) — one flat CSV (bean cols prepended to each of
  its brews), then **freezes + locks** that bean and its brews ("commit a finished coffee").
- **BACKUP / RESTORE** — full JSON of beans+brews (`exportJSON`/`importJSON`); the
  PWA-reinstall safety net (RESTORE replaces all data).
- All CSVs carry stable **ID** keys for Excel upsert: beans `ID`; brews `ID` + `Bean_ID`
  (FK); per-bean file `Bean_ID` + `Brew_ID`. Unit conversions on export: `Time_Aim` =
  contact secs→min, `Pour_Decay` = %→fraction, `Output` = brewTarget.

## Excel integration
Workbook `~/Downloads/TFD Coffee Log 2026 Claude.xlsm` (ListObjects `BeanLog`,
`BrewLog`) ingests the CSVs via a VBA **upsert** macro `ImportBlackMagic` (source:
`~/Downloads/BlackMagicImport.bas`): matches by app `ID` (stored Text), appends new /
updates existing rows, assigns next `Bag` to new beans, writes only app-input columns
and leaves Excel formula columns alone (Combo_Name, Pour1, EY*/EQV*, and brew
Bag/Country/Roaster derived via `XLOOKUP` on `Bean_ID`). **Mac VBA constraints (cost a
lot of debugging):** Excel-for-Mac has NO `FileDialog`, `Scripting.Dictionary`, or
`FileSystemObject` — the macro uses `GetOpenFilename` (no Win-style filter), VBA
`Collection`, and native binary read + a hand-rolled UTF-8 decoder. **Never open the
CSVs directly in Excel** — it converts 13-digit IDs to `1.78E+12` and collapses them.
Pour1 (geometric first pour) = `Output·(1−r)/(1−r^n)`, `n = Time_Aim/0.5`.

## Phase 3 ideas (not yet started)
- Chart TDS or Rating over time
- Compare brews side by side
- "Use this recipe to brew now" (a separate action from Edit, which always returns to
  the current cup)

## Design conventions
Refined via a Claude Design pass; tokens live in `:root` in `index.html`.
White background, black text, with **one** restrained accent.

- **Tokens:** `--ink #0B0B0C` · `--secondary rgba(60,60,67,.6)` ·
  `--tertiary rgba(60,60,67,.34)` · `--hairline rgba(60,60,67,.13)` ·
  `--accent #9A5A2B` (warm amber). **Amber is used on Bean/History (nav), the
  TIME +/− / TDS / Brew★ / Bean★ values, and the clock's sweep hand** — not on the
  progress arc, the in-dial timer/reset hint, or the action button.
- Font: `var(--font)` system stack; all numerals `font-variant-numeric: tabular-nums`.
- Type scale: title 23/700, big pour number 54/700, metric value 21/600, save 17,
  nav 16, metric label 10/600 uppercase (0.07em), unit 11/500, in-dial timer 15.
- The ↺ reset hint is an inline SVG (grey via `currentColor`) — never an emoji glyph
  (those box-render on iOS).
- **Screen is locked** (`html,body { overflow:hidden; overscroll-behavior:none }`,
  body `position:fixed`) so a thumb-swipe can't scroll or rubber-band the page; the
  brew screen is tuned to fit an iPhone 17 Pro (402×874) at `100dvh`.
- Grids use the hairline-gap trick: `gap: 0.5px; background: var(--hairline)` with
  white cells, so gaps render as 0.5px dividers.
- Save button uses full-radius (999px); the timer has no button (tap the dial).
- **Fits the screen:** `.app` is `width:100%` (max 440px) × `min-height:100dvh` with
  `env(safe-area-inset-*)` padding, tuned so the brew screen fits an iPhone 17 Pro
  (402×874) without scrolling. Dial is 235px; shrink the pour number with it to keep
  3-digit targets clear of the sweep hand.
- Keep it a single HTML file until complexity justifies splitting.
