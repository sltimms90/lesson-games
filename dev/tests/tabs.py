"""25 Nov: the teacher's app open in two tabs on one lesson. Before, both tabs joined the live game, the one not in use
kept an old board, and on its "turn" it undid the student's moves with that old board, so the student's screen went out
of sync. Now only the tab in front is live; the other says so and leaves the room until it's looked at again.
Also: a screen that missed moves takes the student's newer board instead of undoing it."""
import time
from lg import *
pack = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-15","updatedAt":"x","liveRoom":"0123456789abcdef0123456789abcdef",
        "games":[{"id":"g2","type":"snakes","title":"Race","block":"Mia\nTeacher","options":{"boardId":"b1","auto":True}}]}
db = seed_db([pack])
ST = "(()=>__T.UI.run && JSON.stringify((({_animating,_rev,spinning,...o})=>o)(__T.UI.run.st)))()"
def st(pg): return pg.evaluate(ST)
def pos(pg): return pg.evaluate("__T.UI.run && __T.UI.run.st.players.map(p=>p.pos)")
def pill(pg): return pg.inner_text("#livePill") if pg.locator("#livePill").count() else ""
def same(a, b, t=6):
    end = time.time() + t
    while time.time() < end:
        x, y = st(a), st(b)
        if x and x == y and '"rolling"' not in x: return True
        time.sleep(0.25)
    return False
def front(pg): pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(1200)
def turn(T, S):
    pg = S if T.evaluate("__T.UI.run.st.players[__T.UI.run.st.turn].name") == "Mia" else T
    b = pg.locator("[data-a=sn-roll]:not([disabled])"); ok = b.count() > 0
    if ok: b.click()
    pg.wait_for_timeout(3800); return ok
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(viewport={"width":1180,"height":820}); errs = []
    A = teacher(ctx, db, errs); go_lesson(A, "Mia · LP9"); A.wait_for_timeout(400)
    A.click("#clsBar [data-a=clink]"); A.wait_for_selector("#slinkUrl"); curl = A.input_value("#slinkUrl"); A.click("[data-a=clink-close]")
    S = student(ctx, curl, errs); S.wait_for_timeout(900)
    A.click("[data-a=play][data-g=g2]"); S.wait_for_selector(".sn-board", timeout=6000); A.wait_for_timeout(600)
    for _ in range(2): turn(A, S)
    check(same(A, S), "one tab: both screens agree")
    B = teacher(ctx, db, errs); B.wait_for_timeout(2500)   # a second tab of the app reopens on the same game, in front
    check(B.evaluate("__T.UI.view") == "play" and "live in another tab" in pill(A), "the second tab is live; the first says 'live in another tab': %s" % pill(A))
    check(A.locator("[data-a=sn-roll]:not([disabled])").count() == 0 and A.locator("[data-a=live-here]").count() == 1, "the first tab can't roll, and offers Use this tab")
    check(same(B, S), "second tab and student agree")
    front(A)
    check("connected" in pill(A) and "live in another tab" in pill(B) and same(A, S), "back to the first tab: it's live again and matches the student")
    stale = pos(B); agree = True
    for _ in range(5): turn(A, S); agree = agree and same(A, S, 3)
    check(agree, "five turns, student and the live tab agree every time (before: the student's board jumped back each turn)")
    check(pos(B) == stale, "the tab not in use doesn't touch the game")
    front(B)
    check(same(B, S) and pos(B) != stale and "live in another tab" in pill(A), "the stale tab, back in front, takes the student's newer board (not its own old one)")
    for _ in range(2): turn(B, S)
    check(same(B, S), "and play carries on in sync")
    B.click("[data-a=live-here]") if B.locator("[data-a=live-here]").count() else None
    A.click("[data-a=live-here]"); A.wait_for_timeout(1200)
    check("connected" in pill(A) and same(A, S), "Use this tab hands the game back to the first tab")
    check(not errs, "no page errors %s" % errs)
    done()
