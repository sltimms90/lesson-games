"""Header and home tidy (19 Nov): the lesson page's run sheet card becomes a 📋 header icon with a state dot; the home page is
"Lesson Desk" (heading and browser tab; student pages stay "Lesson Games"); › steps past today to planned lessons; the Plan
tab header is ☰ · HW Key · 🗂 (the "fetched" chip refreshes, no ↻), and HW Key shortens to HW on a narrow phone."""
import datetime, json, os
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get APP_NAME(){return APP_NAME},", 1)
APP2 = lg.APP

D = lambda n: (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
G = [{"id":"g1", "type":"hangman", "title":"Words", "block":"went\nsaw", "options":{}}]
spec = lambda lp, fmt: {"student":"Alice", "lp":lp, "date":D(0), "start":"17:00", "length":30, "format":fmt,
  "blocks":[{"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up"}]}, {"label":"1 Words", "mins":20, "lines":[{"type":"cue", "label":"1A Read"}]}]}
DOC = "1PlanDocIdForTidyTests_abcdefg"
HWPLAN = "<h2>SEGMENT 1 — WORDS</h2><p>Hello</p><p><strong>Key — HW4 (from HW4’s key page)</strong></p><p>1 went · 2 saw</p>"
packs = [
  {"id":"alice-lp5", "student":"Alice", "lp":5, "title":"Alice · LP5", "date":D(0), "updatedAt":"x", "games":G, "runsheet":spec(5, "in person"), "plan":{"docId":DOC}},
  {"id":"alice-lp6", "student":"Alice", "lp":6, "title":"Alice · LP6", "date":D(1), "updatedAt":"x", "games":G, "runsheet":spec(6, "online")},
  {"id":"alice-lp7", "student":"Alice", "lp":7, "title":"Alice · LP7", "date":D(3), "updatedAt":"x", "games":G},
  {"id":"bartholomew-lp305", "student":"Bartholomew", "lp":305, "title":"Bartholomew · LP305", "date":D(-1), "updatedAt":"x", "games":G, "plan":{"docId":DOC}},
]
def tpage(ctx, errs, sheets=None):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    db = seed_db(packs)
    for k, v in (sheets or {}).items(): db["sheets"][k] = {"id":k, "data":v}
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":db, "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}))
    calls = []
    def h(r):
        u = r.request.url
        if u.endswith("/functions/v1/plan-doc"):
            calls.append(1)
            if r.request.headers.get("x-slow") or len(calls) == 2: pg.wait_for_timeout(700)
            return r.fulfill(body=json.dumps({"html":HWPLAN, "name":"Alice_LP5.docx", "modified":"2026-11-19T06:00:00Z", "folderId":"1AliceFolderIdForTests_ff"}), content_type="application/json")
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    pg.calls = calls
    return pg
def head_order(pg):
    return pg.evaluate("[...document.querySelector('.pl-top').children].map(e => e.classList.contains('t') ? 'title' : (e.getAttribute('data-a') || e.tagName))")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    ctx = b.new_context(viewport={"width":1024, "height":768})
    t = tpage(ctx, errs)
    t.wait_for_selector(".daybar")
    # ---- 2. Lesson Desk
    check(t.inner_text(".head h1") == "Lesson Desk" and t.evaluate("__T.APP_NAME") == "Lesson Desk", "home heading is Lesson Desk (one constant)")
    check(t.title() == "Lesson Desk", "browser tab title is Lesson Desk (%s)" % t.title())
    # ---- 3. day forward
    check(t.locator("[data-a=day-next]").count() == 1 and t.locator("[data-a=day-today]").count() == 0, "at today: › is there, Today isn't")
    t.click("[data-a=day-next]"); t.wait_for_timeout(150)
    check(t.inner_text(".daybar h3").startswith("Tomorrow") and t.eval_on_selector_all(".daybar ~ .list .item b", "els=>els.map(e=>e.textContent)") == ["Alice · LP6"], "› goes to tomorrow, with its planned lesson: %s" % t.inner_text(".daybar h3"))
    check(t.locator("[data-a=day-today]").count() == 1, "Today button shows away from today")
    t.click("[data-a=day-next]"); t.wait_for_timeout(150)
    check("No lessons on this day." in t.inner_text("#app"), "a day with nothing shows the usual empty line")
    t.click("[data-a=day-next]"); t.wait_for_timeout(150)
    check(t.eval_on_selector_all(".daybar ~ .list .item b", "els=>els.map(e=>e.textContent)") == ["Alice · LP7"], "› keeps going (3 days ahead)")
    for _ in range(5): t.click("[data-a=day-next]")
    t.wait_for_timeout(150); check(t.locator("[data-a=day-next]").count() == 1, "no limit going forward")
    t.click("[data-a=day-today]"); t.wait_for_timeout(150)
    check(t.inner_text(".daybar h3").startswith("Today") and t.locator("[data-a=day-today]").count() == 0, "Today jumps back")
    t.click("[data-a=day-prev]"); t.wait_for_timeout(150)
    check(t.inner_text(".daybar h3").startswith("Yesterday"), "‹ still goes back")
    t.click("[data-a=day-next]"); t.wait_for_timeout(150)
    check(t.inner_text(".daybar h3").startswith("Today"), "and › from yesterday lands on Today")
    # ---- 1. 📋 icon on the lesson page
    t.click(".daybar ~ .list .item:has-text('Alice · LP5')"); t.wait_for_selector(".rs-blk")
    t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2")
    check(t.locator(".rs-card").count() == 0 and "Open run sheet" not in t.inner_text("#app"), "no run sheet card on the lesson page")
    ic = t.locator(".wrap > .spread .rs-ic")
    check(ic.count() == 1, "📋 run sheet icon in the header")
    sz = t.evaluate("(() => { const a = document.querySelector('[data-a=pl-open]').getBoundingClientRect(), b = document.querySelector('.rs-ic').getBoundingClientRect(); return [Math.round(a.width), Math.round(a.height), Math.round(b.width), Math.round(b.height), Math.round(b.left - a.right)]; })()")
    check(sz[0] == sz[2] and sz[1] == sz[3] and 0 <= sz[4] <= 14, "same size as 📖 and right beside it %s" % sz)
    check(ic.get_attribute("title") == "Run sheet · in person · not started" and "not started" in ic.get_attribute("aria-label") and "new" in ic.get_attribute("class"), "not started: hollow dot, title 'Run sheet · in person · not started' (%s)" % ic.get_attribute("title"))
    check(t.locator("#clsBar").count() == 1, "the slim class-link line stays")
    ic.click(); t.wait_for_selector(".rs-blk")
    t.click(".rs-chk >> nth=0") if t.locator(".rs-chk").count() else t.click(".rs-body [data-a] >> nth=0")
    t.wait_for_timeout(200); t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2")
    ic = t.locator(".wrap > .spread .rs-ic")
    check("on" in ic.get_attribute("class").split() and "started" in ic.get_attribute("title"), "after marking a line: amber dot, 'started · N unmarked' (%s)" % ic.get_attribute("title"))
    dot = t.evaluate("getComputedStyle(document.querySelector('.rs-ic .rs-dot')).backgroundColor")
    ic.click(); t.wait_for_selector(".rs-blk"); t.click("[data-a=rs-finish]"); t.wait_for_timeout(300)
    if t.locator(".overlay [data-a]").count() and t.evaluate("__T.UI.view") == "sheet" and not t.locator(".rs-top [data-a=rs-finish]:has-text('Finished')").count():
        btn = t.locator(".overlay button:has-text('Finish')");
        if btn.count(): btn.first.click(); t.wait_for_timeout(300)
    if t.evaluate("__T.UI.view") == "sheet": t.click("[data-a=rs-games]")
    t.wait_for_selector(".head h2")
    ic = t.locator(".wrap > .spread .rs-ic")
    check("fin" in ic.get_attribute("class").split() and ic.get_attribute("title").endswith("finished"), "finished: green dot, title says finished (%s)" % ic.get_attribute("title"))
    check(dot != t.evaluate("getComputedStyle(document.querySelector('.rs-ic .rs-dot')).backgroundColor"), "the dot's colour changes with the state")
    # a lesson with no run sheet: no icon
    t.click("[data-a=student]"); t.wait_for_timeout(200); t.click("text=Alice · LP7"); t.wait_for_selector(".head h2")
    check(t.locator(".rs-ic, [data-a=rs-open]").count() == 0, "no run sheet saved: no 📋 icon")
    # ---- 4. Plan tab header
    t.click("[data-a=student]"); t.wait_for_timeout(200); t.click("text=Alice · LP5"); t.wait_for_selector(".rs-blk")
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    order = head_order(t)
    check(order == ["pl-back", "title", "pl-outline", "pl-hw", "pl-files"], "Plan header: ‹ · title · ☰ · HW Key · 🗂, no ↻ (%s)" % order)
    chip = t.locator(".pl-meta [data-a=pl-refresh]")
    check(chip.count() == 1 and "fetched" in chip.inner_text() and chip.evaluate("e => e.tagName") == "BUTTON", "the 'fetched HH:MM' chip is a button (%s)" % chip.inner_text())
    n0 = len(t.calls); chip.click(); t.wait_for_timeout(150)
    busy = t.inner_text(".pl-meta [data-a=pl-refresh]")
    check("refreshing" in busy and t.locator(".pl-meta [data-a=pl-refresh][disabled]").count() == 1, "tapping it refetches, showing 'refreshing…' (%s)" % busy)
    t.wait_for_function("document.querySelector('.pl-meta [data-a=pl-refresh]') && /fetched/.test(document.querySelector('.pl-meta [data-a=pl-refresh]').textContent)", timeout=4000)
    check(len(t.calls) == n0 + 1, "one fetch per tap")
    check(t.inner_text(".pl-top .pl-hwb") == "HW Key", "on the iPad: 'HW Key' in full")
    ctx.close()
    # phones and other sizes
    for vw, vh, name in ((375, 812, "phone 375"), (390, 844, "phone 390"), (820, 1180, "iPad portrait"), (1180, 820, "iPad landscape"), (1440, 900, "desktop")):
        c = b.new_context(viewport={"width":vw, "height":vh}, device_scale_factor=1); e2 = []
        pg = tpage(c, e2); pg.wait_for_selector(".daybar")
        for title, who in (("Alice · LP5", None), ("Bartholomew · LP305", "Bartholomew")):
            go_lesson(pg, title, who=who); pg.wait_for_selector(".rs-blk, .head h2"); pg.wait_for_timeout(150)
            if pg.locator(".rs-top").count(): pg.click(".rs-top [data-a=pl-open]")
            else: pg.click(".row [data-a=pl-open]")
            pg.wait_for_selector(".pl-doc"); pg.wait_for_timeout(250)
            m = pg.evaluate("""(() => { const t = document.querySelector('.pl-top .t'), pt = t.querySelector('.pt'), h = document.querySelector('.pl-top');
              return { have: t.clientWidth, need: Math.ceil(pt.getBoundingClientRect().width), hw: (document.querySelector('.pl-hwb') || {}).textContent,
                       fits: h.scrollWidth <= h.clientWidth + 1, wide: document.documentElement.scrollWidth - innerWidth }; })()""")
            short = m["hw"] == "HW"
            if vw >= 420: ok = m["hw"] == "HW Key"
            else: ok = (m["have"] + 1 >= m["need"]) if not short else True
            check(ok and m["fits"] and m["wide"] <= 1, "%s · %s: HW label %r, title %d/%dpx, header fits, no sideways scroll" % (name, title, m["hw"], m["have"], m["need"]))
            if vw < 420 and title.startswith("Alice"): check(not short, "%s: a short title (Alice · LP5) keeps 'HW Key' when it fits (%s)" % (name, m))
            if vw < 420 and title.startswith("Bartholomew"):
                check(short or m["have"] + 1 >= m["need"], "%s: a long title shortens HW Key to HW rather than cut 'Bartholomew · LP305' (%s)" % (name, m))
                pg.screenshot(path=os.path.join(HERE, "shots", "tidy_plan_%s.png" % vw))
            pg.click("[data-a=pl-back]"); pg.wait_for_timeout(200)
            if pg.locator("[data-a=rs-games]").count(): pg.click("[data-a=rs-games]"); pg.wait_for_timeout(150)
        # lesson page header with 📋 on this size
        go_lesson(pg, "Alice · LP5"); pg.wait_for_selector(".rs-blk"); pg.click("[data-a=rs-games]"); pg.wait_for_selector(".head h2"); pg.wait_for_timeout(150)
        check(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 1 and pg.locator(".rs-ic").is_visible(), "%s: lesson page header with 📋 fits" % name)
        if vw == 390: pg.screenshot(path=os.path.join(HERE, "shots", "tidy_lesson_390.png"))
        errs += e2; c.close()
    # student page keeps "Lesson Games"
    c = b.new_context(viewport={"width":1024, "height":768}); t = tpage(c, errs); go_lesson(t, "Alice · LP5"); t.wait_for_selector(".rs-blk"); t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2")
    t.click("[data-a=slink][data-g=g1]"); t.wait_for_selector("#slinkUrl"); url = t.input_value("#slinkUrl")
    s = student(c, url, errs); s.wait_for_selector("[data-a=s-start]", timeout=6000)
    check(s.title() == "Lesson Games" and "Lesson Desk" not in s.inner_text("body"), "a student page's tab still says Lesson Games (%s)" % s.title())
    c.close()
    print("errors:", errs[:5]); check(not errs, "no page errors")
    b.close()
done()
