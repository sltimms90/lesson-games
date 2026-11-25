"""Plan tab (Nov 2026): the lesson plan, read-only, teacher only.
Fetched through the plan-doc function (routed here to plan_sample.html), kept on the device, ↻ fetches again;
jumps from run sheet lines, outline, scroll kept per lesson (also after a reload), keys and trap answers folded,
the file's HTML can't run code, paste-a-link for older lessons, and the student page never gets any of it."""
import json, os, re
from lg import *
SAMPLE = open(os.path.join(HERE, "plan_sample.html"), encoding="utf-8").read()
DOC = "1PlanDocIdForTestsOnly_abcdefghij"
FN = "**/functions/v1/plan-doc"
APP2 = APP.replace("window.__T={", "window.__T={get SMODE(){return SMODE},", 1)
spec = {"student":"Kit", "lp":12, "date":"2026-11-20", "start":"17:00", "length":42, "format":"in person",
  "blocks":[
    {"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up chat"}, {"type":"trap", "spring":"Where did you go yesterday?"}, {"type":"cue", "label":"0B Spelling test"}]},
    {"label":"1 Teaching Notes: past simple", "mins":15, "lines":[{"type":"cue", "label":"1A Went, saw, ate"}, {"type":"score", "label":"1B Bomb Squad said", "n":2}]},
    {"label":"2 EXAM Paper 1", "mins":15, "lines":[{"type":"cue", "label":"2A The paper"}, {"type":"score", "label":"2A Grammar", "n":10}, {"type":"cue", "label":"2B Read, fix"}]},
    {"label":"Buffer", "mins":2, "lines":[{"type":"cue", "label":"Overrun only"}]}]}
pack = {"id":"kit-lp12", "student":"Kit", "lp":12, "title":"Kit · LP12", "date":"2026-11-20", "updatedAt":"x", "runsheet":spec, "plan":{"docId":DOC}, "materials":[{"t":"Pathways 3 U3R2 SecretLabel", "id":"1MaterialFileIdLeakCheck_xyz", "p":"p.62–63", "seg":["1", "2"]}],
  "liveRoom":"0123456789abcdef0123456789abcdef",
  "games":[{"id":"g1", "type":"hangman", "title":"Past words", "block":"went\nsaw\nate", "options":{}}]}
old = {"id":"kit-lp11", "student":"Kit", "lp":11, "title":"Kit · LP11", "date":"2026-11-13", "updatedAt":"x", "games":[{"id":"g1", "type":"hangman", "title":"Words", "block":"cat\ndog", "options":{}}]}

def serve(pg, calls, html=lambda n: SAMPLE, status=lambda n: 200):
    def h(r):
        n = len(calls) + 1
        calls.append({"auth": r.request.headers.get("authorization"), "apikey": r.request.headers.get("apikey"), "body": r.request.post_data, "method": r.request.method})
        if status(n) == 0: return r.abort()
        if status(n) != 200: return r.fulfill(status=status(n), body=json.dumps({"error":"not_found"}), content_type="application/json")
        return r.fulfill(body=json.dumps({"html": html(n), "name":"Kit_LP12_20261120.docx", "modified":"2026-11-19T06:00:00Z"}), content_type="application/json")
    pg.route(FN, h)
def tpage(ctx, db, errs, calls, **kw):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("T: " + str(e)))
    pg.add_init_script("if(!sessionStorage.getItem('seeded')){ sessionStorage.setItem('seeded','1'); window.__MOCK = %s; } else window.__MOCK = JSON.parse(sessionStorage.getItem('mock') || 'null') || %s;" % ((json.dumps({"db":db, "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}),) * 2))
    def h(r):
        u = r.request.url
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); serve(pg, calls, **kw)
    pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg
def visible(pg, text):
    return pg.evaluate("""t => { const w = document.createTreeWalker(document.querySelector('.pl-doc'), NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const e = n.parentElement; if (n.nodeValue.includes(t) && e.getClientRects().length && !e.closest('details:not([open]) > .pl-in')) return true; } return false; }""", text)
def top_of(pg, sel):
    return pg.evaluate("s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top) : null; }", sel)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1024, "height":768}); errs = []; calls = []
    edits = {"n": 0}
    t = tpage(ctx, seed_db([pack, old]), errs, calls, html=lambda n: SAMPLE if n < 2 else SAMPLE.replace("Overrun only.", "Overrun only. EDITED"))
    go_lesson(t, "Kit · LP12"); t.wait_for_selector(".rs-blk")
    check(t.evaluate("__T.UI.view") == "sheet", "the lesson opens on its run sheet")
    check(t.locator(".rs-top [data-a=pl-open]").count() == 1 and t.locator(".rs-top [data-a=pl-open]").inner_text().strip() == "📖", "run sheet header has the 📖 Plan button (icon only)")
    check(not calls, "nothing is fetched until the plan is opened")
    # jump from a run sheet line
    t.click(".rs-tx.pl-j:has-text('2A The paper')"); t.wait_for_selector("#pl-step-2A", timeout=4000); t.wait_for_timeout(300)
    check(len(calls) == 1 and calls[0]["auth"] == "Bearer TOK" and calls[0]["apikey"] and json.loads(calls[0]["body"]) == {"docId": DOC}, "first open fetches the doc with the teacher's sign-in %s" % calls[:1])
    y = top_of(t, "#pl-step-2A"); check(y is not None and 40 <= y <= 110, "tapping '2A The paper' lands on the plan's 2A heading (top %s)" % y)
    check(re.search(r"fetched \d\d:\d\d", t.inner_text(".pl-meta")) is not None, "shows 'fetched HH:MM' (%s)" % t.inner_text(".pl-meta"))
    check(t.locator(".pl-doc h2#pl-seg-1").count() == 1 and t.locator(".pl-doc h3#pl-step-1B").count() == 1, "segment and step headings get anchors")
    check(t.locator(".pl-doc b:has-text('Rules.')").count() >= 1, "bold labels kept")
    check(t.evaluate("[...document.querySelectorAll('.pl-doc *')].filter(e => !e.matches('button.pl-game')).every(e => [...e.attributes].every(a => ['id','class','open','colspan','rowspan'].includes(a.name) || (a.name === 'title' && e.tagName === 'SUMMARY') || (e.matches('h2.pl-rs, h3.pl-rs') && ['role','tabindex','title','data-a','data-c','data-s'].includes(a.name))))"), "no attributes from the file (no styles; only the app's own 🎲 buttons and run sheet headings carry data-a)")
    check(t.evaluate("[...document.querySelectorAll('.pl-doc [data-a]')].every(e => e.matches('button.pl-game[data-a=pl-play], h2.pl-rs[data-a=pl-rs], h3.pl-rs[data-a=pl-rs]'))"), "…and data-a only ever pl-play (chips) or pl-rs (headings)")
    # folds
    check(t.locator("details.pl-key").count() == 2 and t.evaluate("[...document.querySelectorAll('details.pl-key')].every(d => !d.open)"), "both keys start folded")
    check(not visible(t, "watch: goed") and not visible(t, "She ate rice"), "key answers hidden")
    check(visible(t, "Accept said") is False, "the line after a key (accepted answers) is folded with it")
    check(t.locator("details.pl-ans").count() == 3 and not visible(t, "“I went to the park.”") and not visible(t, "the zoo") and not visible(t, "“I go to the park.”"), "trap Right / Also right / Expect folded")
    check(visible(t, "Where did you go yesterday?") and visible(t, "Yesterday is past"), "trap Spring and After a miss stay open")
    check(visible(t, "Hand the paper") and visible(t, "Done when:"), "teacher's words stay open")
    t.click("details.pl-key >> nth=1 >> summary"); t.wait_for_timeout(100)
    check(visible(t, "watch: goed"), "a key opens on a tap")
    # scroll memory: plan ↔ run sheet ↔ games
    t.evaluate("window.scrollTo(0, 900)"); t.wait_for_timeout(600); py = t.evaluate("scrollY")
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk")
    t.evaluate("window.scrollTo(0, 260)"); t.wait_for_timeout(600)
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    check(abs(t.evaluate("scrollY") - py) <= 2, "📖 reopens the plan where it was left (%s vs %s)" % (t.evaluate("scrollY"), py))
    check(len(calls) == 1, "reopening uses the copy on the device (no new fetch)")
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(200)
    check(abs(t.evaluate("scrollY") - 260) <= 2, "back on the run sheet at the same place (%s)" % t.evaluate("scrollY"))
    t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2"); t.evaluate("window.scrollTo(0, 120)"); t.wait_for_timeout(600)
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(200)
    check(abs(t.evaluate("scrollY") - 260) <= 2, "run sheet → games → run sheet keeps the run sheet's place (%s)" % t.evaluate("scrollY"))
    t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2"); t.wait_for_timeout(200)
    check(abs(t.evaluate("scrollY") - 120) <= 2, "the games page keeps its place too (%s)" % t.evaluate("scrollY"))
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    check(abs(t.evaluate("scrollY") - py) <= 2, "📖 on the games page opens the same place in the plan")
    t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2"); check(t.evaluate("__T.UI.view") == "pack", "🎲 from the plan goes to the games page")
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk")
    # segment bar, a score line, Buffer
    t.click(".rs-bar b.pl-j:has-text('1 Teaching Notes')"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    y = top_of(t, "#pl-seg-1"); check(y is not None and 40 <= y <= 110, "a segment bar opens the plan at SEGMENT 1 (top %s)" % y)
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk")
    t.click(".pl-j:has-text('1B Bomb Squad said')"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    y = top_of(t, "#pl-step-1B"); check(y is not None and 40 <= y <= 110, "a score line ('1B …') opens the plan at 1B (top %s)" % y)
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk")
    t.click(".rs-tx.pl-j:has-text('Overrun only')"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    y = top_of(t, "#pl-h-buffer-2-min-17-40-17-42"); check(y is not None and 40 <= y <= 110, "a line in the Buffer block opens the plan at BUFFER (top %s)" % y)
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk")
    t.click(".rs-tx.pl-j:has-text('Where did you go')"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    y = top_of(t, "#pl-step-0A"); check(y is not None and 40 <= y <= 110, "the trap line under 0A opens the plan at 0A (top %s)" % y)
    # outline
    t.click("[data-a=pl-outline]"); t.wait_for_selector("#plOut")
    items = t.locator("#plOut .pl-out button").all_inner_texts()
    check(any(x.startswith("SEGMENT 2") for x in items) and any(x.startswith("2B ·") for x in items) and t.locator("#plOut li.l2").count() >= 6, "outline lists segments and sub-steps (%d)" % len(items))
    t.click("#plOut button:has-text('1B ·')"); t.wait_for_timeout(200)
    y = top_of(t, "#pl-step-1B"); check(t.locator("#plOut").count() == 0 and 40 <= y <= 110, "outline jumps to 1B (top %s)" % y)
    # reload while on the plan: the copy on the device, same place, no fetch
    t.evaluate("window.scrollTo(0, 700)"); t.wait_for_timeout(600); ry = t.evaluate("scrollY")
    t.evaluate("sessionStorage.setItem('mock', JSON.stringify(window.__MOCK))")
    t.reload(); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(300)
    check(t.evaluate("__T.UI.view") == "plan" and abs(t.evaluate("scrollY") - ry) <= 2, "after a reload the plan reopens at the same place (%s vs %s)" % (t.evaluate("scrollY"), ry))
    check(len(calls) == 1, "…from the copy on the device (no fetch)")
    # refresh (the "fetched" chip under the header): tapped where the page is, without the test scrolling to it
    t.evaluate("document.querySelector('.pl-meta [data-a=pl-refresh]').click()"); t.wait_for_function("document.querySelector('.pl-doc') && document.querySelector('.pl-doc').textContent.includes('EDITED')", timeout=4000)
    check(len(calls) == 2 and abs(t.evaluate("scrollY") - ry) <= 2, "↻ fetches it again and keeps the place")
    # a failed refresh keeps the copy
    t.unroute(FN); serve(t, calls, status=lambda n: 0)
    t.click("[data-a=pl-refresh]"); t.wait_for_selector(".notice[role=alert]")
    check("no connection" in t.inner_text(".notice[role=alert]") and "copy on this device" in t.inner_text(".notice[role=alert]") and t.locator(".pl-doc").count() == 1, "offline ↻: says so, keeps showing the copy (%s)" % t.inner_text(".notice[role=alert]"))
    t.unroute(FN); serve(t, calls)
    # an older lesson without a doc id: paste the link once
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk"); t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2")
    t.click("[data-a=student]"); t.wait_for_timeout(200); t.click("text=Kit · LP11"); t.wait_for_selector(".head h2:has-text('LP11')")
    check(t.locator(".pl-j").count() == 0, "no run sheet links without a plan")
    n0 = len(calls); t.click("header.nav [data-a=pl-open]"); t.wait_for_selector("#plLink")
    check(len(calls) == n0, "no doc id: nothing fetched, it asks for the link")
    t.fill("#plLink", "not a link"); t.click("[data-a=pl-save]"); check("doesn’t look like" in t.inner_text("#plErr"), "a bad link is refused")
    t.fill("#plLink", "https://docs.google.com/document/d/1OlderLessonDocId_0123456789xyz/edit?usp=sharing"); t.click("[data-a=pl-save]")
    t.wait_for_selector(".pl-doc"); t.wait_for_timeout(300)
    saved = t.evaluate("window.__MOCK.db.packs['kit-lp11'].data.plan")
    check(saved == {"docId":"1OlderLessonDocId_0123456789xyz"} and json.loads(calls[-1]["body"])["docId"] == "1OlderLessonDocId_0123456789xyz", "the pasted link's id is saved on the lesson and fetched (%s)" % saved)
    t.click("[data-a=pl-outline]"); t.click("#plOut [data-a=pl-edit]"); t.wait_for_selector("#plLink")
    t.fill("#plLink", "https://drive.google.com/file/d/1KgpOtherDocIdABCDEFGHIJKLMNO/view?usp=drivesdk"); t.click("[data-a=pl-save]"); t.wait_for_selector(".pl-doc")
    check(t.evaluate("window.__MOCK.db.packs['kit-lp11'].data.plan.docId") == "1KgpOtherDocIdABCDEFGHIJKLMNO", "the link can be changed (Drive file link works too)")
    # refusals and errors from the function
    t.unroute(FN); serve(t, calls, status=lambda n: 404)
    t.click("[data-a=pl-refresh]"); t.wait_for_selector(".notice[role=alert]")
    check("Share the folder" in t.inner_text(".notice[role=alert]"), "a file not shared with the plan reader says what to do")
    t.unroute(FN)
    check(not errs, "no page errors %s" % errs[:3])
    t.close()

    # the file's HTML never runs code or brings its attributes in
    errs2 = []; calls2 = []
    EVIL = ('<style>.c1{font-weight:700}.c2{font-style:italic}</style><h2 onclick="window.__pwn=1">SEGMENT 2 — EVIL</h2>'
      '<p><span class="c1">Bold by class</span> <span class="c2">italic by class</span> <span style="font-weight:700">bold by style</span></p>'
      '<p><img src=x onerror="window.__pwn=2"><script>window.__pwn=3</script><a href="javascript:window.__pwn=4" id="lnk">a link</a>'
      '<iframe src="javascript:window.__pwn=5"></iframe><svg onload="window.__pwn=6"></svg><b style="color:red" onmouseover="window.__pwn=7">x</b></p>'
      '<table><tr><td colspan="2" onclick="x">cell</td></tr></table><p>&lt;img src=x onerror=window.__pwn=8&gt;</p>')
    ctx2 = b.new_context(viewport={"width":1024, "height":768})
    t2 = tpage(ctx2, seed_db([pack]), errs2, calls2, html=lambda n: EVIL)
    go_lesson(t2, "Kit · LP12"); t2.wait_for_selector(".rs-blk"); t2.click(".rs-top [data-a=pl-open]"); t2.wait_for_selector(".pl-doc"); t2.wait_for_timeout(500)
    if t2.locator("a").count(): t2.click(".pl-doc >> text=a link")
    t2.hover(".pl-doc b >> nth=-1"); t2.click(".pl-doc h2"); t2.wait_for_timeout(300)
    check(t2.evaluate("__T.UI.view") == "sheet" and t2.locator(".pl-doc").count() == 0, "the SEGMENT 2 heading is the app's run sheet link (its own onclick is gone)")
    t2.click("header.nav [data-a=pl-open]"); t2.wait_for_selector(".pl-doc"); t2.wait_for_timeout(300)
    check(t2.evaluate("window.__pwn") is None, "nothing in the file runs (%s)" % t2.evaluate("window.__pwn"))
    check(t2.locator(".pl-doc img, .pl-doc script, .pl-doc iframe, .pl-doc svg, .pl-doc a, .pl-doc [style], .pl-doc [onclick]").count() == 0, "no images, scripts, frames, links, styles or handlers")
    check(t2.locator(".pl-doc b:has-text('Bold by class')").count() == 1 and t2.locator(".pl-doc i:has-text('italic by class')").count() == 1 and t2.locator(".pl-doc b:has-text('bold by style')").count() == 1, "Google Docs' bold/italic classes and styles become plain bold/italic")
    check(t2.locator(".pl-doc td[colspan='2']").count() == 1 and "<img src=x" in t2.inner_text(".pl-doc"), "table spans kept; escaped text stays text")
    ctx2.close()

    # students: the plan never reaches a student link, a class link or the student page
    errs3 = []; calls3 = []
    ctx3 = b.new_context(viewport={"width":1024, "height":768})
    NDOC = "1NotesDocIdLeakCheck_abcdefg"   # Kit's notes doc (students/kit.notes_doc, 25 Nov): teacher only, like the materials
    t3 = tpage(ctx3, seed_db([pack], students=[{"id":"kit", "name":"Kit", "look":"chalk", "notes_doc":NDOC, "updatedAt":"x"}]), errs3, calls3)
    go_lesson(t3, "Kit · LP12"); t3.wait_for_selector(".rs-blk")
    t3.click("header [data-a=pl-files]"); t3.wait_for_selector("#plFiles")
    check(NDOC in (t3.get_attribute("#plFiles a:has-text('Notes doc')", "href") or ""), "leak check is live: the teacher's Files menu has Kit's notes doc")
    t3.click("#plFiles button[data-a=pl-files-x]"); t3.wait_for_timeout(100)
    t3.click(".rs-tx.pl-j:has-text('0A Warm-up')"); t3.wait_for_selector(".pl-doc")
    t3.click("[data-a=nav-games]"); t3.wait_for_selector(".head h2")
    t3.click("[data-a=slink][data-g=g1]"); t3.wait_for_function("document.getElementById('slinkUrl') && document.getElementById('slinkUrl').value.length > 20")
    slink = t3.input_value("#slinkUrl"); t3.click("[data-a=slink-close]")
    t3.click("#clsBar [data-a=clink]"); t3.wait_for_selector("#slinkUrl"); clink = t3.input_value("#slinkUrl"); t3.click("[data-a=clink-close]")
    REC = "window.__BC=[]; (function(){ const O = window.BroadcastChannel; window.BroadcastChannel = function(n){ const c = new O(n); c.addEventListener('message', e => window.__BC.push(JSON.stringify(e.data))); return c; }; })();"
    secrets = [DOC, "Bomb Squad", "watch: goed", "I went to the park", "plan-doc", "1MaterialFileIdLeakCheck_xyz", "SecretLabel", NDOC, "notes_doc"]   # the plan, the lesson's materials (Nov 2026), the notes doc (25 Nov)
    for name, url in (("student link", slink), ("class link", clink)):
        s = ctx3.new_page(); s.on("pageerror", lambda e: errs3.append("S: " + str(e))); s.add_init_script(REC)
        sreq = []; s.on("request", lambda r: sreq.append(r.url))
        def sh(r):
            u = r.request.url
            if u.endswith("supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
            if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
            return r.abort()
        s.route("**/*", sh); s.goto(url); s.wait_for_timeout(900)
        if name == "class link":
            if t3.evaluate("__T.UI.view") != "play": t3.click("[data-a=play][data-g=g1]")   # (it may already follow the student-link game); s.wait_for_function("() => __T.UI.run && __T.UI.run.gameId === 'g1'", timeout=6000); t3.wait_for_timeout(500)
            t3.click("[data-a=finish-ask]"); t3.click("[data-a=discard]"); t3.wait_for_timeout(400)
        elif s.locator("[data-a=s-start]").count(): s.click("[data-a=s-start]"); s.wait_for_timeout(500)
        data = s.evaluate("JSON.stringify({ html: document.documentElement.outerHTML, smode: __T.SMODE, packs: __T.PACKS, ui: __T.UI, ls: Object.assign({}, localStorage), bc: window.__BC })")
        leaks = [x for x in secrets if x in data and not (x == "plan-doc" and False)]
        # the page source itself contains the app's code (which names the function); look at what the page holds and shows
        held = json.dumps(json.loads(data)["smode"]) + json.dumps(json.loads(data)["packs"]) + json.dumps(json.loads(data)["ui"]) + json.dumps(json.loads(data)["bc"]) + s.inner_text("body")
        check(not [x for x in secrets if x in held], "%s: no plan id or plan text in what the student page holds, shows or receives %s" % (name, [x for x in secrets if x in held]))
        check(not [u for u in sreq if "plan-doc" in u or "/functions/" in u], "%s: the student page never calls the plan function" % name)
        s.evaluate("__T.UI.view = 'plan'; __T.UI.packId = 'kit-lp12'"); s.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        s.evaluate("(() => { try { document.querySelector('[data-a]') && 0; } catch(e){} })()")
        check(s.locator(".pl-doc, [data-a=pl-open], .pl-j, #plLink, [data-a=pl-files], #plFiles, .rs-files, [data-a=pl-openall], #ndSec, #ndIn").count() == 0, "%s: no Plan tab, plan or Files links, Open all, material chips or notes doc on the student page" % name)
        s.close()
    # in the live game, nothing the teacher sends carries the plan
    check(t3.evaluate("JSON.stringify(__T.UI.run || {})").find(DOC) == -1, "the teacher's game state has no plan id")
    check(t3.evaluate("JSON.stringify(__T.UI.run || {})").find("1MaterialFileIdLeakCheck_xyz") == -1, "…and no material ids")
    check(t3.evaluate("JSON.stringify(__T.UI.run || {})").find(NDOC) == -1, "…and no notes doc")
    # the student page, forced onto the plan view with the teacher's plan copy on the device, still shows no plan
    s = ctx3.new_page(); s.add_init_script("localStorage.setItem('lessonGames.student.v1', JSON.stringify({ view:'plan', packId:'kit-lp12' }));")
    s.route("**/*", lambda r: r.fulfill(body=MOCK, content_type="application/javascript") if r.request.url.endswith("supabase.js") else (r.fulfill(body=APP2, content_type="text/html") if "/lesson-games/" in r.request.url else r.abort()))
    s.goto(slink); s.wait_for_timeout(800)
    check(s.evaluate("Object.keys(localStorage).some(k => k.startsWith('lessonGames.plan.'))") and s.locator(".pl-doc, [data-a=pl-open]").count() == 0 and "Bomb Squad" not in s.inner_text("body"), "student page with a plan copy on the same device and view=plan: no plan shown")
    s.close()
    check(not errs3, "no page errors %s" % errs3[:3])
    ctx3.close()

    # readable on iPad and phone: one column, nothing wider than the screen
    for vw, vh, name in ((820, 1180, "iPad portrait"), (1180, 820, "iPad landscape"), (390, 844, "phone")):
        c = b.new_context(viewport={"width":vw, "height":vh}, device_scale_factor=1); e4 = []; c4 = []
        pg = tpage(c, seed_db([pack]), e4, c4); go_lesson(pg, "Kit · LP12"); pg.wait_for_selector(".rs-blk")
        pg.click(".rs-tx.pl-j:has-text('1A Went')"); pg.wait_for_selector(".pl-doc"); pg.wait_for_timeout(300)
        wide = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
        fs = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.pl-doc p')).fontSize)")
        check(wide <= 1 and fs >= 18, "%s: no sideways scroll (%d), text %spx" % (name, wide, fs))
        if name == "iPad portrait": pg.screenshot(path=os.path.join(HERE, "plan_ipad.png"))
        c.close()
done()
