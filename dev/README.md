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

Every script ends with "N failures". `fit.py` fails only on iPad and desktop; on phones it prints NOTE lines
(very long content on a sideways phone hits the half-size floor). New scripts share helpers in `lg.py`. `links.py` has one known false failure ("student sees your
board picture": wrong selector; the screenshot shows the board).
