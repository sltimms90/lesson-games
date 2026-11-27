# dev/ — tests for Lesson Games (not part of the app)

`tests/` runs the app headless in Chromium (Playwright) against `mock-supabase.js`, a stand-in for
supabase-js: tables, sign-in, storage and Realtime broadcast/presence (via BroadcastChannel, so two
tabs in one browser can play a live game together). Nothing here talks to the real project.

    pip install playwright && playwright install chromium   # or point executable_path at Chrome
    cd dev/tests && python3 run.py      # sign-in, sync, backup/restore, student page
    python3 links.py                    # student links for Bingo, Snakes & Ladders, Higher or Lower
    python3 live.py                     # live games on two screens
    python3 turns.py                    # turn locks
    python3 reject.py                   # the teacher's app undoes a student move on the teacher's turn
    python3 t3.py                       # student folders, override, live Taboo
    python3 fit.py [type ...]           # screen fit: every game, long content, iPad/desktop/phone (shots/ has screenshots)
    python3 cls.py                      # class link: teacher puts games on the student's screen; solo games mirrored
    python3 ch.py                       # Challenge button (Snakes & Ladders, Higher or Lower)
    python3 prog.py                     # missed-words warm-up and the student progress view
    python3 hostile.py                  # crafted links and poisoned live messages never run code; the CSP holds
    python3 review.py                   # review fixes: two teacher devices, save acknowledgement, class ✕, stale tabs
    python3 design.py                   # review design changes: lesson page layout, Hard mode, Undo toast; (24 Nov, from design-tweaks-2)
                                        # editing a game clears its half-played copy, Snakes & Ladders defaults to Reach it or go past, token list after leaving
    python3 bf.py                       # 18 Nov feedback: bingo card each for pairs, called line, print 2-up + teacher, My card; run sheet step merge
    python3 hw.py                       # homework links: Student link results save themselves (submit_homework), refused tokens, offline fallback, New link
    python3 rs_every.py                 # 19 Nov: run sheet opens for every lesson; phone/iPad comfort; home by day; lesson page order; edited games on top
    python3 fix19.py                    # 19 Nov feedback: Look selects, run sheet paste under Advanced, Quick game word source line, spelling size/zoom
    python3 plan.py                     # Plan tab: fetch through plan-doc, device copy + ↻, run sheet jumps, outline, scroll kept, folds, no code from the file, never on student pages
    python3 fb1119b.py                  # 19 Nov evening: Win or lose typed bet + All in (student link, class link), Plan tab HW Key, Open plan / Folder links
    python3 materials.py                # lesson materials: the 📂 Files menu (Open plan, Folder, materials) and per-block chips on the run sheet; bad entries dropped, text only
    python3 tidy.py                     # header and home tidy: 📋 run sheet icon with a state dot, Lesson Desk, › past today, Plan header ☰ · HW Key · 📂 with the fetched chip as refresh
    (22 Nov) one nav bar on every teacher screen: 🏠 Lesson Desk · 👤 student | 🎲 games · 📋 run sheet · 📖 plan · 📂 files, no ‹ arrows;
    the tests above click [data-a=nav-games] / [data-a=rs-open] where they used to click ‹ Games / ‹ back
    python3 phaseb.py                   # Phase B tracker: taught / needs a look / not yet, the 📝 badge on the Lesson Desk, ✅ 🚫 ↶,
                                        # Start-up (everything before a date), a chat's row arriving live, the "LP n Phase B not done yet"
                                        # line, phone/iPad width, backup, students never touch it
    python3 plan1124.py                 # 24 Nov: long "Key — …" headings fold; HW Key finds a key under a homework step (2B · HW27 …);
                                        # Lesson Games “title” in the plan → 🎲 chip that opens the game (back → plan); 📋 on each step /
                                        # segment heading → that run sheet line or block; none of it reaches students (fixtures: plan_1124.py)
                                        # (24 Nov c) no 📋: the step / segment heading itself opens the run sheet (plain tap only);
                                        # HW Key falls back to the previous lesson's HWnn material when the plan has no homework key
                                        # (24 Nov b) BEFORE CLASS "Lesson Games pack <id>: “…” · “…” (note) · …" → chips, stops at the first non-game quote
    python3 tabs.py                     # 25 Nov: the app open in several tabs (games · run sheet · plan): one tab per browser is live,
                                        # the one playing the game ("live in another tab" + Use this tab on another game tab); lesson-page
                                        # tabs only listen (never jump into the game, class bar still right, Play hands the game over);
                                        # a tab that missed moves takes the student's board, never undoes it
    python3 bonus1124.py                # quiz bonus round: shuffle ×0.7 faster each level (700/490/343/240 ms), Reduce Motion 450/360/300 ms;
                                        # new game back to level 1; student link + class link at level 3 same speed, b.pos matches; "Six cards" hint
    python3 openall.py                  # 25 Nov: 📂 Files → Open all (every valid material in order, then the notes doc, as tabs;
                                        # Chrome's pop-up blocker note) and the student's notes doc (students/<slug>.notes_doc, set on
                                        # the student's page: Doc link or bare id → id; junk → error, nothing saved; Remove clears it).
                                        # plan.py's leak check covers notes_doc

    python3 typhoon.py                  # 25 Nov: Typhoon. Editor (fill randomly / shuffle / clear / presets), Quick game, one-screen
                                        # board + Settings → Teacher view; class link: lock → Let them pick → one pick → auto-lock, a tap
                                        # while locked ignored, undo, tally only on the master, swap and swap back; leak test (state, DOM,
                                        # class message, per-game link); fit: iPad board 3×3 / 6×6, phone master
                                        # (26 Nov) against the teacher: Teacher plays too; on Teacher's turn 🎲 Random box or Let them pick
                                        # for me; the turn highlight moves on after each pick; results name whose box it was
    python3 battleships.py              # 25 Nov: Battleships + Finish later. Placement rules, Ready gating, Let them fire / Extra shot /
                                        # Skip my turn, undo a shot, hit / sunk / win, leak test (teacher's unsunk ships), ⚙ Show outlines
                                        # (off after reload and Continue, never sent or saved, student screen unchanged), Finish later →
                                        # next lesson → Continue exactly; Discard; replace prompt; partial + final results; fit iPad/phone/desktop

    python3 td.py                       # 26 Nov: Tower Defence. Setup (map, difficulty), build / upgrade / sell costs, the menu clear of the
                                        # path on every slot, a wave only on ▶ Start wave, ❚❚ / tab hidden / ‹ pause it, auto-pause after a
                                        # wave and the setting off, the wave limit, determinism, ‹ → another game → ▶ Resume exactly, Finish
                                        # later mid-wave → Continue, game over, + Coins, ⚡, undo, live (status screen on Sam's phone, teacher
                                        # pause locks the student, unlock, the student's own pause, coins once, undo), fit iPad/desktop/phone.
                                        # hostile.py has its teacher → student poison cases; fit.py includes it
                                        # (26 Nov, students' feedback) harder Easy/Normal/Hard; Lightning / Gold mine / Laser locked until
                                        # waves 5 / 8 / 12; the 7-tower menu still clear of the path
                                        # (26 Nov, cards round 2) Automatic on/off by difficulty and Sam's setting winning; the two-card offer
                                        # (amounts on the cards), Skip, Take a chance → shuffle → tap → applied once; same seed + tap = same
                                        # result; sizes by wave and difficulty; best tower lost from wave 10; pairing rules; offer and face-down
                                        # cards kept through pause, ‹ / ▶ Resume, Finish later → Continue; status lines; results; fit

    python3 sandbox.py                  # 27 Nov: the test sandbox (test students out of the day list, Students, Phase B owed, missed
                                        # words, Keeps coming up, progress; in backups), 🧪 Test → Reset sandbox (only test students
                                        # touched; the seed has every kind in TYPES), the 🧪 stripe teacher-side only; the class link
                                        # follows EVERY kind onto the student's page (a new kind fails here until it's wired in and
                                        # seeded), with no teacher-only button on the student's screen; an older student page reloads
                                        # itself once (build id), and if it can't, the class bar and pill tell the teacher
    python3 games1127.py                # 27 Nov: Spelling / Matching tiles with modes (old types open as themselves from the lesson
                                        # page, a plan chip, a run sheet row, Resume, a Homework link; Hard mode; Play as; the mode
                                        # remembered per student, a saved type winning; results name the mode), the one + Game picker
                                        # (sections, Words from, More games setting, start screen), card ⋯ menus, the score pad
                                        # (Typhoon tally, TD coins, Undo, read-only board), home's Kept games, Look / Advanced moves; fit

Build id: `build.py` also stamps `APP_B` (a hash of the script). Presence and every live message carry it. A class-link page
that receives a game it can't take (`liveMsgOk` fails) from a different build reloads itself (once per build, once a minute,
`clsReload`); presence alone reloads a waiting page. The teacher's class bar says when the student's page is a different
version, and the pill says when the student's screen hasn't opened the game after 6 s.

Games page (27 Nov): `GROUPS` (Spelling: hangman / anagrams / typeit / spelling; Matching: match / match+pairs / cards) are
tiles over the existing kinds. Saved games keep their own type, so stored data, packs, results, links and the run sheet read
as before; `modeOf(g)` names a game's tile and mode, `rememberMode` keeps the last one per student (`students.data.modes`).
"Play as" adds a converted copy to the lesson (the saved game is never changed). `PICK_SECS` lays out the picker; any kind
not listed lands in More games; `tset().pickMore` is the More games setting. `QUICK` recipes build a game from the chosen
words (`quickStart`); a kind without one opens the editor.

Score pad: `SPAD` / `spadHtml` / `spadHandle`. Typing stays on the screen; + − = and ↺ 0 become the game's own act (`tp-padop`,
`tp-add`, `td-coins` with a signed amount), so Undo and the live screens take them like any tap. Tower Defence grants may be
negative (take away) up to ±`TD_GRANT_MAX` (9999), coins never go below 0; `tdClean` drops anything else.

Test sandbox: `students.data.test === true` (`isTestName` / `isTestPack` / `realPacks`). `SBX_SEED` holds one game of every
kind; `sbxReset` deletes only lessons, results, sheets (`STORE.deleteSheet`), Phase B rows and kept games of flagged students.

Tower Defence (`td`, a single-player break game): `run.st` holds only what's true between waves (map, difficulty, towers,
wave, lives, coins, settings), which is what's saved, kept with Finish later and sent live. The enemies on the path are
`run.sim`, on the screen playing the game only (kept with ‹ / ▶ Resume, never sent). A wave without its sim starts again
from its start (`st.ws`: the lives and coins it began with, plus any building since), so Finish later never keeps half a
wave. `tdStep` is fixed 1/30 s steps with no randomness. Live, the student's screen plays and sends its state (on changes,
at most every 2 s during a wave); the teacher's screen shows a status screen and keeps its own fields (`TD_TFIELDS`: the
pause lock, Stop after each wave, the wave limit, coin grants, the challenge, undo requests), which are all the student's
screen takes from it. Grants have ids, so coins are added once; `tdClean` checks every state before it's drawn or played.
Bonus cards: every 3 waves cleared `tdStep` puts an offer in `st.card` (`tdOffer`: one good and one bad card, each with
its amount, and which side the good one lands on after the shuffle), from `st.seed` and the waves cleared, so nothing is
redrawn after a pause or Continue. `st.card.step`: offer → pick (face down; the shuffle is only an animation) → done.
Every card number is in `TD_CARDTAB` (card × difficulty; sizes step up at `TD_CARDSTEP` waves 5, 10, 15). Next-wave cards set
`st.mod` / `st.modv`, which `tdWave` reads. Cards on/off: `st.cards` true / false, or null = Automatic (off on Easy).
Balance was tuned with simulated players (a good builder that always takes the chance or always skips).

Teacher-owned games (Typhoon, Battleships): the hidden part (Typhoon's boxes, the teacher's fleet) lives in `run.hid` on the
teacher's device only, never in `run.st`, so it's never broadcast, linked or drawn on the student's page. The teacher's screen
takes only what the student's side may do (`TYPES[t].liveIn`: a coordinate, a Ready fleet, Typhoon's master taps while
swapped) and sends its own state back; the student's screen always takes the teacher's (`liveOwnedIn`). `studentLinkData`
sends Typhoon only its size and the bonus meanings in use. Finish later keeps a game on the student's record
(`students/<slug>.data.paused[<type>]`: state + hidden part), so backups, restore and the weekly snapshot carry it; no new
table. The Typhoon bonus list and the Typhoon / Battleships presets are the teacher's settings, in the `students` row `~teacher`.

**After editing `app/index.html`, run `python3 dev/build.py`.** It stamps the Content-Security-Policy with the
script's hash (otherwise the app won't run at all) and copies the app over `index.html`. Tests strip the CSP because
they inject a hook into the script; `hostile.py` checks the real, untouched page.

Every script ends with "N failures". `fit.py` fails only on iPad and desktop; on phones it prints NOTE lines
(very long content on a sideways phone hits the half-size floor). New scripts share helpers in `lg.py`.

`functions/plan-doc/` is the Edge Function behind the Plan tab (deployed as `plan-doc`, verify_jwt off: it checks
`am_i_teacher` with the caller's token itself). It reads the LP file with a Google service account whose JSON key is the
secret `GOOGLE_SA_KEY`; .docx files go through mammoth, native Docs through files.export. It also sends the file's folder
(`folderId`, the first of `parents` from the same metadata call) for the app's Folder link. Test it with Deno:
`deno test --allow-env --allow-read dev/functions/plan-doc/plan_test.ts`. `tests/plan_sample.docx` is a made-up plan in
the LP layout (`make_plan_sample.py`); `tests/plan_sample.html` is the same plan as the function returns it.

`sql/phaseb.sql` is the Phase B table (migration `phaseb`): one row per pack, `{ pack_id, status: done|skip, at, by: chat|manual, note }`,
teacher-only RLS, in the Realtime publication, and copied by the weekly snapshot (`private.take_snapshot`, migration `snapshot_phaseb`). Planning chats write it at the end of Phase B; the 📝 Phase B screen writes `manual` rows.
`mock-supabase.js` keys its `phaseb` rows by `pack_id` and supports `.in()` for the screen's deletes.

`sql/submit_homework.sql` is the database function student pages call to save a homework result (applied to the project as
migrations `submit_homework` and `submit_homework_anon_only`). `mock-supabase.js` has a copy of its checks for the tests.

**Guest accounts and the showcase school (27 Nov).** A guest is an email on `private.guests`; signed in, they get the normal
teacher app scoped to a made-up school: four students with `showcase: true` in their `students` row (never `test`), whose
lessons' ids start `~sc-` (no `slug()` makes `~`). The database enforces it, not the page:

- `sql/guests.sql` (migrations `guest_showcase`, `guest_showcase_student_upsert`, `showcase_plans`): `private.guests`,
  `private.is_guest()` (built like `is_teacher()`), `public.am_i_guest()`, a guest policy on every table (reads and writes
  only showcase rows, `WITH CHECK` on every write, no new or deleted students, no flag changes, a trigger stops a guest
  changing any row's id; boards read-only), the teacher-only `guest_list / guest_add / guest_remove`, and
  `private.showcase_plans` + `public.showcase_plan()` (teacher or guest only). A real lesson naming a showcase student
  switches that student off for guests at once. Sam's "teacher full access" policies are unchanged. `game-pictures` is a
  public bucket; uploads stay teacher-only (the showcase board's picture is already its public address, so a guest never uploads).
- `sql/guests_test.sql`: the real-database test. Run it whole in the SQL editor (or MCP `execute_sql`); it adds throwaway
  fixtures, acts as a guest, a signed-in stranger, anon and Sam through JWT claims, tries every read and write, and always
  rolls itself back by ending with `ALL PASS (n checks)` (or the first `FAIL: …`) raised as an error.
- Plans: `showcase/plans/<docId>.html` are the showcase plans (LP layout, fixed labels). `build.py` writes `showcase/plans.json`
  (what the tests serve) and `sql/showcase_plans.sql` (run it in the SQL editor after changing a plan; its last query lists
  md5s to compare with `plans.json`). `plan-doc` serves `showcase-…` docIds from the database to Sam or a guest, never Drive.
- `functions/guest-account/`: makes the sign-in for an email Sam adds (sign-ups are closed). Teacher only, only for an email
  already on the list, never changes an existing account. `deno test --allow-env dev/functions/guest-account/guest_test.ts`.
- App: `SC_SEED` (one constant, all made up) and `scReset()` (🧪 Test → Reset showcase, and the guest's Reset demo: wipes and
  re-seeds the showcase only). `scopeApply()` turns what the store has (`RAW`) into what the app uses: everything for Sam
  (showcase boards aside), only the showcase for a guest or Sam's Preview as guest. `isAsidePack / isAsideName / isAsideRow`
  keep test and showcase students out of Sam's real work. Material, plan and folder ids starting `showcase-` open
  `showcase.html` (a placeholder page at the site root), never Drive. A guest's teacher settings stay on their device.
  A sign-in after a sign-out in the same page reloads the app, so nothing from the last account stays in memory.

    python3 showcase.py                 # resets (showcase / sandbox never touch each other or real rows), Sam's side, Preview as
                                        # guest, a guest session (only showcase rows; refused writes via mock-supabase.js's copy of
                                        # the rules; New lesson; class link; Reset demo), a signed-in stranger, fit of the stripe/list
    python3 showcase_plans.py           # every link in every seeded plan, as a guest: fixed labels, run sheet ↔ plan both ways,
                                        # game chips in their modes, HW Key (one, menu, last lesson's file), keys and traps fold,
                                        # outline, 📂 Files / Open all / run sheet chips → placeholder; fails on an unknown link type
    python3 fit.py guest                # the guest stripe (home, run sheet, a game screen, Reset demo's question) and the Guests list
