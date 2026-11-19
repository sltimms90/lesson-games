"""19 Nov evening feedback: Win or Lose bets (a typed amount and All in, on a student link and a class link, through the
same live path as the other bet buttons), the Plan tab's HW Key button, and Open plan / Folder links (teacher only)."""
import json, os, re, time
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get RUN(){return UI.run},get VIEW(){return UI.view},", 1)
APP2 = lg.APP

# ---------------- Win or Lose ----------------
QZ = "\n\n".join(["Q%d: which is right?\n*right %d\nwrong %d\nalso wrong %d" % (i, i, i, i) for i in range(1, 5)])
WL = {"mode":"winlose", "timer":0, "lifelines":"none", "shuffleAns":False, "shuffleQs":False, "bonus":0}
games = [{"id":"gq","type":"quiz","title":"Win or lose","block":QZ,"options":WL}]
qpack = {"id":"mia-lp9","student":"Mia Chen","lp":9,"title":"Mia · LP9","date":"2026-11-19","updatedAt":"x","games":games,"liveRoom":"0123456789abcdef0123456789abcdef"}

def st(pg): return pg.evaluate("__T.RUN && JSON.stringify((({_animating,_rev,spinning,betDraft,...o})=>o)(__T.RUN.st))")
def wait_same(T, S, t=8):
    end = time.time() + t
    while time.time() < end:
        a, b2 = st(T), st(S)
        if a and a == b2: return True
        time.sleep(0.25)
    print("   T:", (st(T) or "")[:300]); print("   S:", (st(S) or "")[:300]); return False
def right(pg): pg.click("[data-a=qz-ans][data-i='0']"); pg.wait_for_timeout(300)
def bet_label(pg): return pg.inner_text("#qzBetGo").strip()
def typed(pg, v):
    pg.fill("#qzBetIn", ""); pg.type("#qzBetIn", v); pg.wait_for_timeout(80)

def plan_html_variants():
    here = os.path.dirname(os.path.abspath(__file__))
    sample = open(os.path.join(here, "plan_sample.html"), encoding="utf-8").read()
    hw = ("<p><strong>Key — HW11 (from HW11’s key page)</strong></p>"
          "<p><strong>Pt2:</strong> 1 couch · 2 appeared · 3 machine</p><p><strong>Pt3:</strong> 1 is used · 2 been booked</p>"
          "<p><strong>Watch:</strong> Pt4 #1 “can who fix”</p>")
    hw2 = "<p><strong>Key — HW10 (late homework)</strong></p><p>1 went · 2 saw · 3 ate</p>"
    at = "<h2>BUFFER"
    assert sample.count(at) == 1
    one = sample.replace(at, hw + at)
    two = sample.replace("<h2>SEGMENT 2", hw2 + "<h2>SEGMENT 2").replace(at, hw + at)
    fall = sample.replace(at, "<p><strong>HW11 key</strong></p><p>1 couch · 2 appeared</p>" + at)
    return sample, one, two, fall

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    errs = []
    # ===== 1. Student link, live: the student bets, the teacher's screen watches =====
    ctx = b.new_context(viewport={"width":1180, "height":820})
    db = seed_db([qpack], students=[{"id":"mia-chen","name":"Mia Chen","token":TOK}])
    T = teacher(ctx, db, errs); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
    T.click("[data-a=slink][data-g=gq]"); T.wait_for_selector("#slinkUrl"); url = T.input_value("#slinkUrl"); T.click("[data-a=slink-close]")
    # the student's phone: same browser (the mock passes Realtime over BroadcastChannel), phone-sized
    S = ctx.new_page(); S.set_viewport_size({"width":390, "height":844}); S.on("pageerror", lambda e: errs.append("S: " + str(e))); route(S)
    S.goto("https://sltimms90.github.io/lesson-games/"); S.goto(url); S.reload(); S.wait_for_selector("[data-a=s-start]"); S.wait_for_timeout(400)
    S.click("[data-a=s-start]"); S.wait_for_selector("[data-a=qz-ans]"); T.wait_for_timeout(1000)
    check(T.evaluate("__T.VIEW") == "play" and T.evaluate("__T.RUN && __T.RUN.gameId") == "gq", "student link: the teacher's app follows the student into Win or lose")
    right(S); S.wait_for_selector("[data-a=qz-betopen]")
    check(S.evaluate("__T.RUN.st.pot") == 100, "a right answer starts the pot at 100")
    S.click("[data-a=qz-betopen]"); S.wait_for_selector("#qzBetIn"); T.wait_for_timeout(500)
    check(S.locator("[data-a=qz-allin]").count() == 1 and "All in" in S.inner_text("[data-a=qz-allin]"), "All in button next to the bet buttons")
    fs = S.evaluate("parseFloat(getComputedStyle(document.getElementById('qzBetIn')).fontSize) * (parseFloat(document.querySelector('main.stage').style.zoom) || 1)")
    check(fs >= 16, "on the phone the amount box shows at 16px or more (%.1f): no iOS zoom" % fs)
    check(S.get_attribute("#qzBetIn", "inputmode") == "numeric", "the amount box brings up the number keypad")
    check(T.locator("#qzBetIn").count() == 1 and T.evaluate("document.getElementById('qzBetIn').readOnly") and T.locator("[data-a=qz-allin].ro").count() == 1, "teacher's screen watches: amount box read-only, All in not tappable")
    T.evaluate("document.querySelector('[data-a=qz-allin]').click()"); T.wait_for_timeout(400)
    check(T.evaluate("__T.RUN.st.betting") is True and S.evaluate("__T.RUN.st.betting") is True and T.evaluate("__T.RUN.st.log[0].decision") is None, "the teacher's tap on All in does nothing while watching (liveMayAct)")
    d0 = bet_label(S)
    typed(S, "1000"); check(bet_label(S) == "Bet 100" and S.inner_text("#qzBetN") == "100", "more than the pot is cut to the pot (%s)" % bet_label(S))
    for bad in ["0", "abc", "2.5", "-5"]:
        typed(S, bad); check(bet_label(S) == d0, "'%s' is ignored: the − / + bet stands (%s)" % (bad, bet_label(S)))
    typed(S, "30"); check(bet_label(S) == "Bet 30" and "bank 70" in S.inner_text("#qzBetBank"), "a typed 30 shows Bet 30 · bank 70")
    S.press("#qzBetIn", "Enter"); S.wait_for_timeout(500)
    check(S.evaluate("[__T.RUN.st.score, __T.RUN.st.pot, __T.RUN.st.i]") == [70, 30, 1], "Enter bets 30: 70 banked, 30 carried to question 2 (%s)" % S.evaluate("[__T.RUN.st.score, __T.RUN.st.pot, __T.RUN.st.i]"))
    check(S.evaluate("__T.RUN.st.log[0].decision") == "bet 30, banked 70", "the bet is logged with the question like any bet")
    check(wait_same(T, S), "the teacher's screen agrees after the typed bet")
    right(S)   # pot 30 → 60
    check(S.locator("[data-a=qz-betopen]").count() == 1, "Bet some still offered with a pot under 100 (%s)" % S.evaluate("__T.RUN.st.pot"))
    S.click("[data-a=qz-betopen]"); S.wait_for_selector("[data-a=qz-allin]")
    check(S.evaluate("__T.RUN.st.bet") >= 1, "the starting bet for a small pot is at least 1 (%s)" % S.evaluate("__T.RUN.st.bet"))
    S.click("[data-a=qz-allin]"); S.wait_for_timeout(500)
    check(S.evaluate("[__T.RUN.st.score, __T.RUN.st.pot, __T.RUN.st.i]") == [70, 60, 2], "All in bets the whole pot of 60, nothing banked (%s)" % S.evaluate("[__T.RUN.st.score, __T.RUN.st.pot, __T.RUN.st.i]"))
    check(S.evaluate("__T.RUN.st.log[1].decision") == "bet 60, banked 0 (all in)", "All in is logged: %s" % S.evaluate("__T.RUN.st.log[1].decision"))
    check(wait_same(T, S), "the teacher's screen agrees after All in")
    S.click("[data-a=qz-ans][data-i='1']"); S.wait_for_timeout(300)   # wrong: loses the 60
    check(S.evaluate("[__T.RUN.st.score, __T.RUN.st.pot]") == [70, 0], "a wrong answer after All in loses the 60")
    S.click("[data-a=qz-next]"); S.wait_for_timeout(300); right(S); S.click("[data-a=qz-next]"); S.wait_for_timeout(300)
    S.click("[data-a=finish]"); T.wait_for_timeout(1500)
    rs = T.evaluate("__T.RESULTS.filter(r => r.gameId === 'gq')")
    notes = [x.get("note", "") for x in (rs[0]["items"] if rs else [])]
    check(len(rs) == 1 and "bet 30, banked 70" in notes[0] and "bet 60, banked 0 (all in)" in notes[1], "both bets are in the saved result items: %s" % notes[:2])
    check(len(rs) == 1 and rs[0]["score"]["total"] == 170, "final score 70 + 100 = 170 (%s)" % (rs[0]["score"] if rs else None))
    S.close(); T.close()

    # ===== 2. Class link: the teacher puts the game up, the student goes All in =====
    db = seed_db([qpack], students=[{"id":"mia-chen","name":"Mia Chen","token":TOK}])
    ctx = b.new_context(viewport={"width":1180, "height":820})   # a fresh device: nothing left from part 1
    T = teacher(ctx, db, errs); go_lesson(T, "Mia · LP9"); T.wait_for_timeout(300)
    T.click("#clsBar [data-a=clink]"); T.wait_for_selector("#slinkUrl"); curl = T.input_value("#slinkUrl"); T.click("[data-a=clink-close]")
    C = student(ctx, curl, errs); C.wait_for_timeout(900)
    T.click("[data-a=play][data-g=gq]"); C.wait_for_selector("[data-a=qz-ans]", timeout=5000)
    right(C); C.click("[data-a=qz-betopen]"); C.wait_for_selector("[data-a=qz-allin]")
    typed(C, "40"); C.click("[data-a=qz-bet]"); C.wait_for_timeout(500)
    check(C.evaluate("__T.RUN.st.log[0].decision") == "bet 40, banked 60", "class link: a typed bet goes through (%s)" % C.evaluate("__T.RUN.st.log[0].decision"))
    right(C); C.click("[data-a=qz-betopen]"); C.wait_for_selector("[data-a=qz-allin]"); C.click("[data-a=qz-allin]"); C.wait_for_timeout(500)
    check(C.evaluate("__T.RUN.st.log[1].decision") == "bet 80, banked 0 (all in)", "class link: All in goes through (%s)" % C.evaluate("__T.RUN.st.log[1].decision"))
    check(wait_same(T, C), "class link: the teacher's screen shows the same bets")
    check(T.evaluate("__T.RUN.st.log.map(x => x.decision).join('|')") == "bet 40, banked 60|bet 80, banked 0 (all in)", "…in the teacher's log too")
    check(C.evaluate("!document.querySelector('a[href*=\\'drive.google.com\\'], .pl-ext, #plLinks') && !document.getElementById('app').innerHTML.includes('drive.google.com')"), "no Drive links on the student's page")
    C.close(); T.close()

    # ===== 3. Plan tab: HW Key; Open plan / Folder =====
    SAMPLE, ONE, TWO, FALL = plan_html_variants()
    DOCS = {"1PlanDocIdForTestsOnly_HWoneAAAA": ONE, "1PlanDocIdForTestsOnly_HWtwoBBBB": TWO, "1PlanDocIdForTestsOnly_HWfallCCC": FALL, "1PlanDocIdForTestsOnly_noHWDDDDD": SAMPLE}
    FOLDER = "1KitLessonPlanFolder_abcdefghij"
    spec = {"student":"Kit", "lp":12, "date":"2026-11-20", "start":"17:00", "length":32, "format":"in person",
      "blocks":[{"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up chat"}]},
                {"label":"2 EXAM Paper 1", "mins":20, "lines":[{"type":"cue", "label":"2B Read, fix"}]}, {"label":"Buffer", "mins":2, "lines":[{"type":"cue", "label":"Overrun only"}]}]}
    G = [{"id":"g1", "type":"hangman", "title":"Past words", "block":"went\nsaw\nate", "options":{}}]
    def P(i, lp, doc, rs=True):
        d = {"id":"kit-lp%d" % lp, "student":"Kit", "lp":lp, "title":"Kit · LP%d" % lp, "date":"2026-11-%02d" % (lp + 8), "updatedAt":"x", "games":G}
        if doc: d["plan"] = {"docId":doc}
        if rs: d["runsheet"] = dict(spec, lp=lp)
        return d
    packs = [P(0, 12, "1PlanDocIdForTestsOnly_HWoneAAAA"), P(1, 11, "1PlanDocIdForTestsOnly_HWtwoBBBB", False), P(2, 10, "1PlanDocIdForTestsOnly_HWfallCCC", False),
             P(3, 9, "1PlanDocIdForTestsOnly_noHWDDDDD", False), P(4, 8, None)]
    calls = []
    def tpage(c2):
        pg = c2.new_page(); pg.on("pageerror", lambda e: errs.append("T: " + str(e)))
        pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed_db(packs), "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}))
        def h(r):
            u = r.request.url
            if u.endswith("/functions/v1/plan-doc"):
                doc = json.loads(r.request.post_data or "{}").get("docId"); calls.append(doc)
                return r.fulfill(body=json.dumps({"html": DOCS[doc], "name":"Kit_LP12_20261120.docx", "modified":"2026-11-19T06:00:00Z", "folderId":FOLDER}), content_type="application/json")
            if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
            if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
            return r.abort()
        pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
        return pg
    def top_of(pg, sel): return pg.evaluate("s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top) : null; }", sel)
    def visible(pg, text):
        return pg.evaluate("""t => { const w = document.createTreeWalker(document.querySelector('.pl-doc'), NodeFilter.SHOW_TEXT); let n;
          while ((n = w.nextNode())) { const e = n.parentElement; if (n.nodeValue.includes(t) && e.getClientRects().length && !e.closest('details:not([open]) > .pl-in')) return true; } return false; }""", text)

    pc = b.new_context(viewport={"width":1024, "height":768})
    t = tpage(pc)
    go_lesson(t, "Kit · LP12"); t.wait_for_selector(".rs-blk")
    href = t.get_attribute(".rs-top a.pl-ext:has-text('Open plan')", "href") if t.locator(".rs-top a.pl-ext:has-text('Open plan')").count() else None
    check(href == "https://drive.google.com/file/d/1PlanDocIdForTestsOnly_HWoneAAAA/view", "run sheet header: Open plan → the plan file in Drive (%s)" % href)
    check(t.get_attribute(".rs-top a.pl-ext", "target") == "_blank" and "noopener" in t.get_attribute(".rs-top a.pl-ext", "rel"), "opens outside the app (new tab / Drive app), noopener")
    check(t.locator(".rs-top a:has-text('Folder')").count() == 0 and not calls, "no Folder before the plan has been fetched, and the run sheet fetches nothing")
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    check(calls == ["1PlanDocIdForTestsOnly_HWoneAAAA"], "opening the Plan tab fetches it once")
    fh = t.get_attribute(".pl-meta a:has-text('Folder')", "href") if t.locator(".pl-meta a:has-text('Folder')").count() else None
    check(fh == "https://drive.google.com/drive/folders/" + FOLDER, "Plan tab: Folder → the plan's Drive folder (%s)" % fh)
    check(t.locator(".pl-meta a:has-text('Open plan')").count() == 1, "Plan tab: Open plan too")
    check(t.evaluate("JSON.parse(localStorage.getItem('lessonGames.plan.1PlanDocIdForTestsOnly_HWoneAAAA')).folder") == FOLDER, "the folder is kept with the plan's copy on the device")
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 1 and t.inner_text(".pl-top [data-a=pl-hw]").strip() == "HW Key", "the Plan tab's header has an HW Key button")
    hk = t.locator("details.pl-key:has(summary:has-text('Key — HW11'))")
    check(hk.count() == 1 and not hk.evaluate("d => d.open"), "the HW key starts folded")
    check(not visible(t, "1 couch") and not visible(t, "can who fix"), "its Pt and Watch lines are folded with it")
    check(hk.evaluate("d => ['Pt2:', 'Pt3:', 'Watch:'].every(x => d.querySelector('.pl-in').textContent.includes(x))"), "Pt2, Pt3 and Watch lines are all inside the HW key's fold")
    t.evaluate("window.scrollTo(0, 0)"); t.wait_for_timeout(300)
    t.click(".pl-top [data-a=pl-hw]"); t.wait_for_timeout(500)
    y = top_of(t, "details.pl-key[id^=pl-hw]")
    check(hk.evaluate("d => d.open") and visible(t, "1 couch") and visible(t, "can who fix"), "HW Key unfolds the homework key")
    check(y is not None and 40 <= y <= 110, "…and scrolls it clear of the header (top %s)" % y)
    t.wait_for_timeout(600)
    sy = t.evaluate("scrollY"); saved = t.evaluate("(__T.UI.scr || {})['plan|kit-lp12']")
    check(sy > 300 and saved is not None and abs(saved - sy) <= 2, "the saved place is where the key is (%s vs %s)" % (saved, sy))
    check(t.locator("#plHwMenu").count() == 0, "one HW key: no menu")
    t.click("[data-a=pl-back]"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(200)
    fh2 = t.get_attribute(".rs-top a:has-text('Folder')", "href") if t.locator(".rs-top a:has-text('Folder')").count() else None
    check(fh2 == "https://drive.google.com/drive/folders/" + FOLDER, "back on the run sheet, Folder now shows in the header too (%s)" % fh2)
    t.click(".rs-top [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(300)
    check(abs(t.evaluate("scrollY") - sy) <= 2, "📖 reopens the plan at the HW key (%s vs %s)" % (t.evaluate("scrollY"), sy))
    # phone: the run sheet header still fits
    t.set_viewport_size({"width":390, "height":844}); t.click("[data-a=pl-back]"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(300)
    wide = t.evaluate("document.querySelector('.rs-top').scrollWidth <= document.querySelector('.rs-top').clientWidth + 1 && document.documentElement.scrollWidth <= innerWidth + 1")
    lbl = t.evaluate("[...document.querySelectorAll('.rs-top .pl-ext .lbl')].every(e => !e.getClientRects().length)")
    check(wide and lbl, "phone: the run sheet header fits, Open plan / Folder as 📄 📁 icons")
    check(t.evaluate("[...document.querySelectorAll('.rs-top a.pl-ext')].every(a => a.getAttribute('aria-label'))"), "icon links keep their names for VoiceOver")
    t.screenshot(path=HERE + "/shots/fb_rs_phone.png")
    t.set_viewport_size({"width":1024, "height":768})
    # two HW keys → a small menu
    t.click("[data-a=rs-games]"); t.wait_for_selector(".head h2"); go_lesson(t, "Kit · LP11"); t.wait_for_selector(".head h2")
    t.click(".row [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    t.click(".pl-top [data-a=pl-hw]"); t.wait_for_selector("#plHwMenu")
    items = t.locator("#plHwMenu [data-a=pl-hw]").all_inner_texts()
    check(len(items) == 2 and "HW10" in items[0] and "HW11" in items[1], "two HW keys: a menu lists each by its heading %s" % items)
    t.click("#plHwMenu [data-a=pl-hw] >> nth=1"); t.wait_for_timeout(400)
    y = top_of(t, "#pl-hw-2"); d2 = t.evaluate("document.getElementById('pl-hw-2').open"); d1 = t.evaluate("document.getElementById('pl-hw-1').open")
    check(t.locator("#plHwMenu").count() == 0 and d2 and not d1 and y is not None and 40 <= y <= 110, "picking HW11 closes the menu, unfolds that key only (top %s)" % y)
    check(t.evaluate("document.getElementById('pl-hw-1').textContent.includes('1 went')") and not t.evaluate("document.getElementById('pl-hw-1').textContent.includes('Pt2')"), "the next 'Key — HW' line starts its own key")
    # fallback: a key whose heading says HW
    t.click("[data-a=pl-back]"); t.wait_for_selector(".head h2"); go_lesson(t, "Kit · LP10"); t.wait_for_selector(".head h2")
    t.click(".row [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 1, "no 'Key — HW' line: a key headed 'HW11 key' still gets the button")
    t.click(".pl-top [data-a=pl-hw]"); t.wait_for_timeout(400)
    check(visible(t, "1 couch"), "…and it unfolds")
    # no HW key: no button
    t.click("[data-a=pl-back]"); t.wait_for_selector(".head h2"); go_lesson(t, "Kit · LP9"); t.wait_for_selector(".head h2")
    t.click(".row [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(200)
    check(t.locator("[data-a=pl-hw]").count() == 0 and t.locator("details.pl-key").count() == 2, "a plan with no homework key: no HW Key button, other keys as before")
    # no plan: no links
    t.click("[data-a=pl-back]"); t.wait_for_selector(".head h2"); go_lesson(t, "Kit · LP8"); t.wait_for_selector(".rs-blk")
    check(t.locator(".pl-ext").count() == 0 and t.locator("#plLinks").count() == 0, "a lesson with no plan: no Open plan / Folder")
    check("drive.google.com" not in json.dumps(t.evaluate("__MOCK.db")), "nothing about the Drive links goes into the database")

    print("errors:", errs[:5])
    check(not errs, "no page errors")
    b.close()
done()
