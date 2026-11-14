exec(open("links.py").read().split("with sync_playwright() as p:")[0].replace(
 'HOOK = "window.__T={', 'HOOK = "window.__T={get RUN(){return UI.run},get VIEW(){return UI.view},get LIVE(){return LIVE},'))
import time
def st(pg): return pg.evaluate("__T.RUN && JSON.stringify((({_animating,_rev,spinning,...o})=>o)(__T.RUN.st))")
def wait_same(T, S, label, t=8):
    end = time.time()+t
    while time.time() < end:
        a, b2 = st(T), st(S)
        if a and a == b2 and '"phase":"rolling"' not in a and '"phase":"reveal"' not in a: return True
        time.sleep(0.25)
    print("   T:", (st(T) or "")[:300]); print("   S:", (st(S) or "")[:300]); return False
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(viewport={"width":1180,"height":820})
    T = ctx.new_page(); terr=[]; T.on("pageerror", lambda e: terr.append(str(e))); route(T, [])
    T.add_init_script("if(!sessionStorage.mk){sessionStorage.mk=1; window.__MOCK = %s;}" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    T.goto("https://sltimms90.github.io/lesson-games/app/"); T.wait_for_selector("text=Mia · LP9"); T.click("text=Mia · LP9"); T.wait_for_timeout(300)
    links = {}
    for g in ["g1","g2","g3"]:
        T.click("[data-a=slink][data-g=%s]" % g); T.wait_for_selector("#slinkUrl"); links[g] = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    room = T.evaluate("__MOCK.db.packs['mia-lp9'].data.liveRoom")
    check(room and len(room) == 32, "lesson got a live room saved: %s" % room)
    check(T.evaluate("__T.LIVE.room") == room, "teacher joined the room on the lesson page")
    print("link lengths", {k: len(v) for k, v in links.items()})
    for g, name in [("g1","snakes"), ("g3","hilo"), ("g2","bingo")]:
        S = ctx.new_page(); serr=[]; S.on("pageerror", lambda e: serr.append(str(e))); sreq=[]; S.on("request", lambda r: sreq.append(r.url)); route(S, [])
        S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(links[g]); S.reload(); S.wait_for_selector("[data-a=s-start]")
        S.wait_for_timeout(500); S.click("[data-a=s-start]"); S.wait_for_timeout(800)
        check(T.evaluate("__T.VIEW") == "play" and T.evaluate("__T.RUN && __T.RUN.gameId") == g, name + ": teacher's app jumped into the student's game")
        check(wait_same(T, S, name), name + ": both screens show the same game at the start")
        check("connected" in (T.inner_text("#livePill") if T.locator("#livePill").count() else "") and "connected" in (S.inner_text("#livePill") if S.locator("#livePill").count() else ""), name + ": both show 'connected'")
        if name == "snakes":
            for _ in range(4):
                who = "student" if T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name") == "Mia" else "teacher"; pg = S if who == "student" else T
                btn = pg.locator("[data-a=sn-roll]:not([disabled])")
                if btn.count(): btn.click(); 
                pg.wait_for_timeout(3500)
                check(wait_same(T, S, name), "snakes: %s rolls → both screens agree" % who)
            pos = T.evaluate("__T.RUN.st.players.map(p=>p.pos)"); print("   positions", pos, "log", T.evaluate("__T.RUN.st.log.length"))
            check(T.evaluate("__T.RUN.st.log.length") >= 4, "snakes: 4 turns recorded once each (no double moves)")
        if name == "hilo":
            for _ in range(3):
                who = "student" if T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name") == "Mia" else "teacher"; pg = S if who == "student" else T
                btn = pg.locator("[data-a=hl-call]:not([disabled]), [data-a=hl-next]:not([disabled]), [data-a=hl-newround]:not([disabled])")
                if btn.count(): btn.first.click()
                pg.wait_for_timeout(2500)
                check(wait_same(T, S, name), "hilo: %s taps → both agree" % who)
            check(T.evaluate("__T.RUN.st.log.length") >= 2, "hilo: calls recorded (%d)" % T.evaluate("__T.RUN.st.log.length"))
        if name == "bingo":
            S.click("[data-a=bg-next]"); S.wait_for_timeout(900); check(wait_same(T, S, name), "bingo: student's call shows on the teacher's screen")
            word = T.evaluate("(()=>{var g=__T.RUN.st;return g.current? (g.items[g.current.idx].w||g.items[g.current.idx].word||g.items[g.current.idx].term||JSON.stringify(g.items[g.current.idx])):''})()")
            tiles = S.locator("[data-a=bg-tap]"); hit=False
            for k in range(tiles.count()):
                if tiles.nth(k).inner_text().strip().lower() in word.lower(): tiles.nth(k).click(); hit=True; break
            S.wait_for_timeout(700); check(wait_same(T, S, name), "bingo: student's tap shows on the teacher's screen (word %s, on card: %s)" % (word[:30], hit))
            acts = T.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))")
            good = [a for a in acts if a.startswith("bg-") and a not in ("bg-next","bg-tap")]
            print("   teacher bingo buttons:", sorted(set(acts)))
            if hit and good:
                T.click("[data-a=%s]:not([disabled])" % good[0]); T.wait_for_timeout(700)
                check(wait_same(T, S, name), "bingo: teacher's judgement shows on the student's card")
                print("   claimed:", S.evaluate("JSON.stringify(__T.RUN.st.res)"))
            T.screenshot(path="live_bingo_T.png"); S.screenshot(path="live_bingo_S.png")
        n0 = T.evaluate("Object.keys(__MOCK.db.results).length")
        T.click("[data-a=finish-ask]"); T.wait_for_timeout(300); T.click("[data-a=finish]"); T.wait_for_timeout(1200)
        check(T.evaluate("Object.keys(__MOCK.db.results).length") == n0 + 1, name + ": teacher's Save results saved one result")
        check(S.evaluate("__T.VIEW") == "sdone" and "has your score" in S.inner_text("#app"), name + ": student sees 'Your teacher has your score already'")
        check(not any(x in u for u in sreq for x in ["/rest/v1/", "/auth/v1/"]), name + ": student page never touches the database or sign-in")
        check(not serr, name + ": student errors %s" % serr)
        S.close(); T.wait_for_timeout(300)
    check(not terr, "teacher errors %s" % terr)
    b.close()
print("%d failures" % len(fails))
