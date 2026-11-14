"""Hostile input (review C1/C2): crafted student links and poisoned live messages must never run code.
Every string in the state becomes markup, every number a quote-breaking string; nothing may execute or appear as a tag."""
import json, os
from lg import *
src = open(os.path.join(HERE, "fit.py")).read()
exec(src.split("VIEWS =")[0].split("from lg import *")[1])  # blocks: one long game of every type
EVIL = '<img src=x onerror="window.__pwn=1">'
EVILN = '1" onerror="window.__pwn=1'
games = [{"id":"g_" + t, "type":t, "title":t, "block":b, "options":({"boardId":"b1"} if t == "snakes" else {})} for t, b in blocks.items()]
pack = {"id":"mia-lp9", "student":"Mia", "lp":9, "title":"Mia · LP9", "date":"2026-11-15", "updatedAt":"x", "games":games, "liveRoom":"0123456789abcdef0123456789abcdef"}
POISON = """([mode, evil, eviln]) => {
  const L = __T.LIVE, run = __T.UI.run; if (!run || !L.chan) return 'no run';
  const walk = v => Array.isArray(v) ? (v.length ? v.map(walk) : [evil]) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x)])) : typeof v === 'string' ? evil : typeof v === 'number' ? (mode === 'num' ? eviln : v) : v;
  const st = walk(JSON.parse(JSON.stringify(run.st))); st._rev = (run.st._rev || 0) + 50;
  L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:run.gameId, p:run.packId, gen:run.liveGen, t0:run.liveT0, rev:st._rev, st:st, title:evil, from:'zzzz' } });
  return 'sent';
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    # C2: a crafted Snakes & Ladders link, opened where the teacher is signed in
    s0 = student(ctx, "https://sltimms90.github.io/lesson-games/", errs); s0.wait_for_timeout(500)
    s0.evaluate("localStorage.setItem('lessonGames.auth', 'SECRET')")
    code = s0.evaluate("""(async () => __T.packData({ v:20261113, p:'x', g:{ id:'g1', type:'snakes', title:'Race', block:'Mia\\nTeacher', options:{ boardId:'evil' } },
        x:{ board:{ id:'evil', img:'x" onerror="window.__pwn=localStorage.getItem(\\'lessonGames.auth\\')', w:600, h:600, rows:10, cols:10 }, tokens:{ Mia:'y" onerror="window.__pwn=2' } } }))()""")
    s0.goto("https://sltimms90.github.io/lesson-games/#s=" + code); s0.wait_for_timeout(600)
    if s0.locator("[data-a=s-start]").count(): s0.click("[data-a=s-start]"); s0.wait_for_timeout(800)
    check(s0.evaluate("window.__pwn") is None, "crafted board/token picture addresses don't run code (%s)" % s0.evaluate("window.__pwn"))
    check(s0.locator("img[src='x'], img[src='y']").count() == 0, "foreign picture addresses are dropped")
    s0.close()
    # C1: poisoned live state, every game type, both kinds of poison
    t = teacher(ctx, seed_db([pack]), errs); t.wait_for_selector("text=Mia · LP9", timeout=8000); t.click("text=Mia · LP9"); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); url = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    s = student(ctx, url, errs); s.wait_for_timeout(900)
    for g in games:
        t.click("[data-a=play][data-g=%s]" % g["id"]); t.wait_for_timeout(300)
        if t.evaluate("__T.UI.view") != "play": check(False, "%s didn't start" % g["type"]); continue
        s.wait_for_function("() => __T.UI.run && __T.UI.run.gameId === '%s'" % g["id"], timeout=6000); t.wait_for_timeout(300)
        for mode in ("str", "num"):
            r = s.evaluate(POISON, [mode, EVIL, EVILN]); t.wait_for_timeout(500)
            pwn = t.evaluate("window.__pwn"); tags = t.locator("#app img[src='x']").count()
            check(pwn is None and tags == 0 and t.evaluate("__T.UI.view") == "play", "%s (%s poison, %s): teacher safe" % (g["type"], mode, r))
        t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    check(not [e for e in errs if "pwn" in e], "no errors from the poison %s" % errs[:3])
    # the real page, untouched: it runs under its CSP, and injected inline code is blocked
    raw = open(ROOT + "/index.html", encoding="utf-8").read()
    c = b.new_context(); pg = c.new_page(); perr = []; pg.on("pageerror", lambda e: perr.append(str(e)))
    pg.route("**/*", lambda r: r.fulfill(body=raw, content_type="text/html") if "/lesson-games/" in r.request.url and not r.request.url.endswith(".js") else (r.fulfill(body=MOCK, content_type="application/javascript") if r.request.url.endswith("supabase.js") else r.abort()))
    pg.goto("https://sltimms90.github.io/lesson-games/"); pg.wait_for_timeout(600)
    check("Ask your teacher for a game link" in pg.inner_text("#app"), "the real student page runs under its CSP")
    pg.evaluate("""document.body.insertAdjacentHTML('beforeend', '<img src="x" onerror="window.__csp=1">')"""); pg.wait_for_timeout(400)
    check(pg.evaluate("window.__csp") is None, "CSP blocks an injected onerror= handler")
    pg.goto("https://sltimms90.github.io/lesson-games/app/"); pg.wait_for_timeout(1200)
    check(pg.locator("#sbEmail").count() == 1, "the real teacher app runs under its CSP (sign-in screen)")
    check(not perr, "no errors on the real page %s" % perr[:2])
done()
