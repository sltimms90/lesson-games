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
    t = teacher(ctx, seed_db([pack]), errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
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
    # Tower Defence, the other way: the teacher's fields arriving at the student's screen. Coins only as whole numbers
    # within the cap, each grant once; nothing else of the student's game is taken; a wrong kind drops the message.
    t.click("[data-a=play][data-g=g_td]"); s.wait_for_function("() => __T.UI.run && __T.UI.run.gameId === 'g_td'", timeout=6000); t.wait_for_timeout(400)
    if s.locator("[data-a=td-go]").count(): s.click("[data-a=td-go]"); t.wait_for_timeout(500)
    TSEND = """([over, evil]) => { const run = __T.UI.run, L = __T.LIVE, st = JSON.parse(JSON.stringify(run.st)); Object.assign(st, over);
      if (st.ch === 'EVIL') st.ch = { q: evil, w: evil };
      L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:run.gameId, p:run.packId, gen:run.liveGen, t0:run.liveT0, rev:(run.st._rev || 0) + 100, st:st, title:'x', from:'zzzz', r:'t' } }); return 'sent'; }"""
    ss = s.evaluate("JSON.parse(JSON.stringify(__T.UI.run.st))"); c0 = ss["coins"]
    bad = [{"id":"a1", "n":"50"}, {"id":"a2", "n":1e9}, {"id":"a3", "n":-1e9}, {"id":"a3b", "n":10000}, {"id":"a3c", "n":-10000}, {"id":"a3d", "n":float("inf")}, {"id":EVIL, "n":5}, {"id":"a4", "n":2.5}, {"id":"a5", "n":None}, {"id":"a6", "n":0}, {"n":30}, "50", 7, {"id":"ok1", "n":25}]
    t.evaluate(TSEND, [{"grants":bad, "coins":999999, "lives":1, "wave":19, "towers":[{"k":"sniper", "lv":3, "spent":0}] * 3, "pz":EVIL, "ch":"EVIL"}, EVIL]); s.wait_for_timeout(600)
    s2 = s.evaluate("JSON.parse(JSON.stringify(__T.UI.run.st))")
    check(s2["coins"] == c0 + 25 and s2["lives"] == ss["lives"] and s2["wave"] == ss["wave"] and s2["towers"] == ss["towers"] and s2["pz"] == ss["pz"], "td: from the teacher, only the one good grant (+25) counts; the student's coins, lives, wave, towers aren't taken (%d → %d)" % (c0, s2["coins"]))
    check(s.evaluate("window.__pwn") is None and s.locator("#app img[src='x']").count() == 0 and s.locator(".chov").count() == 1, "td: a poisoned challenge prompt shows as text, runs nothing")
    t.evaluate(TSEND, [{"grants":[{"id":"ok1", "n":25}, {"id":"ok2", "n":200}, {"id":"ok3", "n":10001}], "ch":None}, EVIL]); s.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.coins") == c0 + 25 + 200, "td: a grant comes once; 9999 is the cap (10001 is dropped)")
    # the score pad's take-away and set-to: negative grants, never below 0 coins
    t.evaluate(TSEND, [{"grants":[{"id":"ok1", "n":25}, {"id":"ok2", "n":200}, {"id":"neg1", "n":-25}], "ch":None}, EVIL]); s.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.coins") == c0 + 200, "td: a take-away grant (−25) counts once")
    t.evaluate(TSEND, [{"grants":[{"id":"ok1", "n":25}, {"id":"ok2", "n":200}, {"id":"neg1", "n":-25}, {"id":"neg2", "n":-9999}], "ch":None}, EVIL]); s.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.coins") == 0, "td: taking away more than they have stops at 0 coins")
    t.evaluate(TSEND, [{"grants":[{"id":"ok1", "n":25}, {"id":"ok2", "n":200}, {"id":"neg1", "n":-25}, {"id":"neg2", "n":-9999}, {"id":"back", "n":c0 + 225}], "ch":None}, EVIL]); s.wait_for_timeout(500)
    for over in ({"tlock":"yes"}, {"limit":EVILN}, {"auto":1}, {"uReq":"9"}, {"bonus":[1]}):
        t.evaluate(TSEND, [dict(over, grants=[{"id":"x" + str(abs(hash(json.dumps(over))) % 9999), "n":100}]), EVIL]); s.wait_for_timeout(350)
    s3 = s.evaluate("JSON.parse(JSON.stringify(__T.UI.run.st))")
    check(s3["coins"] == c0 + 225 and s3["tlock"] is False and s3["limit"] == 0, "td: a teacher's field of the wrong kind drops the whole message (no lock, no limit, no coins)")
    t.evaluate(TSEND, [{"uReq":1e9}, EVIL]); s.wait_for_timeout(400)
    check(s.evaluate("__T.UI.view") == "play" and s.evaluate("window.__pwn") is None, "td: a huge undo request doesn't hang the student's screen")
    # …and the student's side of the cards arriving at the teacher's status screen: shown from fixed text, numbers in range
    s.evaluate("() => { const r = __T.UI.run; r.st.tlock = false; r.st.card = null; r.st.cards = true; }")
    SSEND = """([card, log, evil]) => { const run = __T.UI.run, L = __T.LIVE, st = JSON.parse(JSON.stringify(run.st)); st.card = card; st.cardLog = log;
      L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:run.gameId, p:run.packId, gen:run.liveGen, t0:run.liveT0, rev:(run.st._rev || 0) + 500, st:st, title:'x', from:'zzzz', r:'s' } }); return 'sent'; }"""
    bc = {"g":{"k":"coins", "good":True, "n":1e12, "kk":EVIL, "lv":99, "s":-5}, "b":{"k":"lose", "good":False, "n":EVIL, "kk":"sniper", "lv":3, "s":2}, "step":"done", "gl":EVIL, "took":"L"}
    for card, log in ((bc, []), ({"g":{"k":"constructor", "good":True}, "b":{"k":"__proto__"}, "step":"done", "took":"R"}, [{"k":"toString"}, {"skip":EVIL}, {"k":"coins", "n":1e15}]), ({"g":{"k":"tax", "good":True}, "b":{"k":"coins", "good":False}, "step":"pick"}, [EVIL, 5])):
        s.evaluate(SSEND, [card, log, EVIL]); t.wait_for_timeout(500)
        check(t.evaluate("window.__pwn") is None and t.locator("#app img[src='x']").count() == 0 and t.evaluate("__T.UI.view") == "play", "td: poisoned cards from the student's screen: teacher safe (%s)" % t.inner_text(".td-stline")[:80])
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    # Re-check 1: state for a game that is NOT on screen (teacher on the lesson page). One number at a time, or an
    # extra list item, becomes an attribute-breaking string. Nothing may land in the page and the game must not open.
    ATTR = '1" xssattr="1" x="'
    OFF = """([st, gid, pid, attr, path]) => {
      const L = __T.LIVE; if (!L.chan) return 'no chan';
      const o = JSON.parse(st); let c = o; for (let i = 0; i < path.length - 1; i++) c = c[path[i]];
      const k = path[path.length - 1]; if (k === '+') c.push(attr); else c[k] = attr;
      L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:gid, p:pid, gen:'gen' + Math.random().toString(36).slice(2, 8), t0:Date.now() + 1e6, rev:3, st:o, title:'x', from:'zzzz' } });
      return 'sent';
    }"""
    def num_paths(v, path=(), out=None):
        out = [] if out is None else out
        if isinstance(v, bool): return out
        if isinstance(v, (int, float)): out.append(list(path))
        elif isinstance(v, list):
            if v and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v): out.append(list(path) + ["+"])
            for i, x in enumerate(v): num_paths(x, path + (i,), out)
        elif isinstance(v, dict):
            for k, x in v.items():
                if not k.startswith("_"): num_paths(x, path + (k,), out)
        return out
    import json
    t.click("[data-a=backlesson]") if t.locator("[data-a=backlesson]").count() else None
    sent = 0
    for g in games:
        t.click("[data-a=play][data-g=%s]" % g["id"]); t.wait_for_timeout(300)
        if t.evaluate("__T.UI.view") != "play": check(False, "%s didn't start" % g["type"]); continue
        st = t.evaluate("JSON.stringify(__T.UI.run.st)")
        t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
        paths = num_paths(json.loads(st)); paths = paths[:5] + paths[-3:] if len(paths) > 8 else paths
        bad = []
        for path in paths:
            s.evaluate(OFF, [st, g["id"], pack["id"], ATTR, path]); t.wait_for_timeout(180); sent += 1
            if t.locator("[xssattr]").count() or t.evaluate("window.__pwn") is not None: bad.append(path)
            if t.evaluate("__T.UI.view") == "play": bad.append(("opened", path)); t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
        check(not bad and t.locator("[xssattr]").count() == 0, "%s: %d poisoned numbers for a game not on screen are dropped %s" % (g["type"], len(paths), bad[:3]))
    print("sent %d off-screen poisons" % sent)
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
