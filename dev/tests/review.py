"""Fixes from the independent review (15 Nov 2026): H1 two teacher devices, H2 save acknowledgement,
M1 the student can't end a class game, M2 a stale student tab doesn't lock turn games."""
import json
from lg import *
games = [
  {"id":"g1","type":"hangman","title":"Words","block":"cat\ndog","options":{}},
  {"id":"g2","type":"snakes","title":"Race","block":"Mia\nTeacher","options":{"boardId":"b1","auto":True}},
  {"id":"g3","type":"cards","title":"Rooms","block":"a room where you cook = kitchen\nyou sleep here = bedroom","options":{}},
]
pack = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-15","updatedAt":"x","games":games,"liveRoom":"0123456789abcdef0123456789abcdef"}
db = seed_db([pack])
def open_lesson(pg):
    pg.wait_for_selector("text=Mia · LP9", timeout=8000); pg.click("text=Mia · LP9"); pg.wait_for_timeout(400)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    # H1: two of the teacher's own devices on one lesson, no student
    A = teacher(ctx, db, errs); open_lesson(A); B = teacher(ctx, db, errs); open_lesson(B)
    A.click("[data-a=play][data-g=g1]"); A.wait_for_timeout(900)
    check(A.evaluate("__T.LIVE.peers") == 0 and B.evaluate("__T.LIVE.peers") == 0, "the other teacher device isn't counted as a student")
    check(B.evaluate("__T.UI.view") == "pack", "device B isn't pulled into A's game")
    A.click("[data-a=hm-key][data-c=c]"); A.wait_for_timeout(300)
    check(A.evaluate("__T.UI.run.st.guessed.length") == 1 and A.locator(".ro").count() == 0, "device A plays normally, nothing read-only")
    A.click("[data-a=finish-ask]"); A.click("[data-a=finish]"); A.wait_for_timeout(700)
    check(B.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1').length") <= 1 and A.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1').length") == 1, "Save on A doesn't make B save a second copy")
    B.close(); A.click("[data-a=backlesson]"); A.wait_for_timeout(300)
    # M2: a per-game Hangman link left open doesn't lock Snakes & Ladders on the teacher's screen
    A.click("[data-a=slink][data-g=g1]"); A.wait_for_selector("#slinkUrl", timeout=5000); hurl = A.input_value("#slinkUrl"); A.click("[data-a=slink-close]")
    H = student(ctx, hurl, errs); H.wait_for_timeout(900)
    A.click("[data-a=play][data-g=g2]"); A.wait_for_timeout(600)
    check(A.evaluate("__T.LIVE.peers") == 1 and A.locator("[data-a=sn-roll]:not([disabled])").count() >= 1, "stale per-game tab: Roll still works on the teacher's screen")
    pill = A.inner_text("#livePill") if A.locator("#livePill").count() else ""
    check("🔒" not in pill and A.locator("#livePill [data-a=live-override]").count() == 0 and "not in this game" in pill, "stale tab: the pill says online, not in this game, with no 🔒: %s" % pill)
    A.click("[data-a=finish-ask]"); A.click("[data-a=discard]"); A.wait_for_timeout(300)
    # H2: the student plays a per-game link and saves while the teacher is elsewhere
    H.click("[data-a=s-start]"); A.wait_for_timeout(1200)
    if A.evaluate("__T.UI.view") == "play":   # the teacher's app joined the student's game; go elsewhere
        A.click("[data-a=lesson]"); A.wait_for_timeout(300)
    A.click("[data-a=play][data-g=g3]"); A.wait_for_timeout(500)   # teacher is now in a different game
    for i in range(2):
        H.click("[data-a=hm-show]"); H.wait_for_timeout(200); H.click("[data-a=hm-next]"); H.wait_for_timeout(500)
    H.wait_for_timeout(800)
    check(A.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1').length") == 2, "teacher saved the student's game while in another game")
    check("Your teacher has your score" in H.inner_text("#app"), "student told 'already' only after the teacher saved")
    # ... and with no teacher listening, the student gets the result code, not 'already'
    A.click("[data-a=finish-ask]"); A.click("[data-a=discard]"); A.wait_for_timeout(300); A.click("[data-a=home]") if A.locator("[data-a=home]").count() else None
    A.close(); H.wait_for_timeout(600)
    H.evaluate("document.querySelector('[data-a=s-start]').click()"); H.wait_for_timeout(400)
    for i in range(2):
        H.click("[data-a=hm-show]"); H.wait_for_timeout(200); H.click("[data-a=hm-next]"); H.wait_for_timeout(400)
    H.wait_for_timeout(1200)
    check("Your teacher has your score" not in H.inner_text("#app") and "LGR1." in H.input_value("#res"), "no teacher connected: the student sees the result code")
    H.close()
    # M1: on a class link the student has no ✕, so can't end the teacher's game
    T = teacher(ctx, db, errs); open_lesson(T)
    T.click("#clsBar [data-a=clink]"); T.wait_for_selector("#slinkUrl"); curl = T.input_value("#slinkUrl"); T.click("[data-a=clink-close]")
    S = student(ctx, curl, errs); S.wait_for_timeout(900)
    T.click("[data-a=play][data-g=g2]"); S.wait_for_selector(".sn-board", timeout=6000)
    check(S.locator("[data-a=finish-ask]").count() == 0 and S.locator("[data-a=settings]").count() == 1, "class-link student has no ✕")
    check(T.locator("[data-a=finish-ask]").count() == 1, "teacher still has ✕")
    # Re-check 2: two teacher devices on the lesson page, a student plays a per-game link and saves: one result, not two
    T.click("[data-a=finish-ask]"); T.click("[data-a=discard]"); T.wait_for_timeout(300); S.close()
    T2 = teacher(ctx, db, errs); open_lesson(T2)
    T.click("[data-a=slink][data-g=g1]"); T.wait_for_selector("#slinkUrl", timeout=5000); hurl2 = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    for pgx in (T, T2):
        if pgx.evaluate("__T.UI.view") != "pack": pgx.evaluate("__T.UI.view = 'pack'")
    H2 = student(ctx, hurl2, errs); H2.wait_for_timeout(900); H2.click("[data-a=s-start]"); T.wait_for_timeout(1200)
    for pgx in (T, T2):
        if pgx.evaluate("__T.UI.view") == "play": pgx.click("[data-a=lesson]"); pgx.wait_for_timeout(300)
    for i in range(2):
        H2.click("[data-a=hm-show]"); H2.wait_for_timeout(200); H2.click("[data-a=hm-next]"); H2.wait_for_timeout(500)
    H2.wait_for_timeout(1500)
    gen = H2.evaluate("__T.UI.lastResult && __T.UI.lastResult.gen")
    ids = set()
    for pgx in (T, T2):
        ids |= set(pgx.evaluate("(g) => Object.values(__MOCK.db.results).filter(r => (r.data || r).liveGen === g).map(r => (r.data || r).id || r.id)", gen))
    check(gen and len(ids) == 1, "a student's Save with two teacher devices in the lesson makes one result: %s" % sorted(ids))
    check("Your teacher has your score" in H2.inner_text("#app"), "and the student is told the teacher has it")
    check(not errs, "no page errors %s" % errs[:3])
done()
