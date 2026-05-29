# Black Magic — Pour Over Coffee Timer

## What this is
A single-page mobile web app for logging and timing pour over coffee brews. Designed to fit an iPhone screen (390px wide). No frameworks, no dependencies — pure HTML/CSS/JS in `index.html`.

The original design mockup is `Black Magic iPhone Mockup.pdf` (Adobe Illustrator). `timer-alternatives.html` is a scratchpad from phase 1 exploring three clock designs; it can be ignored going forward.

## File structure
```
index.html              — the entire app (HTML + CSS + JS)
CLAUDE.md               — this file
Black Magic iPhone Mockup.pdf   — original design reference
timer-alternatives.html — phase 1 exploration, not part of the app
```

## App layout (top to bottom)
1. **Header** — "Black Magic" title, live date/time
2. **Brew name** — static for now ("148 Passenger Isidro Geisha")
3. **Stats grid** — 2 rows × 4 columns of editable fields
4. **Timer circle** — analog clock face with floating second hand
5. **Start / Refresh buttons**
6. **Bottom row** — TIME +/−, TDS, Rating
7. **Notes** — free-text input

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

## Phase 2 goals (not yet started)
- Save completed brew records (brew name, all input fields, TIME +/−, TDS, Rating, Notes, date)
- Browse/review brew history
- Possibly: chart TDS or Rating over time, compare brews side by side

## Design conventions
- White background, black text, no accent colors
- Font: system stack (`-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif`)
- Dividers: 1px `#e8e8e8`
- Stat labels: 9px, uppercase, #888
- Stat values: 16px, bold, #000
- Keep it a single HTML file until phase 2 complexity justifies splitting
