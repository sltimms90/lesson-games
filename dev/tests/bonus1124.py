"""24 Nov: the quiz bonus round shuffles clearly faster each round.
 - move time 700 → 490 → 343 → 240 ms (×0.7 a level, floor 200); level 1 unchanged; gap = move + 60
 - Reduce Motion: 450 → 360 → 300 → 300 ms (×0.8 a level, floor 300) — slower than normal, but it ramps
 - the level carries through the game and starts again at 1 in a new game
 - live: a student link and a class link at level 3 run the same timings on the student's screen, and the teacher's
   b.pos matches the student's when the cards stop
 - the setup hint says six cards (what is dealt)"""
import json, re, time
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get RUN(){return UI.run},get VIEW(){return UI.view},", 1)

QZ = "\n\n".join(["Q%d: which is right?\n*right %d\nwrong %d\nalso wrong %d" % (i, i, i, i) for i in range(1, 7)])
GS = {"mode":"gameshow", "timer":0, "lifelines":"none", "shuffleAns":False, "shuffleQs":False, "bonus":1}
pack = {"id":"mia-lp9", "student":"Mia Chen", "lp":9, "title":"Mia · LP9", "date":"2026-11-24", "updatedAt":"x",
        "games":[{"id":"gq", "type":"quiz", "title":"Bonus quiz", "block":QZ, "options":GS}], "liveRoom":"0123456789abcdef0123456789abcdef"}
NORMAL, REDUCED = [700, 490, 343, 240], [450, 360, 300, 300]

def stage(pg): return pg.evaluate("__T.RUN && __T.RUN.st.bonus ? __T.RUN.st.bonus.stage + ':' + __T.RUN.st.bonus.n : (__T.RUN ? __T.RUN.st.phase : '')")
def wait_stage(pg, want, t=20):
    end = time.time() + t
    while time.time() < end:
        if stage(pg) == want: return True
        pg.wait_for_timeout(40)
    print("   stuck at", stage(pg), "waiting for", want); return False
def dur(pg):
    """Every .bcard's left/top transition duration in ms (they must all agree)."""
    v = pg.evaluate("[...document.querySelectorAll('.bcard')].map(e => getComputedStyle(e).transitionDuration.split(',').slice(0, 2).map(x => parseFloat(x) * 1000))")
    flat = set(round(x) for d in v for x in d)
    return flat.pop() if len(flat) == 1 else sorted(flat)
def to_bonus(P, n):
    """From a question: answer it, Next → bonus round n."""
    P.wait_for_selector("[data-a=qz-ans]", timeout=8000); P.click("[data-a=qz-ans][data-i='0']"); P.wait_for_timeout(150)
    if P.locator("[data-a=qz-next]").count(): P.click("[data-a=qz-next]")
    return wait_stage(P, "show:%d" % n)
def play_round(P, n, watch=None):
    """Bonus round n: read the shuffle timing (on P and on the watching screen), pick, Next question."""
    out = {}
    wait_stage(P, "shuffle:%d" % n); P.wait_for_timeout(500)
    out["move"] = dur(P)
    gaps = P.evaluate("""() => new Promise(res => { const t = [], o = new MutationObserver(() => t.push(performance.now()));
      document.querySelectorAll('.bcard').forEach(e => o.observe(e, { attributes:true, attributeFilter:['style'] }));
      setTimeout(() => { o.disconnect(); const s = []; let last = -1e9; t.forEach(x => { if (x - last > 30) s.push(x); last = x; }); res(s.slice(1).map((x, i) => Math.round(x - s[i]))); }, 1600); })""")
    out["gap"] = sorted(gaps)[len(gaps) // 2] if gaps else None
    if watch:
        watch.wait_for_timeout(100); out["watch_move"] = dur(watch) if watch.evaluate("!!document.querySelector('.bcard')") else None
    wait_stage(P, "pick:%d" % n)
    out["pos"] = P.evaluate("JSON.stringify(__T.RUN.st.bonus.pos)")
    if watch:
        end = time.time() + 6
        while time.time() < end and watch.evaluate("__T.RUN && __T.RUN.st.bonus ? JSON.stringify(__T.RUN.st.bonus.pos) : ''") != out["pos"]: watch.wait_for_timeout(100)
        out["watch_pos"] = watch.evaluate("__T.RUN && __T.RUN.st.bonus ? JSON.stringify(__T.RUN.st.bonus.pos) : ''")
    P.click(".bcard[data-k='0']"); P.wait_for_selector("[data-a=qz-bonusdone]", timeout=8000); P.click("[data-a=qz-bonusdone]")
    return out
def quit_game(P):
    P.click("[data-a=finish-ask]"); P.click("[data-a=discard]"); P.wait_for_timeout(400)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    for motion, want in (("no-preference", NORMAL), ("reduce", REDUCED)):
        ctx = b.new_context(viewport={"width":1180, "height":820}, reduced_motion=motion)
        T = teacher(ctx, seed_db([pack]), errs); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
        if motion == "no-preference":
            T.click("[data-a=editgame][data-g=gq]"); T.wait_for_selector("#qzBonusF .hint", timeout=5000)
            h = T.inner_text("#qzBonusF .hint"); check("Six cards" in h and "Five" not in h, "the setup hint says six cards: %s" % h[:70])
            check(T.evaluate("__T.RUN") is None, "(editor open, nothing playing)")
            T.click("[data-a=cancelgame]"); T.wait_for_selector("[data-a=play][data-g=gq]"); T.wait_for_timeout(200)
        T.click("[data-a=play][data-g=gq]")
        got = []
        for n in range(1, 5):
            check(to_bonus(T, n), "%s: bonus round %d after question %d" % (motion, n, n))
            got.append(play_round(T, n))
        moves = [g["move"] for g in got]; gaps = [g["gap"] for g in got]
        check(moves == want, "%s: .bcard transition by level %s (want %s)" % (motion, moves, want))
        extra = 60 if motion == "no-preference" else 70
        check(all(g is not None and abs(g - (m + extra)) <= 60 for g, m in zip(gaps, want)), "%s: one swap every move + %d ms (measured %s)" % (motion, extra, gaps))
        quit_game(T)
        # a new game starts at level 1 again
        T.click("[data-a=play][data-g=gq]"); check(to_bonus(T, 1), "%s: a new game's first bonus round is level 1" % motion)
        wait_stage(T, "shuffle:1"); T.wait_for_timeout(400)
        check(dur(T) == want[0], "%s: …at level 1's speed again (%s)" % (motion, dur(T)))
        check(T.locator(".bonus-h").inner_text() == "Bonus round", "…titled 'Bonus round' (no level)")
        quit_game(T); ctx.close()

    # ===== live: student link and class link, level 3 =====
    for kind in ("student link", "class link"):
        ctx = b.new_context(viewport={"width":1180, "height":820})
        db = seed_db([pack], students=[{"id":"mia-chen", "name":"Mia Chen", "token":TOK}])
        T = teacher(ctx, db, errs); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
        if kind == "student link":
            T.click("[data-a=slink][data-g=gq]"); T.wait_for_selector("#slinkUrl"); url = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
            S = ctx.new_page(); S.set_viewport_size({"width":390, "height":844}); S.on("pageerror", lambda e: errs.append("S: " + str(e))); route(S)
            S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(url); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.wait_for_timeout(400)
            S.click("[data-a=s-start]")
        else:
            T.click("#clsBar [data-a=clink]"); T.wait_for_selector("#slinkUrl"); url = T.input_value("#slinkUrl"); T.click("[data-a=clink-close]")
            S = student(ctx, url, errs); S.wait_for_timeout(900)
            T.click("[data-a=play][data-g=gq]")
        S.wait_for_selector("[data-a=qz-ans]", timeout=8000); T.wait_for_timeout(800)
        for n in range(1, 4):
            check(to_bonus(S, n), "%s: bonus round %d on the student's screen" % (kind, n))
            r = play_round(S, n, watch=T)
            if n == 3:
                check(r["move"] == NORMAL[2], "%s: level 3 on the student's screen moves at %s ms (want 343)" % (kind, r["move"]))
                check(r["gap"] is not None and abs(r["gap"] - 403) <= 60, "%s: …one swap every ~403 ms (%s)" % (kind, r["gap"]))
                check(r["watch_move"] in (None, NORMAL[2]), "%s: the teacher's screen draws the cards at the same speed (%s)" % (kind, r["watch_move"]))
                check(r["watch_pos"] == r["pos"], "%s: when the cards stop, the teacher's b.pos matches the student's (%s / %s)" % (kind, r["watch_pos"], r["pos"]))
        S.close(); T.close(); ctx.close()
    check(not errs, "no page errors %s" % errs[:3])
done()
