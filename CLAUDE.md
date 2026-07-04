# Black Magic — Pour Over Coffee Timer

## What this is
A single-page mobile web app for logging and timing pour over coffee brews. Designed to fit an iPhone screen (390px wide). No frameworks, no dependencies — pure HTML/CSS/JS in `index.html`.

The original design mockup is `Black Magic iPhone Mockup.pdf` (Adobe Illustrator). `timer-alternatives.html` is a scratchpad from phase 1 exploring three clock designs; it can be ignored going forward.

## Brew method (TFD's technique — non-standard; the whole design assumes it)
**Read this first.** The app is built around one specific pour-over method that differs
from common practice. Several design choices look wrong without this context — don't
"fix" them toward standard pour-over.

- **Bloom and Pour 1 share the first 30-second interval — there is NO standalone bloom
  phase.** The first cycle (0–30s) is: pour the **bloom** in the first ~7–10s
  ("Fast Bloom"), **tare the scale to zero**, immediately do the **1st pour**
  ("1st Pour"), then **agitate** — all inside the one interval. (He used to bloom
  separately but found front-loading the pour yields more fruit/complexity.)
  - Because the scale is **tared after the bloom**, the **bloom volume is NOT part of
    the cumulative pour targets.** `POUR_TARGETS` is the *post-tare* geometric series
    that sums to the **Output** (e.g. 350 ml); the **Bloom** (~72–85 ml) is a *separate*
    field, poured then zeroed away. So on the dial, 0–7.5s shows the **Bloom** number and
    7.5s onward shows the **cumulative pour** numbers — they are different scales, by design.
  - **Why Bloom stays its own field:** it's the **contact-time dial-in knob.** If a new
    bean finishes off the target time (e.g. 4:45 vs a 4:30 goal), use the end flow rate
    (say 24 ml / 30 s) to compute a bloom correction — next brew add ~12 ml of bloom and
    the contact time lands close. So Bloom trades against contact time, not against output.

- **No drawdown — a constant-dripper-equilibrium method.** He pours a geometric decay
  schedule (each pour ≈ **Pour Δ %** of the previous, default 90%) every 30s, which holds
  the water in the dripper at a roughly **constant reservoir volume** ("equilibrium
  volume," ~110 ml): pour-in rate ≈ drip-out rate. He **pulls the dripper the instant the
  cup reaches 350.0 ml and stops the timer** — he does **NOT** wait for the bed to draw
  down. Hence there is **no drawdown phase** anywhere (schedule, dial, captions): the brew
  ends at the last scheduled pour, not when the dripper empties. (The **−2s** baked into
  the TIME Δ calc is the reaction-time correction for stopping right at 350.) The 90%
  decay is empirically derived and robust across beans/recipes (drip-out slows as the
  filter gradually clogs, so each pour is slightly smaller to stay at equilibrium).

- **Cadence & shape:** 1–2 cups/day, essentially always a **4:30 contact time** (his
  standard). Pours `n = contact / 30` (9 at 4:30; practical range ~6–14, with **9 and 13**
  most common). Marginal pours shrink (57, 52, 46, 41 … ml) — the dial shows these as
  "**add N ml**" under each cumulative target.

## v2 (June 2026) — what changed since the sections below were written
The app went through a refinement pass (originally prototyped as a parallel "Claude
Magic" fork, then promoted to be *the* app; old v1 is at git tag `v1-final`). The
detailed sections below predate it — where they conflict, **this block wins**:

- **Dark is the only theme**, always (the big dark token/override block applies via
  `@media all`, ignoring the phone's light/dark setting; `color-scheme: dark`,
  black `theme-color`, manifest bg/theme `#000`). The light base CSS is kept but
  overridden, so a future Tools→theme toggle could re-enable it.
- **Sound is OFF** by default (`SOUND_ON = false` gates the audio engine; iOS Web
  Audio is unreliable). Visual cues carry everything. The countdown shows a **3-2-1
  pop + amber "GO" flash** in the dial (no longer audio-dependent).
- **"Decay" → "Pour ↘"** everywhere user-facing (label, editor title, history). The
  underlying id (`decay`), CSV (`Pour_Decay`), and Excel mapping are unchanged.
- **Tools screen** (`#screen-tools`, full screen; reached from the History overlay
  header "Tools" button and the top of the bean-list page). Holds: **(1) an editable
  Default Recipe** (`def-*` fields, `localStorage['blackmagic.defaultRecipe']`) that
  seeds every NEW bean — `getDefaultRecipe()` replaces the hard-coded `DEFAULT_RECIPE`
  in new-bean + `beanToRecipe` fallbacks; existing beans keep their best recipe — and
  **(2) Export / Backup / Restore**, relocated here out of the History header.
- **Brew-grid "exceptions pop":** recipe values render small + grey, and only those
  that DEVIATE from the baseline (the attached bean's best recipe, else the Tools
  default) light up amber + full size (`updateRecipeHighlights()` toggles `.diff`).
  Eligible: Grind, Water, Contact, Agitate, Pour-decay, Target — Dose & Bloom never
  flag. History deltas (`recipeDeltas`) surface the same set.
- **Analog dial:** the in-dial digital m:ss is **hidden during the brew**, revealed
  (final time) only when stopped. A per-pour **step caption** fades in under the pour
  number each 30s interval and fades after 7.5s: "Bloom + Pour 1" → "Pour 2 (90%)" →
  "Pour 3 (81%)"… (% = taper^k). It shares one slot with the reset ↺ hint (which
  shows only when stopped). No drawdown phase (constant-dripper-equilibrium method).

## v3 (June 2026) — nav + brew-screen polish (overrides older sections too)
- **Per-screen headers**, all amber-left / white-center-title / amber-right:
  Brew = `Bean · Black Magic · History`; Brew History = `Brew · Brew History ·
  Tools` (the ✕ is gone — left "Brew" closes the overlay); Bean list = `Brew ·
  Bean History · Tools`; Bean form = `Brew · Bean Magic · Beans`; Tools = `Brew ·
  Tools · Bean`. The bean header's title + right button toggle between list/form
  (`showBeanList`/`showBeanForm`). The date/time readout was removed from the brew
  header (`updateClock`/`#date-display` gone).
- **Coffee bar 2nd line** = `Country Process Varietal · M/D/YY` (values only,
  blanks skipped; `fmtDateNumeric`).
- **Recipe exceptions-pop** refined: deviations stay the SAME size as the others
  (just amber — no layout shift); non-amber values brightened and labels dimmed so
  a label reads distinctly from its value. Highlights recompute after any recipe
  load (`startBrewWith`/`restoreBrewState`/`enterBrewEdit`), not just on bean change.
- **Countdown flash** "GO" → **"Bloom +"** (cues the first pour).
- **Progress ring** is now amber **tick-marks** (a per-frame `<path>` via `arcPath`)
  that grow over 4 min, then go **solid** amber past 4:00; the grey 30s face ticks
  stay.
- **Editing a brew** returns to the Brew History list on Save *and* Cancel (the cup
  underneath is restored first). Bean edit already returned to the bean list.
- Bug fixed: the Bean note no longer collapses to one line on brew-from-bean
  (`growNotes()` now runs after the brew screen is visible).

## v4 (June 2026) — pour ritual + dial + labels (latest; overrides above)
- **Dial centre follows the real pour ritual** (`currentStep(s)`, all derived from
  elapsed in `render()`; the old tick-based step detection + "Bloom +" GO flash are
  gone). Per cycle the big number is the **weight to hit** and the caption the action:
  0–7.5s **Bloom** wt · "Fast Bloom"; 7.5–22.5s **Pour 1** wt · "1st Pour"; 22.5–30s
  Pour 1 wt · "Agitate"; each later 30s cycle **Pour k+1** wt · "Pour k+1 (R%)",
  R = taper^k. Bloom/1st-pour/agitate captions persist until the phase changes; pour
  captions fade after 7.5s. Number pops on change. Idle previews the bloom number.
- **Progress ring**: thinner ticks (stroke 2.4). Past 4:00 the full ticked ring stays
  and a **solid** arc (`#t-arc2`) grows over the overtime lap (4–8 min) — progresses
  to solid rather than snapping.
- **Labels:** Brew★ "1 (1st)"→**"1 (new)"**; Agitate "1 (min)"→**"1 (minimal)"**;
  **Pour ↘ → "Pour Δ"** (the ↘ glyph rendered poorly; Δ matches Time Δ). Ids/CSV
  unchanged.
- **Dark-mode fix:** bean-form Name/Roaster text was black-on-black (#000/#555) →
  now `--ink`/`--secondary`. Reverted the brew-title baseline nudge (header align).

## v6 (June 2026) — segmented %-complete ring + sound back on (latest)
- **Progress ring redesigned** (the fixed-4-min ticked arc is gone). The ring now =
  **% complete over the whole brew** (`s / TOTAL`, full circle = contact time; for
  overtime behaviour past 100% see v7). It's **segmented — one arc per pour**
  (`n = contact/30`): grey
  base segments built by `buildSegments()` on `recalcSchedule` (rebuild when contact
  changes), completed pours go **solid amber**, the current one fills, and `#t-dot`
  marks the leading edge. **No sweep hand.** SVG is now `<g id="t-segs">` + `<circle
  id="t-dot">`; helpers `ringArc`/`ringPos`/`renderRing`. (Removed `t-arc/t-arc2/
  t-hand/t-ticks/t-track`, `arcPath`, `drawTicks`, `CLOCK_SCOPE`, `CIRC`.)
- **Sound back ON** (`SOUND_ON = true`): countdown tones + a beep at each 30s pour
  boundary (the "be ready to pour" cue), since the ring alone could let a mid-brew
  lull slip by. iOS audio still isn't 100% reliable; visual cues back it up.
- **Tools:** Export/Backup/Restore are now compact (`.tools-data-btn`) on **one row at
  the top**, above the Default Recipe (labels shortened to Export/Backup/Restore).

## v7 (June 2026) — dial polish (latest; overrides above)
- **Idle dial reads "Ready"** (smaller, muted grey — `.pour-number.ready`, 27px
  `--secondary`) instead of the bloom number, until the brew starts. `render()` adds
  the class when `!running && elapsed <= 0.05`; the countdown removes it.
- **Overtime ring (renderRing now takes the *uncapped* `s/TOTAL`):** lap 0 paints
  amber up to the bead as before; once past the contact target the bead **keeps
  sweeping a second lap and ERASES the amber behind it** (a growing grey bite from
  12 o'clock = "you're over"). Further laps alternate paint/erase (`lap % 2`), so it
  stays coherent for arbitrarily long brews; the bead always marks "now" and `TIME Δ`
  carries the exact over/under. (No red/new colour — keeps the single-amber palette.)
  Also fixed a start glitch where the first segment lit a gap-width *ahead* of the
  bead: amber is now bounded by the true bead `frac`, not the gapped segment start.
- **Tools data buttons** are now borderless white all-caps text (EXPORT · BACKUP ·
  RESTORE, amber on press) — no box. Default-recipe header → **"Default recipe for new
  beans"**; the "Seeds every new bean…" hint (and orphaned `.tools-hint`) removed.

## v8 (June 2026) — Soft Tine sound via HTMLAudio + Tools controls (latest)
- **Sound engine rebuilt off Web Audio.** The countdown (3·2·1·GO) and the 30s
  pour-boundary cue are now **"Soft Tine"** — soft-attack/gentle-decay sine voices
  **pre-rendered to 16-bit WAV data-URIs** (`renderTones`→`wavURI`→`buildSoundAssets`)
  and played through two **HTMLAudio** elements (`countdownAudio`, `pourAudio`,
  via `playClip`). This plays on iOS's **media channel so it survives the Ring/Silent
  switch**, and removes the interruptible AudioContext entirely. The whole countdown
  is one clip (played at the start gesture); `unlockAudio()` does a muted play→pause
  on first touch so timer-driven plays are allowed. (Removed `tone`/`beep`/`getAudio`/
  `audioCtx`/`countdownNodes` and the visibility `resume()`.) **Volume is baked into
  the WAV** (iOS ignores `HTMLAudio.volume`) and the clips re-render on volume change.
  Soft Tine: countdown C5/D5/E5 pips + an E5→A5 GO rise; pour = one 660 Hz note.
- **Tools gains a Sound row** (under EXPORT/BACKUP/RESTORE, above the recipe): an
  on/off **toggle** (`#snd-toggle`, amber=on / dim=off) + a **volume slider**
  (`#snd-vol`, 0–40%, **default 10%**) with a % readout. `SOUND_ON`/`SOUND_VOL` are
  now mutable, persisted to `localStorage['blackmagic.sound']` `{on,vol}`, loaded on
  launch. Toggling on / releasing the slider plays a sample pour beep.
- **Tools "Default recipe for new beans"** title enlarged (`.tools-body
  .bean-section-label` 12px) with more space above.
- **Landscape CSS counter-rotate removed** (looked kludgy); a rotated Safari tab now
  just reflows. The installed PWA still locks portrait via the manifest.
- **`count-pop` softened to a bloom** (opacity 0.2→1 + scale 0.9→1 over 0.5s ease-out,
  was a sharp 1.35→1 scale bounce). iOS HTMLAudio has ~0.25s start latency vs the
  instant visual; spreading the number's visual change over ~0.5s lets the beep land
  mid-bloom and read as synced — device-independent (no sharp instant to disagree
  with), so it doesn't look wrong on desktop where audio is instant. The latency is
  inherent to the media-channel playback that buys Silent-Mode survival; not "fixed,"
  masked. (The step caption already fades over 0.5s.)

## v9 (June 2026) — dual-cadence dial + left-dial/right-rail layout (latest; overrides the dial/notes/ring parts of v2–v8)
The whole timer was redesigned around the insight that a pour-over is a
**dual-cadence instrument**: a fast 30s "when to pour" heartbeat and a slow
whole-brew journey. The centered dial-with-text is gone.
- **Layout:** the brew screen's timer is now a row (`.brew-instrument`) — a
  **pure analog dial on the LEFT** + a **readout rail on the RIGHT** holding the
  big cumulative pour number (`#t-ml`), a flexible caption (`#t-step`), and a
  **round** start/stop/save button (`#btn-save`, `.btn-round`). The old centered
  `.timer-section`/`.timer-center`/`.dial-timer`/`.dial-sub` + the bottom
  `.save-row` start button are removed; `.save-row` now holds only the edit-mode
  cancel/save row. The round button's hold-to-save is an amber SVG ring
  (`.btn-ring-fill`, stroke-dashoffset over 2s) instead of the pill's scaleX fill;
  the button is **dark grey, not amber** (amber stays off the action button).
- **Dial (`renderDial`, drawn each frame; replaced the segmented %-ring —
  `buildSegments`/`renderRing`/`ringArc`/`segAmber`/`t-segs`/`t-dot` all gone):**
  • a faint full **track** (`#t-face`) + a **subtle amber PROGRESS arc**
  (`#t-prog`, `progArc()`, stroke 2 @ 0.6 opacity) = elapsed/contact, continuous
  whole-brew time on the rim;  • **journey pips** (`#t-pips`, `buildPips()`, one
  per pour at `i/n` around the rim, radius PIP_R=92) riding on the arc — `.done`
  amber for poured, `.cur` amber-ring for the current pour, grey ahead;  • an amber
  **heartbeat HAND** (`#t-hand`+`#t-handdot`, HAND_R=76) that sweeps **one full lap
  per 30s** pour cycle — the live motion. (Sub-pips for 1st-pour/agitate were
  prototyped then dropped — less is more; the captions + soft beeps carry them.)
- **Flexible caption (`currentStep` rewritten):** `Ready` then `3·2·1` (in the
  caption, no animation) before start; first interval **0–10s "Fast Bloom"** (num =
  Bloom) · **10–20s "Pour {pour1}ml"** · **20–30s "Agitate"**; each later interval
  shows **"Pour {Δ}ml"** (marginal add) for its first 20s then the **live timer**
  for the last 10s; once contact is exceeded the **timer shows indefinitely** until
  stop. Big number = the **cumulative** target (bloom weight previewed at idle); it
  blooms-in on change. When stopped the caption shows the final m:ss.
- **Reset:** the ↺ moved into the dial at **half-way from centre to the south edge**
  (`.dial-reset`, top 75%) with a **"RESET" label** above it, amber, shown **only
  when stopped** (the stop→save window); hold-the-dial-2s to reset is unchanged.
- **Sound:** added a softer/lower **sub-beep** (`subAudio`, 440 Hz, `SUB_SPEC`) at
  the **10s and 20s** marks of the first interval only; the 30s pour-boundary beep
  is retained. Countdown no longer animates the number.
- **Notes are now FIXED footprints** (`growNotes` rewritten): **Brew = 2 lines,
  Bean = 4 lines**, each scrolling within itself — so the brew screen always
  presents with the same spacing (the freed space from moving the button into the
  rail pays for it). The shared anti-correlation budget (`NOTES_BUDGET_LINES`) is
  gone.

## v9.2 (June 2026) — dial polish, full-page spacing + Web Audio revert (latest; overrides the v8 audio block)
- **Overtime erase is back:** once contact is exceeded the progress arc (and the
  pips under it) **ERASE amber back to grey** from 12 o'clock (a growing grey bite =
  "you're over") instead of sitting static — the 30s heartbeat hand keeps marking
  "now", TIME Δ carries the exact over/under. `arcSeg(f0,f1)` generalises the arc;
  `renderDial` does the lap math (odd laps erase).
- **Dial details:** bigger journey pips (r 3.2 → 4.5); the 1st-pour/agitate sub-pips
  were dropped (captions + soft beeps carry them); reset is **glyph only** (no
  "RESET" label), **light grey** (`--secondary`, not amber), sitting **half-way
  from centre to the south edge** (stopped only).
- **Round button:** "save brew" stacks on two lines (save / brew); **save hold
  halved to 1s** (`btn-save` holdMs + the ring-fill transition) — the dial reset
  hold stays 2s.
- **Headings** (Black Magic / Bean History / Tools / Brew History) are **light grey**
  (`rgba(235,235,245,.7)`), not full white.
- **Full-page spacing:** the brew screen flexes to fill the app height and spreads
  its blocks down the page (`#screen-brew:not([hidden]) { display:flex; flex:1;
  justify-content:space-between }`).
- **Audio reverted to Web Audio** (the v8 HTMLAudio/WAV engine is retired). The v8
  media-channel playback survived the Ring/Silent switch but lagged ~0.25s behind the
  visual; Web Audio schedules on the audio clock (near-zero latency). **Tradeoff: the
  iPhone Ring/Silent switch now mutes cues.** Timbre = **"Soft Sine Tick"**: pour =
  one soft 520 Hz sine pip (`playPour`), sub-cue = 440 Hz softer (`playSub`, 10s/20s
  first interval), countdown = 523/587/659 pips 1s apart + an 880 GO (`playCountdown`,
  scheduled on the audio clock, cancellable via `countdownNodes`). One soft-attack/
  exp-decay `tone()` voice; a lazy shared `audioCtx()` resumed on first gesture
  (`unlockAudio`). **The Tools volume slider now truly scales output** (per-voice gain
  × `SOUND_VOL`), unlike HTMLAudio.volume which iOS ignored; default `SOUND_VOL` 0.18.
  (Removed `renderTones`/`wavURI`/`buildSoundAssets`/`playClip`/the three `<audio>`
  elements + their specs.) `audio-demo.html` is a standalone tap-to-hear audition
  page for the candidate timbres (not part of the app).

## v9.3 (June 2026) — ★ FIRST SHIPPED MILESTONE (tag `v9-ship`) — final dial/reset/Tools polish (latest)
This is the first version TFD considers shippable; `main` at this point is tagged
**`v9-ship`**. Changes since v9.2:
- **Journey pips are COMPLETION markers.** Each pip sits at its pour's END,
  `(i+1)/n` (not the start `i/n`), so it lights amber exactly when the progress arc
  reaches it (= that pour done), and **the last pour lands AT 12 o'clock — grey until
  4:30, then solid** (it shows the hollow "current" ring during the final 30s). The
  ring now marks the pour you're *filling toward* (just ahead of the arc edge). Fill
  logic is unchanged; overtime erase keys off each pip's completion frac. (Resolves
  the "amber = completed step" ambiguity — top dot = the finish line.)
- **Reset ↺ is light grey** (`--secondary`, not amber) and **aligned with the round
  save button** — both centres sit 53px above the dial's bottom edge (`.dial-reset`
  `bottom:53px; translateY(50%)` = rail padding-bottom 6 + button half 47), so the two
  "clear the timer" controls line up across the dial/rail.
- **Tools horizontal-scroll fix (iOS):** the `-webkit-overflow-scrolling:touch`
  Tools container went sideways-scrollable when content was a hair too wide (Chromium
  didn't reproduce it). `.tools-body` now has `overflow-x:hidden`; the sound %-readout
  is `4ch` (10%/40% fit) with a 4px row buffer so it isn't edge-flush.

## v9.4 (June 2026) — fresh-launch seeding + quicker save (latest; overrides above)
TFD fully closes/reopens the app before each session to recover lost sound (an iOS
Web-Audio quirk), so a clean launch is now the common path — these tune for it.
- **Clean launch seeds from the MOST RECENT brew.** `loadDraft()` still restores an
  unsaved draft first; with no draft it now picks the brew with the max `savedAt` and
  runs `brewFromBrew(recent)` — so the coffee + recipe are prefilled (coffee right
  ~98% of the time, recipe ~80%) instead of the bare default recipe + no coffee. (No
  brews yet → still the default.)
- **−2s reaction-time fudge removed.** Stopping now writes `round(elapsed − TOTAL)` to
  TIME Δ (was `… − 2`), so TIME Δ matches what the sweep hand shows; 2s of slop doesn't
  matter to the brew.
- **Save is now an instant TAP, not a 1s hold.** A tap on the round button when
  stopped calls `saveBrew()` directly (false saves are easy to edit/delete from
  History). The button's `onHold`/`holdWhen` + the "hold to save" hint (`flashHint`)
  are gone; the dial's hold-2s-to-reset is unchanged.
- **Bean note prefilled-from-the-bean reads muted grey** (`.notes-input.prefilled` =
  `--secondary`), turning full white once edited — like the Brew note's always-white,
  so an unchanged verdict doesn't shout. `updateBeanNoteColor()` (called from
  `growNotes()`) toggles the class by comparing the field to `currentBean.tastingNote`.
- **Tools volume slider range widened to 0–100%** (was 0–40%) for louder beeps;
  default still 10%. (`SOUND_VOL` already scales per-voice gain.)

## v10.8 (July 2026) — quiet auto-suggestions + list polish (latest)
- **Auto-suggested dose/bloom no longer flag amber.** `updateRecipeHighlights`
  gates the dose/bloom `.diff` on `doseTouched`/`bloomTouched` — a Loop-2
  sensitivity correction (e.g. grind 8→10 recomputing dose/bloom) is the app's
  own default and reads quiet grey; the flavor knob that caused it carries the
  amber. Only a MANUAL dose/bloom edit turns them amber. (Listener-order gotcha:
  the generic highlight listener registers before the touched-flag listeners, so
  those now re-run `updateRecipeHighlights()` after setting the flag;
  `restoreBrewState` restores the flags BEFORE its highlight pass.)
- **Brew History:** ★4/★5 ratings no longer amber (`.bl-r.hot` retired — ratings
  read like the other columns); legend's deviation column reads **"recipe Δ"**.
- **Tools:** each sensitivity table's **zero-anchor column (8 | 208° | 4:30) is
  static** — a darker-grey "0" (`.sens-zero`, `--tertiary`), no tap-to-edit
  (editing it was meaningless: `getSens` re-zeros the row at the anchor). The
  hidden input remains so `persistSens` reads 0 as before.
- **Bean list cards:** the right side shows **Bean★ amber** (18px/600,
  `.bc-rating`; blank when unrated) instead of "roast M/D" — **vertically
  centered across the name + stats pair** like a merged Excel cell (the card's
  `.bc-top` flex row holds a `.bc-main` name/stats column + the rating,
  `align-items:center`); the stats line is `Roaster · Country · W · 6/15/26` —
  **process compressed to one letter** (Washed=W, Natural=N, Honey=H, anything
  else omitted) and the **roast date (date only, M/D/YY) moved to the end**.
  `.bc-date`/`.bc-lock` CSS pruned. sw.js CACHE v55 (v10.8.1: rating 21→18px,
  centered; `·` between country and process letter). v10.8.2: card padding
  12px → 7px top / 8px bottom (9px visual gap above name = below stats; card
  61→52px so more beans fit one screen). CACHE v56. v10.8.3: **version build
  stamp at the bottom of Tools** (`.tools-version`, tiny tertiary all-caps —
  keep in sync with each release, see Deploy loop). CACHE v57. v10.8.4:
  padding → 5px/6px, explicit `line-height: 1.2` on name + stats, stats
  margin-top 4→3px; card 52→47px desktop. CACHE v58. v10.8.5: added
  `html { -webkit-text-size-adjust: 100% }` on an (incorrect) autosizing theory
  — harmless, kept. CACHE v59. v10.8.6: bean-card rating 18→**14px** (same size
  as the coffee name; amber carries the emphasis). CACHE v60. v10.8.7: **actual
  root cause of the persistent "too much space above the name": iOS Dynamic
  Type / Larger Text scales system-font TEXT in installed web apps** (TFD runs
  a larger text size; small sizes scale more than large — names +~30%) and
  **CSS cannot opt out** (`text-size-adjust` doesn't govern it — v10.8.5/v10.8.6
  changed nothing on-device, proven by identical screenshots at stamped
  versions). First fix attempt: line-heights in **FIXED PIXELS** (name/rating
  17px, stats 13px; padding 6px symmetric). CACHE v61 — still not enough (see
  v10.8.8). v10.8.8: **the pinned line-height was being bypassed by the LINE-BOX
  STRUT**: `bc-name` was an inline `<span>` inside `bc-main`, so its line box
  height = max(span's pinned 17px, bc-main's strut = *inherited* font-size ×
  normal leading) — and Dynamic Type inflates that inherited size, so the strut
  towered over the pin and dumped phantom space **above the name only** (the
  version-independent asymmetry in every screenshot; `bc-stats`, its own block
  with pinned line-height, never suffered). Fix: `bc-name { display: block }` +
  `bc-main { line-height: 17px }` — a block's line box uses its own pinned
  line-height. **Reproduced + verified in desktop Chrome** by inflating
  bc-main's font-size (strut source): old markup 55px card / 10px above name;
  fixed markup 46px / 6px, immune to inflation. **Full pattern for TFD-proof
  list rows: pin line-height in px ON THE BLOCK that owns each line (make
  inline text display:block), never rely on a span's line-height alone.**
  Card = 46px on every device. CACHE v62 — on-device rows shrank (138→127
  screenshot px) but extra space above the name STILL remained. v10.8.9:
  **tap-the-version-stamp layout diagnostic** — tapping `#tools-version` lays
  out a hidden probe bean-card and replaces the stamp with the device's OWN
  measured geometry (card/main/name/stats/rating heights, computed
  font-size/line-height pairs, top/mid/bottom gaps, dpr); tap again to restore.
  Ends the screenshot-forensics loop: the phone reports its real numbers.
  CACHE v63.

## v10.7 (July 2026) — tier-5 false-lock fix + one-time repair
Root cause of "history says blm* ≈ 80 but a new cup suggests 74": the bean's
`bestRecipeRating` was silently stuck at 5 with no 5★ brew, so every 4★ save's
cohort update was tier-blocked and `bestBloom` stayed a pre-Loop-1 raw copy.
The lock came from `saveBean`'s hand-edit rule: it compared the form against the
RAW stored fields, so the v10.1 TDS-aim auto-backfill (form shows 1.72 for a
pre-v10.1 bean that stored nothing) counted as a hand edit on any "update bean".
- **`saveBean` lock rule fixed:** `recipeChanged` now compares against the values
  the form was SEEDED with (`beanToRecipe(bean)` — blanks filled from defaults),
  so a no-op save / auto-backfill can never lock; and **dose & bloom are excluded**
  — they're bean characteristics whose manual re-anchors the Loop-1 cohort mean is
  supposed to absorb. Only FLAVOR-choice edits (grind/agitate/contact/water/
  pourΔ/target/TDS-aim) still declare the deliberate tier-5 "this is best".
- **One-time repair on launch** (`repairTierLocks`, flag
  `localStorage['blackmagic.mig.tier5']`): any bean at tier 5 with NO actual 5★
  brew drops to its highest brewed tier, and if that tier is ≥4 its
  bestDose/bestBloom are immediately re-estimated from the tier's same-signature
  cohort (mean implied dose/bloom) — so the next cup seeds correctly without
  waiting for another 4★ save. Runs once; deliberate tier-5 locks made after this
  build are never clawed back. sw.js CACHE v53.

## v10.6 (July 2026) — deviation baseline = the DEFAULT recipe + calmer Tools/bean form
- **History deviation tokens now compare to the TOOLS DEFAULT recipe, not the
  bean's best** (`compactDeltas(r, def)`). The token describes the cup's recipe vs
  the standard, so it never rewrites itself when the bean's best evolves: a bean
  dialed in at T212 shows T212 on every such cup forever (and 212 renders amber on
  its Bean form) — the 6×5★-at-212 scenario reads exactly as intended. **A
  non-standard TDS aim is now also a token**, plain number format ("1.68"); a
  missing tdsAim = the Tools target → no token (pre-v10.1 brews need no backfill).
- **Bean form:** best-recipe **dose & bloom NEVER flag amber** (bean
  characteristics — differing from the default is expected); the recipe choices
  still flag vs the default. **TDS aim is grey while it equals the Tools target,
  amber otherwise** (`.vr-aim-field` lost the always-amber class; handled in
  `updateBestHighlights`), and matched to recipe-value size (18px).
- **Tools:** ALL amber removed from the marginal-sensitivity cells (the v10.5
  grey-at-0/amber-non-zero `.nz` rule retired — sensitivities are slow-moving
  calibration data, not signals) and from the volume slider (`accent-color`
  grey); "Sound on" is the row's only amber.
- **Brew History spacing:** gutters 10→12px, slightly wider numeric columns, 8px
  extra padding before the deviation column; the legend now labels **date** and
  **recipe**.
- **Bug fixed — brew-from-bean collapsed the notes to base size (Brew 2 / Bean 4
  instead of 4/5):** the `.screen` transition animated `display` with
  allow-discrete, so for 260ms after a bean→brew switch BOTH screens stayed laid
  out; `growNotes()` measured during that window, saw zero slack, and granted no
  extra lines. The leaving screen now hides instantly (`display` dropped from the
  transition; the entry fade via @starting-style is unchanged). Brew-from-history
  never hid the brew screen, which is why that path worked. sw.js CACHE v52.

## v10.5 (July 2026) — dose/bloom are BEAN characteristics + history shows ideals
Conceptual anchor from TFD: **grind/temp/contact/agitate/TDS-aim are the recipe;
dose & bloom are bean characteristics** — two beans can share a recipe with very
different doses/blooms. The app now behaves that way end-to-end:
- **Every fresh cup seeds dose & bloom EMPIRICALLY**: `startBrewWith` ends with
  `autoSuggestDoseBloom()`, so clean launches, Brew-from-history, and
  Brew-from-bean all take flavor variables from the source but dose/bloom = the
  bean's best (Loop-1 cohort mean) + Loop-2 sensitivity corrections. (Previously a
  clean launch copied the recent brew's RAW dose/bloom, bypassing the cohort
  average.) No live bean → snapshot values stand. Manual touched-flags still win.
- **Marginals are live:** editing any sensitivity Δ cell (or the TDS aim) in Tools
  re-runs `autoSuggestDoseBloom()` — the brew screen's suggested dose/bloom track
  the table in real time.
- **Brew History shows IDEAL values, not errors:** the Δdose/Δblm columns became
  **dose\* / blm\*** = `impliedDose`/`impliedBloom` (dose·aim/TDS; bloom +
  lastPour/30·TimeΔ) — the same outcome-corrected numbers the cohort mean
  averages, so a cohort's dose\* column averages to the bean's bestDose. Layout:
  `★r · date · dose · blm · tds · dose* · blm* · deviations` — **date sits right
  after the rating** (shows the within-group sort of 4/5★ runs); raw inputs +
  deviation tokens render small/dim (10px tertiary, `.bl-sm`); dose\*/blm\* are
  the heavy values (13px/600, `.bl-star`), amber only past the noise floor
  (|TDS−aim| > .02, |blm\*−bloom| > 5 ml); **rating amber only for ★4/★5**
  (`.bl-r.hot`); the column legend repeats under every bean header; the
  deviation-signature sort is numeric-aware (G7 before G10).
- **Sens tables re-anchored & mirrored:** zero anchors = the standard recipe
  (grind 8 / **temp 208** / contact 4:30); `getSens()` re-zeros every row at its
  anchor (lossless — only differences are used, so a stored 204-anchored temp
  row shifts to 208=0 automatically; `SENS_ANCHOR`). **Temp + contact display
  REVERSED** (212→196, 5:00→3:00; `SENS_VARS[].rev`, display order only — storage
  stays ascending, `sensAt` unchanged) so every table's zero column is the 2nd:
  8 | 208° | 4:30 align down the screen. Interpolation reminder: `sensAt` is
  piecewise-linear between levels, clamped at the ends (grind 8.5 = midpoint of
  Δ(8),Δ(9); temp 203 = Δ(200) + ¾·(Δ(204)−Δ(200))).
- **Relaunch = reset:** a stopped-but-unsaved cup can't be saved after relaunch
  (draft has no `elapsed`), so `loadDraft` now clears `time-val` — the timer opens
  in the "Ready" state instead of showing a phantom Time Δ (TDS/Brew★ still
  restore). In-session edit side-trips (`restoreBrewState`) are unaffected.
- **Small:** TDS Aim editor presets → 1.68/1.70/1.72/1.74/1.76 (brew + bean form);
  the def-title TDS aim value enlarged to 14px (reads editable).
- **Gotcha fixed while building: never write `dose*` immediately followed by `/`
  inside a CSS comment** — the `*/` terminates the comment early and silently
  kills every rule to the next `}` (write "dose\* and blm\*"). sw.js CACHE v51.

## v10.4 (July 2026) — ★ AESTHETIC-CONSISTENCY PASS: amber = signal, everywhere
The brew screen's grey-until-changed rule now governs the whole app; "amber =
merely editable" is retired (everything is tap-to-edit — the affordance carries
nothing). Solid amber **fill** stays the deliberate exception: it means "commits a
form" (save/update bean, edit-save, Done, selected chips) — the round start button
stays grey by design.
- **Amber diet:** the Tools default recipe renders quiet grey (it IS the baseline —
  nothing to deviate from); sensitivity Δ cells are grey at 0, amber only when a
  non-zero correction rides (`renderSensField` toggles `.nz`); the bean form's Best
  recipe lights amber only where it DEVIATES from the Tools default
  (`updateBestHighlights`, called from `setBeanRecipeFields` + best-* changes) — so
  "what makes this bean special" pops. Verdicts (TDS Aim / Bean★ / Bean notes) stay amber.
- **Brew History noise floor:** Δdose/Δblm go amber (`.bl-err.hot`) only past
  **|TDS − aim| > 0.02** (dose) / **|Δblm| > 5 ml** (bloom); in-noise errors read grey.
  (Formulae unchanged: Δdose = (1 − TDS/aim)·dose, Δblm = lastPour/30 · TimeΔ.)
  **>2 deviation tokens display as "Many"** (the full signature still drives the sort).
  Columns re-spaced to the real data widths with even 10px gutters; the panel now
  matches the screen surface (**#0B0B0C**, header border gone — it presents as a
  sibling screen, not a sheet); legend tracking 0.07em.
- **Grind sensitivities in whole steps 7–11** (was 7–9 by .5). Defaults keep 7/8/9
  from the logbook and extend the 8→9 slope (dose 0.8/1.2 g, bloom 10/15 ml at
  10/11). `getSens()` **re-samples stored tables from an older level layout**:
  user-edited Δs survive via interpolation inside the old range; levels outside it
  take the new defaults (no extrapolation off a noisy end cell). Same-levels stores
  load as before; a level change can no longer corrupt saved Δs.
- **Tools layout:** EXPORT/BACKUP/RESTORE are compact dark **pills** (`.tools-data-btn`);
  the TDS aim rides inside the section title — **"DEFAULT RECIPE (TDS AIM = 1.72)"**,
  value tappable (`.def-title .field`, same `sens-tds` store, editor label "TDS aim");
  the Sound row moved to the **bottom** (below the sensitivities). Sens rows now share
  a true **baseline** (a zero-width-space `::before` strut at the 14 px value size in
  every cell — labels and values no longer sit on different centers); header sizes
  unified (var 11/700, levels 11/600, row labels 10/600 at 0.07em).
- **Bug fixes:** editing a past brew rendered the locked Bean★ cell as a *lighter
  box* — `.locked-field`'s opacity made the opaque cell bg translucent over the
  hairline grid backdrop; `.bottom-stat.locked-field` now stays opaque and dims only
  its children. Edit mode's caption shows the **record's final time** (contact + Δ,
  e.g. "4:40") instead of the live-timer word "Ready". Removed a dead
  `visibilitychange` → `updateClock()` handler (v3 deleted the clock; the handler
  threw a silent ReferenceError on every app foregrounding).
- **Type unification:** bean-form / text-field / section labels now use the 10 px /
  600 / 0.07em token (were 9 px / 0.4px absolute); roast-date input 16 px (matched
  its 16 px siblings); best/def grid values 18 px 0.88-white (match the brew grid).
- **Prune:** the unreachable 'browse' mode of the bean list (`renderBeanHistory` →
  `renderBeanList`) + all `.bc-detail/.bc-actions/.bc-delete-link` CSS, `.time-cell`
  family, `.brew-name`, `.history-export/.hh-actions`, `.save-row.two`, `.header
  .date`, and their dark-theme references. sw.js CACHE v50.

## v10.3 (July 2026) — TDS Aim* grey-until-changed + edit-mode fit
- **TDS Aim\* is light grey while it equals the bean's stabilized aim, amber once
  moved off it** — its results-row button dropped the always-amber class; the
  existing `.diff` pass (`updateRecipeHighlights`, tds-aim already in
  `HILITE_FIELDS`) drives dedicated `.bottom-stats .field[data-f="tds-aim"]` rules.
  (TDS / Brew★ / Bean★ stay always-amber.)
- **Editing a past brew hides the dial** (`#screen-brew.editing .timer-circle-wrap
  { display:none }`, class toggled in `enterBrewEdit`/`exitBrewEdit`) — a record
  fix isn't a live cup, and the freed ~200px lets the cancel/save row fit WITH the
  full v9.6 note footprint (`growNotes()` re-measures after the edit layout
  settles). The rail readout (Time Δ + caption) stays visible/tappable.
- **Bug fixed:** the round start button showed during edit — `.btn-round`'s
  `display:flex` overrode the UA `[hidden]` rule (author styles always beat UA
  styles); explicit `.btn-round[hidden] { display:none }`. This (plus the dial)
  was why cancel/save hung off-screen on the phone. sw.js CACHE v49.

## v10.2 (July 2026) — Time Δ slot takeover + history/tools/bean polish
- **Time Δ has no field on the brew screen anymore.** On stop, the big pour-number
  slot (`#t-ml`) shows it instead — e.g. **"+5 sec"**, amber, 21px (`.pour-number
  .tdelta`) — until save/reset blanks it; the caption below still shows the final
  m:ss. **Tap the slot to adjust** (opens the shared editor; the hidden `#time-val`
  store remains, `renderField('time-val')` safely no-ops with no button). Display is
  keyed off the **value**, not timer state, so a stopped-unsaved cup restored on
  relaunch (draft has no `elapsed`) still shows its Δ. The results row is `TDS Aim*
  · TDS · Brew★ · Bean★`.
- **Brew History lines use the normal system font** (the v10.1 monospace was hard
  to read): a shared **CSS grid** (`.bl-grid`, fixed column template + `tabular-nums`)
  keeps ★/dose/blm/tds/Δdose/Δblm/deviations/date aligned. Rows padded 12px (reliable
  taps), **Brew★ amber** (`.bl-r`), and a **heavier border closes each rating group**
  within a bean (`.tier-end`, applied to the last line before the rating changes).
- **Tools: TDS target sits under the Default-recipe section** (it's the default aim
  seeded into new beans + the fallback aim for pre-v10.1 brews — recipe, not a
  sensitivity). Sensitivities table unchanged below it.
- **Bean form: TDS Aim above Bean★** in the verdict block (closer to the recipe grid).
- **Ops note:** GitHub Pages deploys can fail transiently (v10.1's deploy `49a66ee`
  failed; the next push carried it through — the phone showing a stale version was
  exactly this). After pushing, **verify the latest `pages-build-deployment` run
  conclusion** (`gh run list --workflow pages-build-deployment`), don't assume.
  sw.js CACHE v48.

## v10.1 (July 2026) — per-bean TDS aim + Brew History as a dial-in table
- **Labels (v10.1.1):** the brew screen shows **"TDS Aim\*"** — the \* marks the
  *working* per-brew value — while the bean form's stabilized target is plain
  **"TDS Aim"** (`FX['best-tds-aim'].label` overridden after the RECIPE_MAP clone).
- **TDS Aim is the 9th recipe field** (id `tds-aim`, bean-form id `best-tds-aim`,
  record/bean key `tdsAim`; `recKey()` maps the two irregular ids). TFD brews
  different beans at different strengths, so the target is no longer a global
  constant: it lives on the **brew results row** (replacing Time Δ, which moved to
  the **dial rail** above the round button, `.rail-time` — same `time-val` id, stop
  still writes it), on the **bean form** under Bean★ (`.vr-aim`), and on every brew
  record. In `RECIPE_FIELDS`/`BEST_KEYS`/`HILITE_FIELDS`/`DRAFT_FIELDS`/`SIG_KEYS` —
  so it highlights amber when off the bean's aim, rides drafts, and **splits Loop 1
  cohorts** (a 1.60 run never averages with a 1.72 run; pre-v10.1 brews with no
  `tdsAim` are treated as the Tools TDS target, which doubles as the default aim
  for new beans via `getDefaultRecipe()`).
- **Loop 2 with strength scaling:** suggested dose = (bestDose + sensitivity
  corrections) × (aim / bean's aim) — dose ∝ TDS to 1st order (aim 1.60 on a bean
  dialed at 1.72 → dose × 0.930). Bloom is not scaled by aim (no marginal yet). A
  4★/5★ save adopts the brew's aim onto the bean like the other recipe fields, so
  "preferred the weaker cup → rate 5" re-anchors the bean at the new strength.
  Loop 1's `impliedDose` corrects each cohort brew toward **its own** recorded aim.
- **Brew History overlay redesigned** (the bean LIST is unchanged): a **bean-name
  section header per bag** (beans are drunk sequentially — no name repetition),
  then **one monospace line per brew** (`ui-monospace`/SF Mono, columns align):
  `★r dose blm tds Δdose Δblm deviations · date`. **Only the two error columns are
  amber**: `Δdose = (1 − TDS/aim)·dose` (dose short/over for the aim, 1st-order) and
  `Δblm = lastPour/30 · TimeΔ` (bloom short/over for contact). Deviations vs the
  bean's best are compact tokens: `G9 T204 3.5' A2 P85 V1050 @1.60` (grind, temp,
  contact-minutes, agitate, pour Δ, target, TDS aim). A `.bh-legend` header row
  decodes the columns; dim `M/D` date right-aligned; tap → same Brew/Edit/Delete
  sheet. v9.6's sort (bean → ★ desc → deviation signature → newest) is unchanged.
  `recipeDeltas`→`compactDeltas` (also the sort's signature); the old card markup +
  the v9.5 "4/5★ Bloom/TimeΔ appendix" are superseded by the error columns;
  `fmtSavedAt` removed.
- **CSV:** brews gain `TDS_Aim` (after `TDS`), beans gain `TDS_Aim` (after the
  `Best_*` block). The Excel macro maps columns by name, so the new columns are
  inert until mapped. sw.js CACHE v46.

## v10 (July 2026) — ★ CLOSED-LOOP DIAL-IN: marginal sensitivities + cohort-averaged best recipe
The app graduates from logbook to advisor. Core reframing (from TFD's paper-logbook
header): **Grind/Temp/Contact/Agitate are the FLAVOR choices; Dose & Bloom are
dependent CONTROLS** solved to hold the two targets constant (dose ↔ TDS 1.72,
bloom ↔ contact time). Noise floor: TDS σ ≈ ±0.015, contact σ ≈ 5s — single brews
are noisy; averages converge. **Brew★ is a dial-in state machine** (now load-bearing
logic, not just labels): 1 = noisy first datapoint from population priors, 2 =
converging, 3 = deliberate off-recipe test of one flavor variable, 4 = locked on the
standard recipe (sampling), 5 = improved recipe adopted (sampling resumes there).
- **Tools gains "Marginal sensitivities"** (`SENS_DEFAULT` seeded from the paper
  logbook; `localStorage['blackmagic.sens']`; `buildSensTables()` renders 3 dynamic
  6-col grids — Grind 7–9×.5, Temp 196–212×4, Contact 3:00–5:00×:30 — each level an
  editable Δdose/Δbloom tap-to-edit cell, plus a **TDS target** field, default 1.72).
  Each Δ is relative to an arbitrary anchor row; **all math uses differences
  f(new)−f(old), so the anchor cancels** (logbook base 204° vs app 208° is moot).
  `sensAt()` linearly interpolates between levels, clamps past the ends. Only the Δ
  cells persist (levels fixed) so future level edits can't corrupt stored data.
- **Loop 2 — cross-recipe prediction (`autoSuggestDoseBloom`):** editing
  grind/temp/contact on the brew screen recomputes **dose & bloom = bean best +
  Σ sensitivity differences** (`recipeCorrection`), written straight into the
  fields. **Dose & Bloom now flag amber** when off the bean's best (added to
  `HILITE_FIELDS` — the v2 "Dose & Bloom never flag" rule is retired: off-best now
  means a correction or override is riding). A manual dose/bloom edit sets
  `doseTouched`/`bloomTouched` and wins — never recomputed over (flags reset on
  `startBrewWith`/`selectBean`/post-save; carried through the edit side-trip
  snapshot; guard: no-op while `editingBrewId`). Reverting the flavor variable
  restores best and clears the amber.
- **Loop 1 — within-recipe estimation (`persistBestRecipe` rewritten):** a fresh
  4★/5★ save adopts the brew's flavor variables as the best recipe (tier protection
  unchanged), then sets **bestDose/bestBloom = equal-weight mean over the cohort**
  (same bean + same Brew★ tier + same flavor signature `recipeSig` over
  grind/water/contact/agitate/decay/target) of each brew's **outcome-corrected**
  values: `impliedDose = dose × (TDS target / measured TDS)` (dose ∝ TDS, 1st
  order); `impliedBloom = bloom + (lastPour/30s) × TimeΔ` (end-flow-rate rule;
  `lastPourOf()` recomputes the geometric schedule's final pour per brew). After the
  save the live dose/bloom fields are seeded with the refreshed estimate — the next
  cup starts at the new best. No recency weighting (TFD's choice) — bag-aging drift
  is handled by manual bloom override, which the cohort mean then absorbs.
- **New-bean priors:** `DEFAULT_RECIPE` dose 24→**23.8g**, bloom 85→**90ml** (means
  across ~200 past beans for TDS 1.72 / 4:30; true per-bean values range 21–25g /
  60–130ml, so the 1★ first brew is expected to miss and Loops 1–2 converge from
  there).
- **BACKUP/RESTORE now carries settings** (JSON `version:2`: `settings.defaultRecipe/
  sens/sound`); restore writes them back and **reloads the app** to re-seed. Old v1
  backups still restore (beans+brews only). Sensitivities are NOT in the CSV export
  (device settings, not data).

## v9.6 (July 2026) — History dial-in sort + adaptive full-page notes
- **Brew History is no longer chronological — it's sorted for dial-in reading**
  (`renderHistory`): **BEAN** (groups; the most recently brewed bag first) → **Brew★
  descending** (unrated last) → **changed-variable signature** (`recipeDeltas().join()`,
  so brews that tested the same variable sit together; the 4/5★ Bloom/Time appendix is
  per-cup data and deliberately NOT part of the key) → **newest first**. Rationale: TFD
  reads same-recipe runs as a group — averaging over input noise (TDS SD ≈ ±0.015,
  contact SD ≈ 5s) and eyeballing bloom/contact drift as a bag ages (beans slow over
  time → bloom must rise to hold contact). A planned future step is a table of marginal
  sensitivities to compute a per-brew "surprise" for TDS/Bloom even across recipe
  changes.
- **Notes use the full page, adaptively** (`growNotes` rewritten): base footprints stay
  Brew 2 / Bean 4 (the v9 layout known to fit), then the function measures the brew
  screen's real leftover flex slack (children heights + margins vs `clientHeight`,
  12px held back for space-between breathing) and grants up to 3 extra lines toward
  **Brew 4 / Bean 5**, in priority order Brew → Brew → Bean. Degrades gracefully on
  smaller safe-area-adjusted heights / larger Dynamic Type (verified 4/5 → 3/4 → 2/4
  with no overflow). Constants: `NOTES_BREW_LINES/NOTES_BEAN_LINES` (base),
  `NOTES_BREW_MAX/NOTES_BEAN_MAX`.

## v9.5 (June 2026) — bean brew-note + coffee-bar recipe load + History tweaks
- **The bean now carries an evolving BREW note (`bean.brewNote`)**, parallel to the
  existing tasting note. On a fresh save the brew note is written to the brew record
  (`brewNote`, unchanged) AND **overwrites `bean.brewNote`** (`persistBeanBrewNote()`,
  alongside `persistBeanNote`, same `loadedFromHistory` guard) — so over many cups it
  evolves from noisy per-cup observations into a memorialised insight ("lower temp
  better for naturals") and doubles as a next-cup plan. Every new brew **prefills
  `#notes-brew` from `bean.brewNote`** (set in `setBeanBar`, mirroring the bean note;
  `startBrewWith` no longer blanks it; `clearForNextBrew` carries it forward so
  back-to-back cups keep it). It reads **muted grey until edited** (the `.prefilled`
  treatment now covers BOTH notes — `updateBeanNoteColor`→`updateNoteColors`, keyed off
  `currentBean.brewNote`). Not in the CSV export yet (the per-brew note already exports;
  `bean.brewNote` rides JSON BACKUP/RESTORE) — add a `Brew_Notes` BeanLog column + macro
  map if it's wanted in Excel.
- **Coffee-bar swap loads the bean's best recipe.** `selectBean` (the top-center
  "Select a coffee ⌄" → `'attach'` path) now also loads the chosen bean's best recipe
  (`beanToRecipe`) + recalcs + re-flags highlights, not just the coffee/Bean★/notes.
  (Time/TDS/Brew★ are left alone — still a lighter swap than `brewFromBean`.)
- **History stats line:** for **4★/5★** brews (which usually have no recipe delta to
  show) the line appends **Bloom + Time Δ** in amber (e.g. `25g · TDS 1.40 · ★4 · Bloom
  120 · Time -3`) — to eye whether contact time is drifting as a bag ages. 3★ test
  brews still show the changed-variable deltas (`recipeDeltas`).
- **1st-pour/agitate sub-beeps now full volume** (`playSub` gain 0.32 → 0.5, matching
  `playPour`); still lower-pitched (440 Hz) to stay distinct from the 30s pour cue.

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

**Deploy loop:** branch → edit → verify → merge to `main` → the **"Deploy Pages"
Actions workflow** (`.github/workflows/deploy.yml`) publishes (~1–2 min). Bump the
`CACHE` version in `sw.js` when changing cached assets so clients pick up the
update, **and keep the Tools `.tools-version` build stamp in sync** (e.g.
"v10.8.3 · cache v57") — it's the definitive "which version is this phone
running?" check. `gh` CLI lives at `~/.local/bin/gh` (logged in as `tfdunn`).
`.claude/` is gitignored.

**Deploy reliability (July 2026):** Pages was switched from the legacy
branch-based pipeline (`pages-build-deployment`) to **workflow-based deployment**
(repo Pages `build_type=workflow`) because the legacy deploy step failed
transiently 3× ("Deployment failed, try again later") with no retry hook.
`deploy.yml` retries the deploy step up to **3 attempts** (30s/60s pauses), so
flakes self-heal. Still **verify the run conclusion after pushing**:
`gh run list --workflow deploy.yml`. Manual retrigger (replaces the old
empty-commit trick): `gh workflow run deploy.yml`.

**CDN staleness (v10.8.2 lesson):** GitHub Pages serves with
`cache-control: max-age=600`, so a phone can get a copy up to **10 minutes older
than a successful deploy** — the Fastly edge keeps serving what it cached until
the TTL expires (the SW's `no-store` bypasses only the local HTTP cache, not the
CDN). A "deploy succeeded but the phone shows the old version" report inside that
window is normal; check the Tools version stamp, wait ~10 min, or switch networks
(Wi-Fi ↔ cellular hits a different edge) before debugging anything else.

**Auto-update:** the SW is network-first with `{cache:'no-store'}` (always fetches
fresh when online; cache is offline fallback only) and `skipWaiting()` +
`clients.claim()`. `index.html` calls `registration.update()` on load and on every
`visibilitychange`, and reloads once on `controllerchange` — so reopening the
installed PWA (while online) pulls the latest version on its own. A stuck old
install can still be reset by removing the home-screen icon and re-adding it
(⚠️ that may clear the PWA's `localStorage` — export brews/beans first).

## App layout (top to bottom)
1. **Header** — Brew screen: `Bean` (top-left), title + live date/time, `History`
   (top-right). Bean screen: `Brew` (top-left), title; in the **bean form** an amber
   `Beans` appears top-right (cancel → list). All nav text is amber.
2. **Coffee selector** — full-width `Select a coffee ⌄` row. Opens the Bean tab in
   **`'attach'` mode**: tapping a bean swaps the coffee **without touching the recipe**
   (vs the top-left `Bean` button → `'manage'` mode, where Brew loads the bean's recipe).
   See "Bean tab — two entry modes".
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
| Pour ↘ (id `decay`) | 1 | 85 / 90 / 95 / 100 | "%" — per-pour taper; see v2 block |
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

**Portrait lock:** manifest `orientation:"portrait"` keeps the installed PWA upright.
(The old CSS counter-rotate fallback for a rotated Safari tab was removed in v8 — it
looked kludgy; a rotated tab now just reflows.)

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
  Bean★ + Bean note + **best recipe** to the bean, then `clearForNextBrew()`). A quick
  tap here only flashes "hold to save".

**Brew timestamp:** a saved brew's `savedAt` is the **start time** (the instant "GO"
fires and the timer starts), not the hold-to-save time — captured in `brewStartedAt`,
used by `collectRecord()`, and round-tripped through the draft so a stopped-but-unsaved
brew keeps its real time. Editing a past brew preserves its original `savedAt`.

**Dial** — **hold 2s** → `clearForNextBrew()`: zero the clock and blank TIME +/− / TDS /
Brew★ for the next cup **without saving** (keeps coffee + recipe + Bean★). A tap does nothing.

`clearForNextBrew()` also runs right after a save. Recipe-field changes call the lighter
`resetTimer()` (clock only).

### Sound — **see v8 (Soft Tine via HTMLAudio/WAV); the Web Audio version below is retired**
- *(historical)* Web Audio oscillators scheduled on the AudioContext clock; brighter
  tones (392/440/523 → 784 GO, 880 pour). Replaced in v8 because the iOS Ring/Silent
  switch muted Web Audio and the AudioContext could be interrupted. The v8 engine
  pre-renders Soft Tine to WAV data-URIs played through `<audio>` (media channel →
  survives Silent Mode), with on/off + volume in Tools. Details in the v8 block.

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

### Data model — live reference
Beans in `localStorage['blackmagic.beans']`, brews in `['blackmagic.brews']` (JSON
arrays; per-browser, no backend). A brew links to its bean by `beanId`. While a
record is **unlocked**, a brew's bean identity (name/roaster/roastDate/brewName) is
resolved **live** from the current bean (`brewIdentity()`) — so fixing a bean typo
flows through to every unlocked brew; the snapshot fields on the brew are a fallback
for deleted beans. `locked`/`exportedAt` remain in the model for any records frozen by
the (now-retired) per-bean export, but **no current path creates new locks**; locked
records still ignore live lookup and refuse edits. `nextId()`/`nextBeanId()` =
`max(Date.now(), maxExisting+1)` → stable unique keys (also the Excel match key).

### Best recipe (evolves on the bean, like Bean★/tasting note)
Each bean carries a **best recipe** — the 8 input fields stored as
`bestDose/bestGrind/bestAgitate/bestContact/bestWater/bestBloom/bestDecay/bestTarget`
+ a `bestRecipeRating` tier. New beans seed the **default recipe** (`DEFAULT_RECIPE`:
24g · 8# · agitate 1/min · 4:30 · 208°F · 85ml · 90% · 350ml) at tier 0.
- **Write (tier-protected, `persistBestRecipe()`):** on a fresh save with Brew★ ≥ 4,
  if `brewRating ≥ bean.bestRecipeRating`, the brew's recipe is copied onto the bean and
  the tier set to that rating — so a later 4★ never clobbers a 5★. Guarded by
  `loadedFromHistory` (editing a past brew never writes), same as Bean★/note.
- **Manual edit:** the bean form shows the best recipe as **editable** `.field` cells
  (`best-*`, reusing the brew screen's tap-to-edit `#ed-bg`; FX configs cloned via
  `RECIPE_MAP`). Hand-editing an existing recipe sets `bestRecipeRating = 5` (a deliberate
  "this is best"), so only a 5★ brew or another edit can replace it.

### Bean tab (list-first) — two entry modes
Reached two ways, distinguished by `beanPickMode` (set on the way in):
- **Coffee bar** (top-center "Select a coffee ⌄") → `'attach'`: **tap a bean swaps the
  coffee + Bean★ + bean note but leaves the recipe alone** (`selectBean`), returning to
  brew immediately. The quick mid-cup swap.
- **Bean button** (top-left nav) → `'manage'`: tap a bean → action sheet
  **Brew · Edit · Delete** (Delete confirmed; Edit disabled on locked beans).
  - **Brew** (`brewFromBean`) → start a **fresh cup**: coffee + recipe + Bean★ + bean
    note all loaded from the bean's **best recipe** (changes coffee AND recipe). Always enabled.
  - **Edit** loads the form (`editingBeanId`, updates in place).

Both open the same reverse-chron list (`renderBeanHistory('manage', …)`) with **＋ create
new bean** pinned on top. No long-press anymore — plain tap (scroll-safe; a scroll gesture
doesn't fire `click`).

**New/Edit Bean form** (top → bottom): name · roaster · `Country | Process` ·
`Region | Varietal` · **`Roast Date | Bags @ Size`** (Roast Date is 50% so its divider
lines up with the rows above; the right cell combines **# Bags `@` Bag Size** into one tight
unit, e.g. "2 @ 12oz") · **Roaster Notes** · **Best recipe** (centered header aligned with
Roaster Notes; editable 8-field grid whose **values render amber** to signal they're editable
— override the default even before the 1st brew) · **`Bean ★ | Bean Notes`** (the bean's
verdict — editable here too; Bean★ shown larger) · **save/update bean**.
- **Header (form view):** grey "‹ Beans" removed; **three exits** — amber **Brew**
  (top-left, `btn-to-brew`) = cancel→brew; amber **Beans** (top-right, `btn-to-beanlist`,
  shown only in the form) = cancel→list; **save/update bean** (bottom) = save→list. Cancels
  reset `editingBeanId` + clear the form.
- **Free-text fields** (country/region/process/varietal/roaster) use learning autocomplete
  (`optionsFor()` = seed ∪ saved; **5 most-used pinned**, rest alphabetical). Region has no
  seed list — it learns purely from saved values.
- **Bag Size** = constrained list (`BAG_SIZES`: 100g/250g/350g/1000g/4oz…32oz) + type-other,
  default **250g**; stored as a label, converted to grams on CSV (`bagSizeToGrams`, oz×28.35).
  **# Bags** = a constrained **1–6** tap-to-edit field (FX `bean-bagcount`), default 1. New
  beans also seed the default recipe.
- **Bean★ + Bean Notes** (`bf-rating` cloned from `bean-rating`; `bean-tasting` →
  `tastingNote`) are editable on the form *and* from the brew screen — same stored fields.
  Both render **amber** (they're the bean's two key "verdicts"). Bean Notes is an
  auto-growing textarea capped at **7 lines** then scrolls; **Roaster Notes** likewise caps
  at **2 lines** (`growCapped(el, maxLines)`; `growBeanForm()` sizes both on open). The caps
  keep **save bean** on screen on an iPhone 17 Pro (~11 raw lines fit at 402×874, trimmed
  for the safe areas + the 2-line Roaster Notes).
- **My Notes merged away:** the legacy `myNotes` field was removed from the form (it
  overlapped Bean Notes). Existing `myNotes` data is preserved (`Object.assign` doesn't
  clobber absent keys) and still exported (appended to beans `Comments`).
- **First brew of a bean:** `brewFromBean` sets Brew★ = 1 ("1st") when the bean has no
  saved brews yet.

### Brew history (slide-up overlay — **Brew screen only**)
Header **History** opens `#history-overlay`; its head = **EXPORT · BACKUP · RESTORE · ×**.
- Cards newest-first, compact `dose · TDS · ★` line. **Experiment deltas:** the line also
  appends, in **amber**, any of **Grind / Temp / Contact** that differ from the brew's bean's
  **best recipe** (`recipeDeltas()` vs `liveBean(beanId).best*`) — so a 3★ experiment shows at
  a glance which variable was changed (e.g. `24g · TDS 1.38 · ★3 · Grind 9`). The ★ rating is
  amber too; a fully-standard brew shows no deltas. (Baseline is the bean's best recipe, not a
  global standard — only true deviations from the dialed-in recipe surface.)
- **Tap → action sheet
  Brew · Edit · Delete** (Delete confirmed; Edit disabled on locked brews; Brew always
  enabled). Plain `click` — no long-press.
- **Brew** (`brewFromBrew`) → start a **fresh cup**: coffee + **recipe from that brew's
  snapshot**, but Bean★ + bean note from the **live bean** (latest). ("Remake this cup.")
  Contrast with **Brew-from-bean**, which pulls the recipe from the bean's best recipe.
  Both go through `startBrewWith()` (clears brew-only fields, `editingBrewId=null`).
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
bagSize, bagCount, roasterNotes, myNotes, rating, tastingNote, brewNote,
bestDose/bestGrind/bestAgitate/bestContact/bestWater/bestBloom/bestDecay/bestTarget,
bestRecipeRating, locked, exportedAt, updatedAt`.

### Export model (two paths)
- **EXPORT** (overlay) — full dump of **both** datasets in **ONE file**
  `blackmagic.csv` (`exportCombinedCSV()`): the beans block, a `@@BLACKMAGIC:BEANS@@`
  marker line above it and a `@@BLACKMAGIC:BREWS@@` marker before the brews block.
  One file = one iOS "Save to Files" tap; the Excel macro splits on the markers back
  into the two tables. No locking, re-runnable. (Was two staggered files
  brews.csv/beans.csv pre-v7.) The Excel feed.
- **BACKUP / RESTORE** — full JSON of beans+brews (`exportJSON`/`importJSON`); the
  PWA-reinstall safety net (RESTORE replaces all data).
- (Per-bean export + freeze/lock was **retired** — the global EXPORT is the only feed.)
- Each section carries stable **ID** keys for Excel upsert: beans `ID`; brews `ID` +
  `Bean_ID` (FK). Unit conversions on export: `Time_Aim` = contact secs→min,
  `Pour_Decay` = %→fraction, `Output` = brewTarget. The **beans** block also carries
  the best recipe as
  `Best_Dose/Best_Grind/Best_Temp/Best_Time_Aim/Best_Bloom/Best_Pour_Decay/Best_Agitate/Best_Output`
  (same unit conventions: `Best_Time_Aim` = min, `Best_Pour_Decay` = fraction).

## Excel integration
Workbook `~/Downloads/TFD Coffee Log 2026 Claude.xlsx` (ListObjects `BeanLog`,
`BrewLog`) ingests the export via a VBA **upsert** macro `ImportBlackMagic` (source:
`~/Downloads/BlackMagicImport.bas`; assign it to a sheet button). **One-click, no
prompts:** it reads `blackmagic.csv` from `CSV_FOLDER` (hardcoded to the iCloud folder
`/Users/tfd_2023/Documents/Black Magic Export Restore`, where the phone exports; set
`CSV_FOLDER=""` to use the workbook's own folder) and splits it on the
`@@BLACKMAGIC:BEANS@@`/`@@BLACKMAGIC:BREWS@@` markers (`SplitSections`/`TrimWS`/
`ParseCsv`). Mac sandbox access is granted via `GrantAccessToMultipleFiles` (a
ONE-TIME consent prompt the first run); if the file is missing/denied it falls back
to a manual `GetOpenFilename` picker. Note: the `.bas` is just source — after editing
it you must re-import the module into the workbook (VBE ▸ remove module ▸ Import
File). It matches by app `ID` (stored Text), appends new /
updates existing rows, assigns next `Bag` to new beans, writes only app-input columns
and leaves Excel formula columns alone (Combo_Name, Pour1, EY*/EQV*, and brew
Bag/Country/Roaster derived via `XLOOKUP` on `Bean_ID`). The macro maps **csv→xl** by
parallel `csvH`/`xlH` arrays, so differing names are fine. **Best recipe → BeanLog:**
only `Best_Grind→Grind`, `Best_Temp→Temp`, `Best_Time_Aim→Contact` map in (those are the
only recipe columns BeanLog has — the other dial knobs are held constant); units already
match (Grind ~7–9, Temp °F, Contact min). Bean★ → BeanLog `Rating`: the **production**
workbook renamed its `Grade` column to `Rating`, so the macro's `Rating→Rating` mapping
lands (the stale Downloads copy still says `Grade` — rename it there too if you re-import).
**Mac VBA constraints (cost a lot of debugging):** Excel-for-Mac has NO `FileDialog`,
`Scripting.Dictionary`, or `FileSystemObject` — the macro uses `GrantAccessToMultipleFiles`
+ `GetOpenFilename` (no Win-style filter), VBA `Collection`, and native binary read + a
hand-rolled UTF-8 decoder. **Never open `blackmagic.csv` directly in Excel** — it converts
13-digit IDs to `1.78E+12` and collapses them. Pour1 (geometric first pour) = `Output·(1−r)/(1−r^n)`, `n = Time_Aim/0.5`.

## Phase 3 ideas (not yet started)
- Chart TDS or Rating over time
- Compare brews side by side
- ("Use this recipe to brew now" is **done** — the Brew action on bean/brew cards.)

## Design conventions
Refined via a Claude Design pass; tokens live in `:root` in `index.html`.
White background, black text, with **one** restrained accent.

- **Tokens:** `--ink #0B0B0C` · `--secondary rgba(60,60,67,.6)` ·
  `--tertiary rgba(60,60,67,.34)` · `--hairline rgba(60,60,67,.13)` ·
  `--accent #9A5A2B` (warm amber). **Amber is used on Bean/History (nav), the
  TIME +/− / TDS / Brew★ / Bean★ values, the bean form's Bean★ + Bean Notes (the two
  "verdicts") + its best-recipe values (amber = editable), and the clock's sweep hand** —
  not on the progress arc, the in-dial timer/reset hint, or the action button.
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
