"""Lesson materials (Nov 2026): packs.materials [{t, id, p, seg}] from Gate 5 → the 📂 Files menu (Open plan, Folder, then
each material) on the run sheet and Plan tab headers, and a chip per material under each run sheet block named in its seg.
Untrusted fields: a bad id or missing label drops the entry; labels are text, never HTML. Teacher only (plan.py checks
that nothing reaches student or class links). Phone, iPad and desktop sizes."""
import json, os
import lg
from lg import *
APP2 = lg.APP

DOC = "1PlanDocIdForMaterialsTest_abcd"
MATS = [
  {"t":"Pathways 3 U3R2", "id":"1PathwaysU3R2FileId_abcdef", "p":"p.62–63", "seg":["1", "2"]},
  {"t":"His Dark Materials", "id":"1HisDarkMaterialsFileId_xyz", "p":"ch.4", "seg":["2"]},
  {"t":"WS605", "id":"1WS605FileIdForTests_qrstuv", "p":"p.1–2", "seg":["1"]},
  {"t":"Bad id", "id":"../../etc/passwd", "seg":["1"]},
  {"t":"Short id", "id":"abc", "seg":["1"]},
  {"id":"1NoLabelFileIdForTests_zzzz", "seg":["1"]},
  {"t":"<img src=x onerror=alert(1)>Reader", "id":"1ReaderFileIdForTests_hhhhh", "p":"<b>p.9</b>"},
  {"t":"Glossary", "id":"1GlossaryFileIdForTests_ggg", "p":"all", "seg":["9"]},
  "not an object", None, {"t":"Numbers seg", "id":"1NumbersSegFileId_nnnnnn", "seg":[3]},
]
spec = {"student":"Ray", "lp":605, "date":"2026-11-20", "start":"17:00", "length":60, "format":"online",
  "blocks":[{"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up"}]},
            {"label":"1 SPINE Club Recruiter", "mins":20, "lines":[{"type":"cue", "label":"1A The pitch"}]},
            {"label":"2 Reading: His Dark Materials", "mins":20, "lines":[{"type":"cue", "label":"2A Read"}]},
            {"label":"3 Close", "mins":10, "lines":[{"type":"cue", "label":"3A HW"}]}]}
G = [{"id":"g1", "type":"hangman", "title":"Words", "block":"went\nsaw", "options":{}}]
A = {"id":"ray-lp605", "student":"Ray", "lp":605, "title":"Ray · LP605", "date":"2026-11-20", "updatedAt":"x", "games":G, "runsheet":spec, "plan":{"docId":DOC}, "materials":MATS}
B = {"id":"ray-lp604", "student":"Ray", "lp":604, "title":"Ray · LP604", "date":"2026-11-13", "updatedAt":"x", "games":G, "runsheet":dict(spec, lp=604)}   # before the change: no plan, no materials
C = {"id":"ray-lp603", "student":"Ray", "lp":603, "title":"Ray · LP603", "date":"2026-11-06", "updatedAt":"x", "games":G, "runsheet":dict(spec, lp=603), "materials":"oops"}   # junk
D = {"id":"ray-lp602", "student":"Ray", "lp":602, "title":"Ray · LP602", "date":"2026-10-30", "updatedAt":"x", "games":G, "runsheet":dict(spec, lp=602), "materials":MATS[:1]}   # materials, no plan

def tpage(ctx, errs):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: (errs.append("dialog " + d.message), d.dismiss()))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed_db([A, B, C, D]), "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}))
    def h(r):
        u = r.request.url
        if u.endswith("/functions/v1/plan-doc"):
            return r.fulfill(body=json.dumps({"html":"<h2>SEGMENT 1 — SPINE</h2><p>Hello</p>", "name":"Ray_LP605.docx", "modified":"2026-11-19T06:00:00Z", "folderId":"1RayFolderIdForTests_ffff"}), content_type="application/json")
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg
def menu(pg):
    if not pg.locator("header [data-a=pl-files]").count(): return None
    pg.click("header [data-a=pl-files]"); pg.wait_for_selector("#plFiles")
    out = pg.evaluate("[...document.querySelectorAll('#plFiles a')].map(a => ({ t: a.querySelector('span:not([aria-hidden])').textContent, p: (a.querySelector('small') || {}).textContent || '', href: a.href, target: a.target, rel: a.rel }))")
    return out
def close(pg): pg.click("#plFiles button[data-a=pl-files-x]"); pg.wait_for_timeout(100)
def chips(pg, n):
    return pg.evaluate("n => { const s = [...document.querySelectorAll('.rs-blk')].find(b => b.querySelector('.rs-bar b').textContent.trim().startsWith(n + ' ')); return s ? [...s.querySelectorAll('.rs-files a')].map(a => [a.textContent.replace('📄', '').trim(), a.href, a.target]) : null; }", n)
URL = lambda i: "https://drive.google.com/file/d/%s/view" % i

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    ctx = b.new_context(viewport={"width":1024, "height":768})
    ctx.route("https://drive.google.com/**", lambda r: r.fulfill(body="<title>Drive</title>stand-in for Drive", content_type="text/html"))
    t = tpage(ctx, errs)
    go_lesson(t, "Ray · LP605", who="Ray"); t.wait_for_selector(".rs-blk")
    m = menu(t)
    check(m is not None, "the run sheet header has the 📂 Files button")
    names = [x["t"] for x in (m or [])]
    check(names == ["Open plan", "Pathways 3 U3R2", "His Dark Materials", "WS605", "<img src=x onerror=alert(1)>Reader", "Glossary", "Numbers seg"],
          "Files lists Open plan, then the materials in the planner's order; bad ids, short ids, no label and non-objects dropped: %s" % names)
    mm = dict((x["t"], x) for x in (m or []))
    check(mm.get("Open plan", {}).get("href") == URL(DOC), "Open plan → the plan file")
    check(mm.get("Pathways 3 U3R2", {}).get("href") == URL("1PathwaysU3R2FileId_abcdef") and mm["Pathways 3 U3R2"]["p"] == "p.62–63", "a material → its Drive file, pages shown beside it")
    check(all(x["target"] == "_blank" and "noopener" in x["rel"] for x in (m or [])), "every link opens outside the app, noopener")
    check(t.locator("#plFiles img, #plFiles b").count() == 0 and mm.get("<img src=x onerror=alert(1)>Reader", {}).get("p") == "<b>p.9</b>", "labels and pages are shown as text, never HTML")
    check("Folder" not in names and "once the plan has been fetched" in t.inner_text("#plFiles"), "no Folder before the plan is fetched, with a note saying how to get it")
    close(t); check(t.locator("#plFiles").count() == 0, "Close shuts the menu")
    # tapping a file link opens it in a new tab and closes the menu
    t.click("header [data-a=pl-files]"); t.wait_for_selector("#plFiles")
    with ctx.expect_page() as np: t.click("#plFiles a:has-text('WS605')")
    newp = np.value; newp.wait_for_load_state(); check(newp.url == URL("1WS605FileIdForTests_qrstuv"), "tapping WS605 opens its file in a new tab (%s)" % newp.url); newp.close()
    t.wait_for_timeout(200); check(t.locator("#plFiles").count() == 0, "…and the menu closes")
    # per-block chips
    c0, c1, c2, c3 = chips(t, "0"), chips(t, "1"), chips(t, "2"), chips(t, "3")
    check(c0 == [], "block 0 (no material for it): no chips (%s)" % c0)
    check([x[0] for x in c1 or []] == ["Pathways 3 U3R2 · p.62–63", "WS605 · p.1–2"], "block 1 shows Pathways and WS605, in order: %s" % c1)
    check([x[0] for x in c2 or []] == ["Pathways 3 U3R2 · p.62–63", "His Dark Materials · ch.4"], "block 2 shows Pathways and His Dark Materials: %s" % c2)
    check([x[0] for x in c3 or []] == ["Numbers seg"], "a seg written as a number still matches block 3: %s" % c3)
    check(all(x[1].startswith("https://drive.google.com/file/d/") and x[2] == "_blank" for x in (c1 or []) + (c2 or [])), "chips open their Drive files in a new tab")
    check("Glossary" not in t.inner_text(".rs") and "Reader" not in t.inner_text(".rs"), "a seg matching no block (9) or no seg at all: only in the Files list")
    check(t.locator(".rs-blk .rs-files img").count() == 0, "no HTML from the materials on the run sheet")
    # Plan tab: Files in its header, with Folder once fetched
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    m2 = menu(t); n2 = [x["t"] for x in (m2 or [])]
    check(n2[:2] == ["Open plan", "Folder"] and "Pathways 3 U3R2" in n2, "Plan tab 📂 Files: Open plan, Folder (now fetched), then the materials: %s" % n2[:4])
    close(t)
    t.click("[data-a=pl-back]"); t.wait_for_selector(".rs-blk")
    check("Folder" in [x["t"] for x in (menu(t) or [])], "back on the run sheet, the Files menu has Folder too"); close(t)
    # lessons without materials
    t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2"); go_lesson(t, "Ray · LP604", who="Ray"); t.wait_for_selector(".rs-blk")
    check(t.locator("[data-a=pl-files]").count() == 0 and t.locator(".rs-files").count() == 0, "a lesson from before the change (no plan, no materials): no Files button, no chips")
    t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2"); go_lesson(t, "Ray · LP603", who="Ray"); t.wait_for_selector(".rs-blk")
    check(t.locator("[data-a=pl-files]").count() == 0 and t.locator(".rs-files").count() == 0, "materials that aren't a list: ignored")
    t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2"); go_lesson(t, "Ray · LP602", who="Ray"); t.wait_for_selector(".rs-blk")
    n4 = [x["t"] for x in (menu(t) or [])]
    check(n4 == ["Pathways 3 U3R2"], "materials without a plan: Files has just the materials (%s)" % n4); close(t)
    check(len(chips(t, "1") or []) == 1, "…and the chips")
    ctx.close()
    # sizes
    for vw, vh, name in ((390, 844, "phone"), (820, 1180, "iPad portrait"), (1180, 820, "iPad landscape"), (1440, 900, "desktop")):
        c = b.new_context(viewport={"width":vw, "height":vh}, device_scale_factor=1); e2 = []
        pg = tpage(c, e2); go_lesson(pg, "Ray · LP605", who="Ray"); pg.wait_for_selector(".rs-blk"); pg.wait_for_timeout(200)
        wide = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
        tw = pg.evaluate("Math.round(document.querySelector('.rs-top .t').getBoundingClientRect().width)")
        hdr = pg.evaluate("document.querySelector('.rs-top').scrollWidth <= document.querySelector('.rs-top').clientWidth + 1")
        chipok = pg.evaluate("[...document.querySelectorAll('.rs-file')].every(a => a.getBoundingClientRect().right <= innerWidth && a.getBoundingClientRect().height >= 40)")
        check(wide <= 1 and hdr and tw >= (90 if vw <= 400 else 200) and chipok, "%s: no sideways scroll (%d), header fits, title %dpx wide, chips on screen and 40px+ tall" % (name, wide, tw, ))
        if name in ("phone", "iPad portrait"):
            pg.screenshot(path=os.path.join(HERE, "shots", "mat_rs_%s.png" % name.split()[0]))
            pg.click("header [data-a=pl-files]"); pg.wait_for_selector("#plFiles"); pg.wait_for_timeout(100)
            fits = pg.evaluate("(() => { const r = document.querySelector('#plFiles .pop').getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight + 1; })()")
            check(fits, "%s: the Files menu fits on screen" % name)
            pg.screenshot(path=os.path.join(HERE, "shots", "mat_files_%s.png" % name.split()[0]))
        errs += e2; c.close()
    print("errors:", errs[:5])
    check(not errs, "no page errors (and no alert from a label)")
    b.close()
done()
