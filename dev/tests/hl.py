exec(open("links.py").read().split("with sync_playwright() as p:")[0])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(viewport={"width":1180,"height":820})
    T = ctx.new_page(); route(T, []); T.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    T.goto("https://sltimms90.github.io/lesson-games/app/"); T.wait_for_selector("text=Mia · LP9"); T.click("text=Mia · LP9"); T.wait_for_timeout(300)
    T.click("[data-a=slink][data-g=g3]"); T.wait_for_selector("#slinkUrl"); url = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    S = ctx.new_page(); e=[]; S.on("pageerror", lambda x: e.append(str(x))); route(S, [])
    S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(url); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.click("[data-a=s-start]"); S.wait_for_timeout(500)
    for i in range(8):
        btn = S.locator("[data-a=hl-call]:not([disabled])")
        if btn.count(): btn.first.click(); S.wait_for_timeout(700)
    S.screenshot(path="hilo_mid.png")
    S.click("[data-a=finish-ask]"); S.wait_for_timeout(300); S.click("[data-a=finish]"); 
    S.wait_for_function("document.querySelector('#res') && /LGR1\\./.test(document.querySelector('#res').value)", timeout=5000)
    code = S.input_value("#res"); print(code.splitlines()[0]); print("errors", e)
    T.click("[data-a=sres-open]"); T.fill("#sresIn", code)
    a2 = T.eval_on_selector_all("[data-a]", "els=>els.map(e=>e.getAttribute('data-a'))"); add=[a for a in a2 if a.startswith("sres-") and a not in ("sres-open","sres-close")]
    T.click("[data-a=%s]" % add[0]); T.wait_for_timeout(500)
    print(T.evaluate("Object.values(__MOCK.db.results).map(r=>r.data.title+' | '+(r.data.score&&r.data.score.text))"))
    b.close()
