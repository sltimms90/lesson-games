exec(open("live.py").read().split("\nwith sync_playwright() as p:")[0])
seed["packs"]["mia-lp9"]["data"]["games"][2]["options"] = {"turns":"each"}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(viewport={"width":1180,"height":820})
    T = ctx.new_page(); terr=[]; T.on("pageerror", lambda e: terr.append(str(e))); route(T, [])
    T.add_init_script("if(!sessionStorage.mk){sessionStorage.mk=1; window.__MOCK = %s;}" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    T.goto("https://sltimms90.github.io/lesson-games/app/"); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
    menu_click(T, "[data-a=slink][data-g=g3]"); T.wait_for_selector("#slinkUrl"); url = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    S = ctx.new_page(); route(S, []); S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(url); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.wait_for_timeout(400); S.click("[data-a=s-start]"); S.wait_for_timeout(1000)
    # play until it is the Teacher's turn
    for i in range(80):
        if T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name") == "Teacher" and T.evaluate("__T.RUN.st.phase") == "call": break
        for pg in (S, T):
            l = pg.locator("[data-a=hl-call]:not([disabled]), [data-a=hl-next]:not([disabled]), [data-a=hl-newround]:not([disabled])")
            if l.count(): l.first.click(); pg.wait_for_timeout(1800); break
    check(T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name") == "Teacher", "reached the teacher's turn")
    n = T.evaluate("__T.RUN.st.log.length")
    # simulate an OLD student page: switch its lock off and press anyway
    S.evaluate("window.__T.LIVE.peers = 0")
    S.evaluate("document.querySelectorAll('[data-a=hl-call]').forEach(b=>{b.disabled=false})")
    S.click("[data-a=hl-call]"); S.wait_for_timeout(2500)
    check(T.evaluate("__T.RUN.st.log.length") == n and T.evaluate("__T.RUN.st.phase") == "call", "teacher's app ignored the student's move on the teacher's turn")
    check(wait_same(T, S, "hilo"), "student's screen was put back to the teacher's game")
    check(T.evaluate("__T.RUN.st.players[__T.RUN.st.turn].name") == "Teacher", "still the teacher's turn on both")
    T.click("[data-a=hl-call]:not([disabled])"); T.wait_for_timeout(2600)
    check(T.evaluate("__T.RUN.st.log.length") == n + 1 and wait_same(T, S, "hilo"), "teacher then plays normally")
    check(not terr, "errors %s" % terr); b.close()
print("%d failures" % len(fails))
