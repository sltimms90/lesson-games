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
    python3 design.py                   # review design changes: lesson page layout, Hard mode, Undo toast
    python3 bf.py                       # 18 Nov feedback: bingo card each for pairs, called line, print 2-up + teacher, My card; run sheet step merge
    python3 hw.py                       # homework links: Student link results save themselves (submit_homework), refused tokens, offline fallback, New link
    python3 rs_every.py                 # 19 Nov: run sheet opens for every lesson; phone/iPad comfort; home by day; lesson page order; edited games on top
    python3 fix19.py                    # 19 Nov feedback: Look selects, run sheet paste under Advanced, Quick game word source line, spelling size/zoom
    python3 plan.py                     # Plan tab: fetch through plan-doc, device copy + ↻, run sheet jumps, outline, scroll kept, folds, no code from the file, never on student pages
    python3 fb1119b.py                  # 19 Nov evening: Win or lose typed bet + All in (student link, class link), Plan tab HW Key, Open plan / Folder links
    python3 materials.py                # lesson materials: the 🗂 Files menu (Open plan, Folder, materials) and per-block chips on the run sheet; bad entries dropped, text only

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

`sql/submit_homework.sql` is the database function student pages call to save a homework result (applied to the project as
migrations `submit_homework` and `submit_homework_anon_only`). `mock-supabase.js` has a copy of its checks for the tests.
