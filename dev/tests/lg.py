"""Shared helpers for the newer tests (fit.py, cls.py, ...). Older scripts stay self-contained."""
import json, os
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../.."))
MOCK = open(os.path.join(HERE, "mock-supabase.js")).read()
HOOK = "window.__T={get STORE(){return STORE},get UI(){return UI},get LIVE(){return LIVE},packData:packData,get PACKS(){return PACKS},get RESULTS(){return RESULTS},liveRoomFor:liveRoomFor,get SB(){return SB},get AUTH(){return AUTH},get STOREKIND(){return STORE && STORE.kind}};\n"
def app_html():
    a = open(ROOT + "/app/index.html", encoding="utf-8").read()
    a = __import__("re").sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>', "", a)  # the hook changes the script, so its CSP hash wouldn't match
    assert a.count("if(STUDENT_PAGE) startStudent();") == 1
    return a.replace("if(STUDENT_PAGE) startStudent();", HOOK + "if(STUDENT_PAGE) startStudent();")
APP = app_html()
BOARD = open(os.path.join(HERE, "board.b64")).read(); TOK = open(os.path.join(HERE, "tok.b64")).read(); JPG = open(os.path.join(HERE, "board.jpg"), "rb").read()
FAILS = []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: FAILS.append(m)
def done():
    print("%d failures" % len(FAILS))
def go_lesson(pg, title, who=None, timeout=8000):
    """Home lists only today's lessons; anything else is reached through the Students list (folded)."""
    pg.wait_for_selector("#stuSec, .head h2", timeout=timeout)
    if pg.locator(".head h2", has_text=title).count(): return   # the app reopened on this lesson
    if not pg.locator("#stuSec").count():
        if not pg.locator("[data-a=home]").count(): pg.click("[data-a=student]"); pg.wait_for_timeout(200)
        pg.click("[data-a=home]"); pg.wait_for_selector("#stuSec", timeout=timeout)
    if not pg.locator(".daybar ~ .list >> text=" + title).count():
        if not pg.evaluate("document.getElementById('stuSec').open"): pg.click("#stuSec > summary")
        pg.click("#stuSec [data-a=student]:has-text('%s')" % (who or title.split(" · ")[0])); pg.wait_for_timeout(250)
    pg.click("text=" + title)
def route(page, imgs=None):
    def h(r):
        u = r.request.url
        if "/storage/v1/object/public/" in u:
            if imgs is not None: imgs.append(u)
            return r.fulfill(body=JPG, content_type="image/jpeg")
        if u.endswith("/app/supabase.js") or u.endswith("/lesson-games/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP, content_type="text/html")
        return r.abort()
    page.route("**/*", h)
def seed_db(packs, students=None, results=None):
    db = {"packs":{}, "results":{}, "students":{}, "boards":{}, "sheets":{}}
    for p in packs: db["packs"][p["id"]] = {"id":p["id"], "data":p}
    for s in (students or []): db["students"][s["id"]] = {"id":s["id"], "data":s}
    for r in (results or []): db["results"][r["id"]] = {"id":r["id"], "data":r}
    db["boards"]["b1"] = {"id":"b1","data":{"id":"b1","name":"Blue","img":BOARD,"w":600,"h":600,"rows":10,"cols":10,"l":0,"r":0,"t":0,"b":0,"zig":True,"start":"bl","jumps":"3-22\n17-4","updatedAt":"x"}}
    return db
def teacher(ctx, db, errs):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("T: " + str(e)))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":db, "session":{"user":{"email":"t@x"}}}))
    route(pg); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg
def student(ctx, url, errs, imgs=None):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("S: " + str(e)))
    route(pg, imgs); pg.goto(url)
    return pg
def overflow(pg):
    """What scrolls or spills: the page itself, and any element whose content is wider/taller than its box."""
    return pg.evaluate("""() => {
      const W = innerWidth, H = innerHeight, out = [], d = document.documentElement;
      if (d.scrollHeight > H + 1) out.push('page scrolls ' + d.scrollHeight + '>' + H);
      if (d.scrollWidth > W + 1) out.push('page wide ' + d.scrollWidth + '>' + W);
      document.querySelectorAll('#app *').forEach(e => {
        const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.position === 'fixed') return;
        if (r.right > W + 2 || r.bottom > H + 2 || r.left < -2) {
          if (e.closest('.overlay') || e.closest('svg')) return;
          out.push('off-screen <' + e.tagName.toLowerCase() + ' class=' + e.className + '> ' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' "' + (e.textContent||'').trim().slice(0,30) + '"');
        }
        if ((cs.overflowX === 'hidden' || cs.overflow === 'hidden') && cs.textOverflow !== 'ellipsis' && e.scrollWidth > e.clientWidth + 2 && !e.matches('.reel, .reel *, .wheelwrap, svg *'))
          out.push('clipped <' + e.tagName.toLowerCase() + ' class=' + e.className + '> ' + e.scrollWidth + '>' + e.clientWidth + ' "' + (e.textContent||'').trim().slice(0,30) + '"');
      });
      return out.slice(0, 6);
    }""")
