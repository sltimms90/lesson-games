exec(open("links.py").read().split("with sync_playwright() as p:")[0])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180,"height":820})
    T = ctx.new_page(); errs=[]; T.on("pageerror", lambda e: errs.append(str(e))); imgs=[]
    T.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    route(T, imgs); T.goto("https://sltimms90.github.io/lesson-games/app/"); T.wait_for_selector("text=Mia · LP9")
    T.click("text=Mia · LP9"); T.wait_for_timeout(300)
    urls = {}
    for g in ["g1","g2"]:
        T.click("[data-a=slink][data-g=%s]" % g); T.wait_for_selector("#slinkUrl"); urls[g] = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    codes = {}
    for g in ["g1","g2"]:
        S = ctx.new_page(); e=[]; S.on("pageerror", lambda x: e.append(str(x))); route(S, [])
        S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(urls[g]); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.click("[data-a=s-start]"); S.wait_for_timeout(500)
        for i in range(25):
            if S.locator("#res").count(): break
            if g == "g1":
                if S.locator("[data-a=sn-roll]").count(): S.click("[data-a=sn-roll]:not([disabled])", timeout=3000); S.wait_for_timeout(1700)
                else:
                    acts = S.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))")
                    nxt = [a for a in acts if a.startswith("sn-") and a not in ("sn-fix",)]
                    if nxt: S.click("[data-a=%s]:not([disabled])" % nxt[0]); S.wait_for_timeout(600)
                    else: break
            else:
                acts = S.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))")
                cur = S.evaluate("(document.querySelector('.callcol .ball span')||{}).textContent")
                word = S.evaluate("(document.querySelector('.callcol .word, .callcol h2, .callcol .call')||{}).textContent || ''")
                if i == 3: S.screenshot(path="bingo_mid.png")
                tiles = S.locator("[data-a=bg-tap]")
                hit = False
                if word.strip():
                    for k in range(tiles.count()):
                        if tiles.nth(k).inner_text().strip().lower() == word.strip().lower() and "on" not in (tiles.nth(k).get_attribute("class") or ""):
                            tiles.nth(k).click(); hit=True; S.wait_for_timeout(300); break
                acts = S.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))")
                good = [a for a in acts if "ok" in a or "good" in a]
                if good: S.click("[data-a=%s]:not([disabled])" % good[0]); S.wait_for_timeout(300); continue
                if "bg-next" in acts: S.click("[data-a=bg-next]"); S.wait_for_timeout(500)
                elif "finish-ask" in acts and i > 20: S.click("[data-a=finish-ask]"); S.wait_for_timeout(400)
                else:
                    other = [a for a in acts if a not in ("pause","settings","bg-tap")]
                    if other: S.click("[data-a=%s]:not([disabled])" % other[0]); S.wait_for_timeout(400)
        if not S.locator("#res").count():
            acts = S.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))"); print(g, "stuck, actions:", sorted(set(acts))); S.screenshot(path="stuck_%s.png"%g)
            if "finish-ask" in acts:
                S.click("[data-a=finish-ask]"); S.wait_for_timeout(400)
                acts = S.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))"); print(" after finish-ask:", sorted(set(acts)))
                fin = [a for a in acts if a.startswith("finish") and a != "finish-ask"]
                if fin: S.click("[data-a=%s]:not([disabled])" % fin[0]); S.wait_for_timeout(800)
        S.wait_for_function("document.querySelector('#res') && /LGR1\\./.test(document.querySelector('#res').value)", timeout=5000)
        codes[g] = S.input_value("#res"); print(g, "result:", codes[g].splitlines()[0]); S.screenshot(path="done_%s.png"%g)
        print(g, "student errors", e); S.close()
    acts = T.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))")
    for g in ["g1","g2"]:
        T.click("[data-a=sres-open]"); T.fill("#sresIn", codes[g])
        a2 = T.eval_on_selector_all("[data-a]", "els=>els.filter(e=>!e.disabled).map(e=>e.getAttribute('data-a'))"); add=[a for a in a2 if a.startswith("sres-") and a not in ("sres-open","sres-close")]
        T.click("[data-a=%s]" % add[0]); T.wait_for_timeout(600)
    print("saved results:", T.evaluate("Object.values(__MOCK.db.results).map(r=>r.data.title+' | '+(r.data.score&&r.data.score.text))"))
    print("teacher errors", errs)
    b.close()
