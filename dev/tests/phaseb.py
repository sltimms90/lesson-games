"""Phase B tracker (22 Nov): the phaseb table (one row per pack, written by the planning chats and the Phase B screen),
taught / needs a look / not yet worked out from run sheet marks and results, the Phase B screen (Owed, Needs a look,
Done lately with undo, the one-off Start-up action), the owed badge on the Lesson Desk home, the quiet line on a lesson
whose previous lesson still owes its Phase B, live updates when a chat writes a row, and fit on phone and iPad."""
import datetime, json
from lg import *

D = lambda n: (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
NOW = datetime.datetime.now(datetime.timezone.utc)
ISO = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
AT = lambda n, h=10: ISO(datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=n), datetime.time(h, 0)).astimezone(datetime.timezone.utc))
G = [{"id":"g1", "type":"hangman", "title":"Words", "block":"went\nsaw", "options":{}}]
def spec(stu, lp, d): return {"student":stu, "lp":lp, "date":d, "start":"17:00", "length":30, "format":"in person",
  "blocks":[{"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up"}]}, {"label":"1 Words", "mins":20, "lines":[{"type":"cue", "label":"1A Read"}]}]}
def pk(stu, lp, d, rs=False, upd="2026-11-01T00:00:00Z"):
    o = {"id":"%s-lp%d" % (stu.lower().replace(" & ", "-"), lp), "student":stu, "lp":lp, "title":"%s · LP%d" % (stu, lp), "date":d, "updatedAt":upd, "games":G}
    if rs: o["runsheet"] = spec(stu, lp, d)
    return o
packs = [
  pk("Alice", 4, D(-10)),                      # result -> owed, 10 days (late)
  pk("Alice", 5, D(-3), rs=True),              # run sheet marked -> owed; opens on its run sheet
  pk("Alice", 6, D(0), rs=True),               # today, nothing yet -> not owed; its page says LP 5 is owed
  pk("Bob", 20, D(-5)),                        # nothing, date passed -> needs a look
  pk("Bob", 21, D(-1)),                        # homework result only -> needs a look (homework doesn't count)
  pk("Bob", 22, D(2), rs=True),                # future, a skip ticked in advance -> not yet
  pk("Cathy & Lily", 70, ""),                  # no date, a result -> owed, day from the result
  pk("Dan", 1, "", upd=AT(-6)),                # no date, nothing, a newer lesson -> needs a look
  pk("Dan", 2, ""),                            # no date, nothing, newest -> not yet
  pk("Eve", 9, D(-4)),                         # result, and a chat already did Phase B -> done lately
  pk("Eve", 10, D(-1), rs=True),               # run sheet marked -> owed
  pk("Eve", 11, D(0)),                         # today; its page says LP 10 is owed
  pk("Fay", 3, D(-30)),                        # result, Phase B done 20 days ago -> in neither list
]
def res(pid, at, hw=False):
    r = {"id":pid + "_g1_" + at[:10], "packId":pid, "gameId":"g1", "type":"hangman", "title":"Words", "at":at, "summary":"Words — 2/2", "items":[], "score":{}}
    if hw: r["homework"] = True
    return r
results = [res("alice-lp4", AT(-10)), res("bob-lp21", AT(-1, 20), hw=True), res("cathy-lily-lp70", AT(-2)), res("eve-lp9", AT(-4)), res("fay-lp3", AT(-30))]
def sheet(pid, marks, d): return {"id":pid, "packId":pid, "date":d, "updatedAt":AT(0, 1), "marks":marks, "finished":False}
sheets = {"alice-lp5": sheet("alice-lp5", {"x.cue.a":"y"}, D(-3)), "eve-lp10": sheet("eve-lp10", {"end.spine":"4"}, D(-1)),
          "bob-lp22": sheet("bob-lp22", {"b1.skip":"y"}, D(2)), "alice-lp6": sheet("alice-lp6", {}, D(0))}
phaseb = {"eve-lp9":{"pack_id":"eve-lp9", "status":"done", "at":ISO(NOW - datetime.timedelta(days=1)), "by":"chat", "note":None},
          "fay-lp3":{"pack_id":"fay-lp3", "status":"done", "at":ISO(NOW - datetime.timedelta(days=20)), "by":"chat", "note":None}}

def tpage(ctx, errs, rows=None):
    db = seed_db(packs, results=results)
    for k, v in sheets.items(): db["sheets"][k] = {"id":k, "data":v}
    db["phaseb"] = json.loads(json.dumps(phaseb if rows is None else rows))
    return teacher(ctx, db, errs)
def names(pg, sec):
    return pg.eval_on_selector_all(sec + " .pb-row .pb-t", "els => els.map(e => e.querySelector('b').textContent + ' ' + (e.querySelector('.pb-lp') ? e.querySelector('.pb-lp').textContent : ''))")
def row(pg, pid): return pg.evaluate("id => __MOCK.db.phaseb[id] || null", pid)
def badge(pg): return pg.evaluate("(() => { const b = document.querySelector('.pb-ent .pb-badge'); return b ? b.textContent : ''; })()")
def owed(pg): return pg.locator("#pbOwed .pb-row").count()
def widths(pg):
    """sideways only: the page wider than the screen, or anything sticking out left or right"""
    return pg.evaluate("""() => { const W = innerWidth, out = []; if (document.documentElement.scrollWidth > W + 1) out.push('page wide ' + document.documentElement.scrollWidth);
      document.querySelectorAll('#app *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.right > W + 2 || r.left < -2)) out.push(e.tagName + '.' + e.className + ' ' + Math.round(r.left) + '..' + Math.round(r.right) + ' ' + (e.textContent || '').trim().slice(0, 30)); });
      return out.slice(0, 5); }""")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    ctx = b.new_context(viewport={"width":1180, "height":820})
    t = tpage(ctx, errs)
    t.wait_for_selector(".daybar"); t.wait_for_timeout(300)
    # ---- the badge on the Lesson Desk home
    check(badge(t) == "4", "home: Phase B entry shows 4 owed (%r)" % badge(t))
    check(t.get_attribute(".pb-ent", "aria-label") == "Phase B: 4 owed", "badge has a spoken label: %s" % t.get_attribute(".pb-ent", "aria-label"))
    check(t.evaluate("__MOCK.log.some(l => l === 'select phaseb')"), "the app reads the phaseb table")
    # ---- the Phase B screen
    t.click(".pb-ent"); t.wait_for_selector("#pbOwed")
    check(t.inner_text(".nav .t") == "Phase B" and t.locator(".nav [data-a=home]").count() == 1 and t.locator(".nav [data-a=student]").count() == 0, "Phase B screen: nav bar with 🏠 and its title, no 👤")
    check(names(t, "#pbOwed") == ["Alice LP 4", "Alice LP 5", "Cathy & Lily LP 70", "Eve LP 10"], "Owed, oldest first: %s" % names(t, "#pbOwed"))
    waits = t.eval_on_selector_all("#pbOwed .pb-wait", "els => els.map(e => e.textContent + (e.classList.contains('late') ? '!' : ''))")
    check(waits == ["10 days!", "3 days", "2 days", "1 day"], "days waiting, a week or more stands out: %s" % waits)
    check(D(-10)[8:].lstrip("0") in t.inner_text("#pbOwed .pb-row >> nth=0"), "the day taught is shown: %s" % t.inner_text("#pbOwed .pb-row >> nth=0 >> small"))
    check(t.eval_on_selector_all("#pbOwed .pb-row >> nth=0 >> button", "els => els.map(e => e.textContent + '|' + e.getAttribute('aria-label'))") == ["🎲|Open the lesson", "✅|Mark Phase B done", "🚫|Not needed"], "owed row: icon buttons open · done · not needed")
    check(t.eval_on_selector_all("#pbOwed .pb-row >> nth=1 >> [data-a=open]", "els => els.map(e => e.textContent)") == ["📋"], "a lesson with a run sheet opens on 📋")
    check(t.evaluate("document.getElementById('pbLook').open") and names(t, "#pbLook") == ["Dan LP 1", "Bob LP 20", "Bob LP 21"], "Needs a look (open, it has some): %s" % names(t, "#pbLook"))
    check(t.locator("#pbLook [data-a=pb-done]", has_text="Taught (mark done)").count() == 3 and t.locator("#pbLook [data-a=pb-skip]", has_text="Not needed").count() == 3, "Needs a look rows: Taught (mark done) · Not needed")
    allrows = t.inner_text("#app")
    check("LP 6" not in allrows and "LP 22" not in allrows and "LP 2\n" not in allrows and "LP 11" not in allrows, "not yet taught (today, future, newest undated) isn't listed")
    check(not t.evaluate("document.getElementById('pbDone').open") and names(t, "#pbDone") == ["Eve LP 9"], "Done lately is folded, last 14 days only: %s" % names(t, "#pbDone"))
    check("planning chat" in t.text_content("#pbDone") and t.locator("#pbDone [data-a=pb-undo]").count() == 0, "a chat's mark has no undo")
    # ---- open the run sheet, and the quiet line there
    t.click("#pbOwed .pb-row >> nth=1 >> [data-a=open]"); t.wait_for_selector("main.rs")
    check(t.inner_text(".pb-prev") == "LP 4 Phase B not done yet", "run sheet of LP5 says LP 4 is owed: %r" % (t.locator(".pb-prev").all_inner_texts()))
    t.click(".pb-prev button"); t.wait_for_selector("#pbOwed")
    check(True, "the line goes to the Phase B screen")
    # ---- mark done, undo, not needed
    t.click("#pbOwed .pb-row[data-pid=alice-lp4] [data-a=pb-done]"); t.wait_for_timeout(200)
    r = row(t, "alice-lp4")
    check(r and r["status"] == "done" and r["by"] == "manual" and r["note"] is None and r["at"], "✅ writes { done, manual }: %s" % r)
    check(owed(t) == 3 and "Alice LP 4" in names(t, "#pbDone"), "it leaves Owed and shows under Done lately")
    check(not any(l.startswith("upsert packs") for l in t.evaluate("__MOCK.log")), "marking never saves the pack")
    t.click("#pbDone > summary"); t.click("#pbDone .pb-row[data-pid=alice-lp4] [data-a=pb-undo]"); t.wait_for_timeout(200)
    check(row(t, "alice-lp4") is None and owed(t) == 4, "↶ undo deletes the row; back to owed")
    t.click("#pbOwed .pb-row[data-pid=cathy-lily-lp70] [data-a=pb-skip]"); t.wait_for_timeout(200)
    check((row(t, "cathy-lily-lp70") or {}).get("status") == "skip" and owed(t) == 3, "🚫 writes { skip, manual }")
    check("not needed" in t.inner_text("#pbDone .pb-row[data-pid=cathy-lily-lp70]"), "Done lately says not needed")
    t.click("#pbLook .pb-row[data-pid=bob-lp20] [data-a=pb-done]"); t.wait_for_timeout(150)
    t.click("#pbLook .pb-row[data-pid=dan-lp1] [data-a=pb-skip]"); t.wait_for_timeout(150)
    check(row(t, "bob-lp20")["status"] == "done" and row(t, "dan-lp1")["status"] == "skip" and names(t, "#pbLook") == ["Bob LP 21"], "Needs a look: Taught → done, Not needed → skip")
    # ---- a failed save comes back
    t.evaluate("__MOCK.failNext = true"); t.click("#pbOwed .pb-row[data-pid=eve-lp10] [data-a=pb-done]"); t.wait_for_timeout(400)
    check(row(t, "eve-lp10") is None and owed(t) == 3 and "Couldn’t save" in t.inner_text("body"), "a failed save says so and the lesson stays owed")
    # ---- the lesson page line, then a planning chat's write arriving live
    t.click(".nav [data-a=home]"); t.wait_for_selector(".daybar")
    check(badge(t) == "3", "badge follows the marks (3): %r" % badge(t))
    go_lesson(t, "Eve · LP11")
    t.wait_for_selector(".head h2")
    check(t.inner_text(".pb-prev") == "LP 10 Phase B not done yet", "lesson page of LP11: one quiet line for LP 10")
    upsert = {"pack_id":"eve-lp10", "status":"done", "at":ISO(NOW), "by":"chat", "note":None}
    t.evaluate("r => { __MOCK.remote('phaseb', 'INSERT', r); __MOCK.remote('phaseb', 'UPDATE', r); }", upsert); t.wait_for_timeout(300)
    check(t.locator(".pb-prev").count() == 0, "a chat's row arrives live: the line goes")
    check(t.evaluate("Object.keys(__MOCK.db.phaseb).filter(k => k === 'eve-lp10').length") == 1, "the same upsert twice is still one row")
    t.click(".nav [data-a=home]"); t.wait_for_selector(".daybar")
    check(badge(t) == "2", "badge 2 after the chat's mark: %r" % badge(t))
    go_lesson(t, "Bob · LP22"); t.wait_for_selector("main.rs, .head h2")
    check(t.locator(".pb-prev").count() == 0, "previous lesson needing a look (not owed): no line")
    # ---- start-up on a fresh table
    ctx2 = b.new_context(viewport={"width":1180, "height":820}, accept_downloads=True)
    t2 = tpage(ctx2, errs, rows={})
    t2.wait_for_selector(".daybar"); t2.wait_for_timeout(300)
    check(badge(t2) == "6", "with no rows yet every taught lesson is owed (6, Eve 9 and Fay 3 too): %r" % badge(t2))
    t2.click(".pb-ent"); t2.wait_for_selector("#pbLaunch")
    check(t2.evaluate("document.getElementById('pbLaunch').open"), "Start-up is open while the table is empty")
    t2.fill("#pbBefore", D(-2)); t2.wait_for_timeout(200)
    lb = t2.inner_text("[data-a=pb-launch]")
    check(lb == "Mark 6 as done", "before %s: Fay 3, Alice 4, Dan 1, Bob 20, Eve 9, Alice 5 (%s)" % (D(-2), lb))
    t2.click("[data-a=pb-launch]"); t2.wait_for_timeout(150)
    check(t2.inner_text("[data-a=pb-launch]") == "Tap again: mark 6" and not t2.evaluate("Object.keys(__MOCK.db.phaseb).length"), "first tap only arms it")
    t2.click("[data-a=pb-launch]"); t2.wait_for_timeout(300)
    rows = t2.evaluate("Object.values(__MOCK.db.phaseb)")
    check(sorted(r["pack_id"] for r in rows) == ["alice-lp4", "alice-lp5", "bob-lp20", "dan-lp1", "eve-lp9", "fay-lp3"] and all(r["by"] == "manual" and r["note"] == "launch" and r["status"] == "done" for r in rows), "second tap marks them done (manual, note launch)")
    check(t2.evaluate("__MOCK.log.filter(l => l.startsWith('upsert phaseb')).length") == 1, "in one upsert")
    check(names(t2, "#pbOwed") == ["Cathy & Lily LP 70", "Eve LP 10"] and names(t2, "#pbLook") == ["Bob LP 21"], "what's left: %s / %s" % (names(t2, "#pbOwed"), names(t2, "#pbLook")))
    check("6 lessons marked done in one go" in t2.text_content("#pbDone") and t2.locator("#pbDone .pb-row").count() == 1, "Done lately: one Start-up line, not 6 rows")
    t2.click("#pbDone > summary"); t2.click("[data-a=pb-undo-launch]"); t2.wait_for_timeout(300)
    check(not t2.evaluate("Object.keys(__MOCK.db.phaseb).length") and owed(t2) == 6, "↶ undoes the whole start-up")
    t2.click("#pbOwed .pb-row[data-pid=eve-lp10] [data-a=pb-done]"); t2.wait_for_timeout(200)   # one row for the backup
    with t2.expect_download() as dl:
        t2.click(".nav [data-a=home]"); t2.wait_for_selector(".daybar"); t2.click("[data-a=backup]")
    data = json.load(open(dl.value.path()))
    check([r["pack_id"] for r in data["collections"].get("phaseb", [])] == ["eve-lp10"], "the backup file carries the Phase B rows")
    n = t2.evaluate("__T.STORE.restore({ phaseb:[{ pack_id:'bob-lp21', status:'skip', at:'2026-11-01T00:00:00Z', by:'chat' }, { pack_id:'x', status:'bogus' }] })")
    check(n.get("phaseb") == 1 and row(t2, "bob-lp21") == {"pack_id":"bob-lp21", "status":"skip", "at":"2026-11-01T00:00:00Z", "by":"chat", "note":None}, "restore puts Phase B rows back (bad ones dropped): %s" % n)
    # ---- fit: phone (both ways) and landscape iPad, no sideways scrolling
    for vw, vh, nm in [(390, 844, "phone"), (844, 390, "phone landscape"), (1180, 820, "iPad landscape"), (360, 740, "small phone")]:
        c2 = b.new_context(viewport={"width":vw, "height":vh}, has_touch=vw < 900)
        f = tpage(c2, errs); f.wait_for_selector(".daybar"); f.wait_for_timeout(300)
        w0 = widths(f)
        f.click(".pb-ent"); f.wait_for_selector("#pbOwed"); f.evaluate("document.getElementById('pbDone').open = true; document.getElementById('pbLaunch').open = true"); f.wait_for_timeout(150)
        w1 = widths(f)
        check(not w0 and not w1, "%s %dx%d: home and Phase B fit the width %s %s" % (nm, vw, vh, w0, w1))
        tops = f.eval_on_selector_all("#pbOwed .pb-row", "els => els.map(e => { const t = e.querySelector('.pb-t').getBoundingClientRect(), b = e.querySelector('.pb-b').getBoundingClientRect(); return Math.abs(t.top + t.height / 2 - (b.top + b.height / 2)) < 12; })")
        check(all(tops), "%s: each owed row is one line (name, then its three icons)" % nm)
        if nm in ("phone", "iPad landscape"): f.screenshot(path="phaseb_%s.png" % ("phone" if nm == "phone" else "ipad"), full_page=True)
        c2.close()
    # ---- students reach nothing of it
    s = ctx.new_page(); s.on("pageerror", lambda e: errs.append("S: " + str(e)))
    s.add_init_script("window.__MOCK = %s;" % json.dumps({"db":{"phaseb":phaseb}}))
    route(s); s.goto("https://sltimms90.github.io/lesson-games/#s=nothing"); s.wait_for_timeout(500)
    check(not s.evaluate("(window.__MOCK.log || []).some(l => l.indexOf('phaseb') !== -1)") and "Phase B" not in s.inner_text("body"), "a student page never touches phaseb")
    src = open(ROOT + "/app/index.html", encoding="utf-8").read()
    import re
    for fn in ["function packData", "function slinkData", "function liveSync", "function clsBarHtml", "function startStudent"]:
        i = src.find(fn); body = src[i:src.find("\nfunction ", i + 10)] if i != -1 else ""
        check(i != -1 and "PHASEB" not in body and "phaseb" not in body.lower().replace("phase b", ""), "%s doesn't touch Phase B" % fn)
    print("errors:", errs)
    check(not errs, "no page errors")
    b.close()
done()
