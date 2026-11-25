"""25 Nov: Open all and the student's notes doc (teacher only, desktop Chrome).
Open all (first in the 📂 Files menu) opens every valid material in the planner's order, then the student's notes doc, as
new tabs; shown only when there is at least one of those. Chrome's pop-up blocker (only the first tab gets through) →
a one-line note in the menu, gone once Open all gets every tab through. The notes doc (students/<slug>.notes_doc, a Doc id)
is set on the student's page: a Doc link or bare id is kept as the id, junk shows an error and saves nothing, Remove clears it.
plan.py checks that notes_doc never reaches a student link, class link or broadcast."""
import json
import lg
from lg import *
APP2 = lg.APP

ND = "1RayNotesDocIdForTests_abcdef"
def MAT(t, i, seg="1"): return {"t":t, "id":i, "seg":[seg]}
spec = {"student":"Ray", "lp":605, "date":"2026-11-20", "start":"17:00", "length":60, "format":"online",
  "blocks":[{"label":"1 Reading", "mins":30, "lines":[{"type":"cue", "label":"1A Read"}]}, {"label":"2 Close", "mins":30, "lines":[{"type":"cue", "label":"2A HW"}]}]}
G = [{"id":"g1", "type":"hangman", "title":"Words", "block":"went\nsaw", "options":{}}]
def PK(i, who, lp, **kw): return dict({"id":i, "student":who, "lp":lp, "title":"%s · LP%d" % (who, lp), "date":"2026-11-%02d" % (lp % 28 + 1), "updatedAt":"x", "games":G, "runsheet":dict(spec, student=who, lp=lp)}, **kw)
MATS = [MAT("Pathways 3 U3R2", "1PathwaysU3R2FileId_abcdef"), MAT("Bad id", "../etc/passwd"), MAT("WS605", "1WS605FileIdForTests_qrstuv", "2"), MAT("Reader", "1ReaderFileIdForTests_hhhhh")]
PACKS = [
  PK("ray-605", "Ray", 605, plan={"docId":"1PlanDocIdForOpenAll_abcdef"}, materials=MATS),   # both
  PK("ray-604", "Ray", 604),                                                                   # notes doc only
  PK("zoe-10", "Zoe", 10, materials=MATS[:2]),                                                  # materials only (one bad)
  PK("kim-7", "Kim", 7, plan={"docId":"1PlanDocIdForKim7_abcdefg"}),                            # a plan, no materials, no notes doc
  PK("kim-6", "Kim", 6, materials=[MAT("Only a bad one", "nope")]),                             # nothing valid at all
]
STU = [{"id":"ray", "name":"Ray", "look":"chalk", "notes_doc":ND, "updatedAt":"x"}, {"id":"zoe", "name":"Zoe", "updatedAt":"x"},
       {"id":"kim", "name":"Kim", "notes_doc":"<img src=x onerror=alert(1)>", "updatedAt":"x"}]   # Kim's stored value is junk: ignored
FILE = lambda i: "https://drive.google.com/file/d/%s/view" % i
DOCU = lambda i: "https://docs.google.com/document/d/%s/edit" % i

def tpage(ctx, errs):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: (errs.append("dialog " + d.message), d.dismiss()))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed_db(PACKS, students=STU), "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}))
    def h(r):
        u = r.request.url
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg
def items(pg):
    if not pg.locator("header [data-a=pl-files]").count(): return None
    pg.click("header [data-a=pl-files]"); pg.wait_for_selector("#plFiles")
    return pg.evaluate("[...document.querySelectorAll('#plFiles .pl-files li')].map(l => l.classList.contains('sep') ? '—' + l.textContent : l.querySelector('[data-a=pl-openall]') ? 'Open all' : l.querySelector('a') ? l.querySelector('a span:not([aria-hidden])').textContent : l.className)")
def close(pg):
    if pg.locator("#plFiles").count(): pg.click("#plFiles button[data-a=pl-files-x]"); pg.wait_for_timeout(100)
def back(pg): pg.click("[data-a=nav-games]"); pg.wait_for_selector(".head h2")
def go(pg, title, who): go_lesson(pg, title, who=who); pg.wait_for_selector(".rs-blk")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    ctx = b.new_context(viewport={"width":1440, "height":900})
    ctx.route("https://drive.google.com/**", lambda r: r.fulfill(body="<title>Drive</title>stand-in", content_type="text/html"))
    ctx.route("https://docs.google.com/**", lambda r: r.fulfill(body="<title>Docs</title>stand-in", content_type="text/html"))
    t = tpage(ctx, errs)

    # both: materials (bad id skipped) then the notes doc
    go(t, "Ray · LP605", "Ray")
    it = items(t)
    check(it == ["Open all", "Open plan", "—This lesson’s materials", "Pathways 3 U3R2", "WS605", "Reader", "—Every lesson", "Notes doc"],
          "Ray LP605 Files: Open all first, Open plan, the valid materials, then Notes doc: %s" % it)
    check("4 tabs" in t.inner_text("#plFiles [data-a=pl-openall]"), "Open all says how many tabs (4)")
    nd = t.get_attribute("#plFiles a:has-text('Notes doc')", "href")
    check(nd == DOCU(ND), "the Notes doc item opens the Doc for editing (%s)" % nd)
    tabs = []; t_pages = []
    def on_page(q): t_pages.append(q)
    ctx.on("page", on_page)
    t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(1200)
    urls = []
    for q in t_pages:
        q.wait_for_load_state(); urls.append(q.url); tabs.append(q.evaluate("window.opener === null"))
    check(urls == [FILE("1PathwaysU3R2FileId_abcdef"), FILE("1WS605FileIdForTests_qrstuv"), FILE("1ReaderFileIdForTests_hhhhh"), DOCU(ND)],
          "Open all: one tab per material in the planner's order (bad id skipped), the notes doc last: %s" % urls)
    check(tabs and all(tabs), "every opened tab has no link back to Lesson Desk (opener cut)")
    check(t.locator("#plFiles").count() == 0, "all tabs opened: the menu closes")
    check(not [q for q in t_pages if q.evaluate("window.outerWidth") < 300], "tabs, not little pop-up windows")
    for q in t_pages: q.close()
    t_pages.clear()

    # Chrome's pop-up blocker: only the first open gets through
    t.evaluate("""(() => { const real = window.open; window.__realOpen = real; let n = 0;
      document.addEventListener('click', () => { n = 0; }, true);
      window.open = function(){ n++; return n === 1 ? real.apply(window, arguments) : null; }; })()""")
    items(t); t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(800)
    check(len(t_pages) == 1, "blocked: only the first tab opened (%d)" % len(t_pages))
    note = t.locator("#plFiles .pl-blocked")
    check(t.locator("#plFiles").count() == 1 and note.count() == 1 and "Chrome blocked some tabs: click the pop-up icon in the address bar → Always allow, then Open all again." in note.inner_text(),
          "blocked: the menu stays open with the one-line note")
    t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(500)
    check(t.locator("#plFiles .pl-blocked").count() == 1, "blocked again: still one note, not two")
    close(t); items(t)
    check(t.locator("#plFiles .pl-blocked").count() == 1, "reopening the menu while the site is still blocked keeps the note")
    for q in t_pages: q.close()
    t_pages.clear()
    t.evaluate("window.open = window.__realOpen; void 0")   # Sam picks Always allow
    t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(1200)
    check(len(t_pages) == 4 and t.locator("#plFiles").count() == 0, "allowed: all 4 tabs open and the menu closes (%d)" % len(t_pages))
    items(t); check(t.locator("#plFiles .pl-blocked").count() == 0, "…and the note doesn't come back"); close(t)
    for q in t_pages: q.close()
    t_pages.clear()

    # notes doc only
    back(t); go(t, "Ray · LP604", "Ray")
    it = items(t)
    check(it == ["Open all", "—Every lesson", "Notes doc"], "a lesson with no plan or materials: Files has Open all and the notes doc (%s)" % it)
    t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(800)
    check([q.url for q in t_pages] == [DOCU(ND)], "Open all: just the notes doc (%s)" % [q.url for q in t_pages])
    for q in t_pages: q.close()
    t_pages.clear()

    # materials only (one bad)
    back(t); go(t, "Zoe · LP10", "Zoe")
    it = items(t)
    check(it == ["Open all", "—This lesson’s materials", "Pathways 3 U3R2"] and "1 tab" in t.inner_text("#plFiles [data-a=pl-openall]"), "Zoe (no notes doc): Open all and her one valid material: %s" % it)
    t.click("#plFiles [data-a=pl-openall]"); t.wait_for_timeout(800)
    check([q.url for q in t_pages] == [FILE("1PathwaysU3R2FileId_abcdef")], "Open all: the material, nothing for the bad id, no notes doc (%s)" % [q.url for q in t_pages])
    for q in t_pages: q.close()
    t_pages.clear()

    # a plan only: Files, but no Open all; nothing valid: no Files at all
    back(t); go(t, "Kim · LP7", "Kim")
    it = items(t)
    check(it == ["Open plan"], "Kim LP7 (a plan, no materials, a junk notes doc): no Open all, no Notes doc (%s)" % it); close(t)
    back(t); go(t, "Kim · LP6", "Kim")
    check(t.locator("[data-a=pl-files]").count() == 0, "Kim LP6 (only a bad material, junk notes doc): no Files button")

    # the Plan tab header has the same menu
    back(t); go(t, "Ray · LP605", "Ray")
    t.route("**/functions/v1/plan-doc", lambda r: r.fulfill(body=json.dumps({"html":"<h2>SEGMENT 1</h2><p>Hi</p>", "name":"x.docx", "modified":"2026-11-19T06:00:00Z"}), content_type="application/json"))
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    it = items(t)
    check(it and it[0] == "Open all" and it[-1] == "Notes doc", "Plan tab 📂: Open all first, Notes doc last (%s)" % it); close(t)

    # the student's page: Notes doc field
    def stu_page(who):
        t.click("[data-a=home]"); t.wait_for_selector("#stuSec")
        if not t.evaluate("document.getElementById('stuSec').open"): t.click("#stuSec > summary")
        t.click("#stuSec [data-a=student]:has-text('%s')" % who); t.wait_for_selector("#ndSec")
        if not t.evaluate("document.getElementById('ndSec').open"): t.click("#ndSec > summary")
    def saved(who): return t.evaluate("(window.__MOCK.db.students[%s] || {data:{}}).data.notes_doc" % json.dumps(who))
    stu_page("Zoe")
    check("none" in t.inner_text("#ndSec summary") and t.input_value("#ndIn") == "", "Zoe's page: Notes doc, none yet, empty field")
    ZD = "1ZoeNotesDocId-_abcdefghij"
    t.fill("#ndIn", "  https://docs.google.com/document/d/%s/edit?tab=t.0#heading=h.x  " % ZD); t.click("[data-a=nd-save]"); t.wait_for_timeout(300)
    check(saved("zoe") == ZD, "a Doc link (with ?tab and #heading): only the id is saved (%s)" % saved("zoe"))
    check(t.input_value("#ndIn") == DOCU(ZD) and "set" in t.inner_text("#ndSec summary") and t.get_attribute("#ndOpen", "href") == DOCU(ZD), "the field shows the Doc's link, with an Open link")
    t.fill("#ndIn", "1BareIdPastedForZoe_abcdefg"); t.press("#ndIn", "Enter"); t.wait_for_timeout(300)
    check(saved("zoe") == "1BareIdPastedForZoe_abcdefg", "a bare id (Enter to save) is kept as it is")
    t.fill("#ndIn", "https://docs.google.com/document/u/0/d/1UserZeroDocId_abcdefgh/edit"); t.click("[data-a=nd-save]"); t.wait_for_timeout(300)
    check(saved("zoe") == "1UserZeroDocId_abcdefgh", "a /document/u/0/d/… link works too")
    log0 = t.evaluate("window.__MOCK.log.length")
    for junk in ("not a link", "https://drive.google.com/file/d/1PathwaysU3R2FileId_abcdef/view", "short", "https://docs.google.com/document/d/abc/edit", "<script>alert(1)</script>"):
        t.fill("#ndIn", junk); t.click("[data-a=nd-save]"); t.wait_for_timeout(200)
        err = t.locator("#ndErr")
        check(err.count() == 1 and "isn’t a Google Doc link" in err.inner_text() and saved("zoe") == "1UserZeroDocId_abcdefgh" and t.input_value("#ndIn") == junk,
              "junk %r: inline error, the text stays for fixing, nothing saved" % junk)
    check(t.evaluate("window.__MOCK.log.length") == log0, "…and nothing was sent to the database")
    check(t.locator("#ndSec script, #ndSec img").count() == 0, "the pasted text is shown as text")
    # what's typed survives a sync arriving
    t.fill("#ndIn", "half typed"); t.evaluate("window.__MOCK.remote('packs', 'UPDATE', { id:'zoe-10', data: Object.assign({}, window.__MOCK.db.packs['zoe-10'].data, { updatedAt:'y' }) })"); t.wait_for_timeout(300)
    check(t.input_value("#ndIn") == "half typed", "a sync arriving mid-edit keeps what's typed (%r)" % t.input_value("#ndIn"))
    t.fill("#ndIn", ""); t.click("[data-a=nd-save]"); t.wait_for_timeout(300)
    check(saved("zoe") is None and "notes_doc" not in t.evaluate("window.__MOCK.db.students.zoe.data"), "saving an empty field clears it")
    check(t.locator("[data-a=nd-clear]").count() == 0 and "none" in t.inner_text("#ndSec summary"), "…none again, no Remove button")
    stu_page("Ray")
    check(t.input_value("#ndIn") == DOCU(ND) and t.locator("[data-a=nd-clear]").count() == 1, "Ray's page: his notes doc, with Remove")
    t.click("[data-a=nd-clear]"); t.wait_for_timeout(300)
    st = t.evaluate("window.__MOCK.db.students.ray.data")
    check("notes_doc" not in st and st.get("look") == "chalk", "Remove clears the notes doc and keeps the rest of the record (%s)" % st)
    go(t, "Ray · LP604", "Ray")
    check(t.locator("[data-a=pl-files]").count() == 0, "Ray LP604 after Remove: nothing left, so no Files button")
    # a student with no record yet gets one
    t.evaluate("delete window.__MOCK.db.students.zoe; window.__MOCK.remote('students', 'DELETE', { id:'zoe' })"); t.wait_for_timeout(200)
    stu_page("Zoe"); t.fill("#ndIn", DOCU(ZD)); t.click("[data-a=nd-save]"); t.wait_for_timeout(300)
    check(saved("zoe") == ZD and t.evaluate("window.__MOCK.db.students.zoe.data.name") == "Zoe", "a student with no record yet: one is made with the notes doc")
    go(t, "Zoe · LP10", "Zoe")
    it = items(t); check(it and it[-1] == "Notes doc", "…and her lessons' Files menu has it, every lesson (%s)" % it); close(t)
    t.screenshot(path=HERE + "/shots/openall_rs.png")
    items(t); t.screenshot(path=HERE + "/shots/openall_menu.png"); close(t)

    print("errors:", errs[:5])
    check(not errs, "no page errors (and no alert)")
    b.close()
done()
