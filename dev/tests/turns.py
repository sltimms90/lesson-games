exec(open("live.py").read().split("\nwith sync_playwright() as p:")[0])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(viewport={"width":1180,"height":820})
    T = ctx.new_page(); terr=[]; T.on("pageerror", lambda e: terr.append(str(e))); route(T, [])
    T.add_init_script("if(!sessionStorage.mk){sessionStorage.mk=1; window.__MOCK = %s;}" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    T.goto("https://sltimms90.github.io/lesson-games/app/"); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
    links = {}
    for g in ["g1","g2","g3"]:
        T.click("[data-a=slink][data-g=%s]" % g); T.wait_for_selector("#slinkUrl"); links[g] = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    def roll_btn(pg, a): 
        l = pg.locator("[data-a=%s]" % a); return l.count() and not l.first.is_disabled()
    for g, name, act in [("g1","snakes","sn-roll"), ("g3","hilo","hl-call")]:
        S = ctx.new_page(); serr=[]; S.on("pageerror", lambda e: serr.append(str(e))); route(S, [])
        S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(links[g]); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.wait_for_timeout(400); S.click("[data-a=s-start]"); S.wait_for_timeout(1000)
        for rnd in range(3):
            turn = T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name")
            s_can, t_can = roll_btn(S, act), roll_btn(T, act)
            check((turn == "Mia") == bool(s_can) and (turn != "Mia") == bool(t_can), "%s: %s's turn → student button %s, teacher button %s" % (name, turn, "on" if s_can else "off", "on" if t_can else "off"))
            print("   pills:", S.inner_text("#livePill"), "|", T.inner_text("#livePill"))
            before = T.evaluate("__T.RUN.st.log.length")
            wrong = T if turn == "Mia" else S
            wrong.keyboard.press("h" if name == "hilo" else "Enter"); wrong.wait_for_timeout(600)
            check(T.evaluate("__T.RUN.st.log.length") == before and T.evaluate("__T.RUN.st.phase") in ("roll","call"), name + ": keyboard on the wrong screen does nothing")
            right = S if turn == "Mia" else T
            right.click("[data-a=%s]" % act + (":not([disabled])")); right.wait_for_timeout(3600 if name=="snakes" else 2600)
            if name == "hilo":
                nxt = T.evaluate("(()=>{const s=__T.RUN.st; return s.phase==='result' && s.players.length>1 ? s.players[(s.turn+1)%s.players.length].name : ''})()")
                passing = T.evaluate("!!document.querySelector('[data-a=hl-next]') && /Now it/.test(document.querySelector('[data-a=hl-next]').textContent)")
                if passing:
                    taker = S if nxt == "Mia" else T; other = T if taker is S else S
                    check(taker.locator("[data-a=hl-next]:not([disabled])").count() == 1 and other.locator("[data-a=hl-next]:not([disabled])").count() == 0, "hilo: %s (whose turn it becomes) taps Now it's my turn, not the other screen" % nxt)
                    taker.click("[data-a=hl-next]:not([disabled])"); taker.wait_for_timeout(800)
                else:
                    nx = right.locator("[data-a=hl-next]:not([disabled])")
                    if nx.count(): nx.click(); right.wait_for_timeout(800)
            check(wait_same(T, S, name), name + ": still in step after %s plays" % turn)
        S.close(); T.wait_for_timeout(500)
        print("   after close: peers", T.evaluate("__T.LIVE.peers"), "notmine", T.locator(".notmine").count(), "phase", T.evaluate("__T.RUN.st.phase"), "turn", T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name"), [T.locator(".notmine").nth(i).get_attribute("data-a") for i in range(T.locator(".notmine").count())])
        check(not T.locator(".notmine").count(), name + ": student gone → teacher's buttons unlock")
        T.click("[data-a=finish-ask]"); T.wait_for_timeout(300); T.click("[data-a=discard]"); T.wait_for_timeout(500)
        check(not serr, name + " student errors %s" % serr)
    # bingo: judging only on teacher
    S = ctx.new_page(); route(S, []); S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(links["g2"]); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.wait_for_timeout(400); S.click("[data-a=s-start]"); S.wait_for_timeout(1000)
    for i in range(10):
        S.click("[data-a=bg-next]"); S.wait_for_timeout(700)
        word = T.evaluate("(()=>{var g=__T.RUN.st,it=g.current&&g.items[g.current.idx];return it?(it.w||it.word||''):''})()")
        tl = S.locator("[data-a=bg-tap]"); hit = False
        for k in range(tl.count()):
            if tl.nth(k).inner_text().strip().lower() == word.lower(): tl.nth(k).click(); hit = True; break
        if hit: break
    S.wait_for_timeout(700)
    check(S.locator("[data-a=bg-res]").count() == 0 and "Say your sentence" in S.inner_text("#app"), "bingo: student sees 'Say your sentence to your teacher' instead of the buttons")
    check(T.locator("[data-a=bg-res]").count() == 2, "bingo: teacher has Good sentence / Not right yet")
    S.screenshot(path="turn_bingo_S.png")
    check(not terr, "teacher errors %s" % terr)
    b.close()
print("%d failures" % len(fails))
