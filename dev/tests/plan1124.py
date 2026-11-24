"""24 Nov 2026: Plan tab fixes and plan → game / run sheet links (teacher only).
 1. a whole-bold "Key — …" heading folds at any length (Austin LP28's two long keys used to render open);
    sweep: every bold line starting "Key" in the three 23 Nov plans ends up inside details.pl-key
 2. HW Key also finds a key under a homework step ("2B · HW27 fixes" + a bold "Key", Justin LP28); Lucas unchanged
 3a. Lesson Games “title” in the plan → a 🎲 chip that opens that game (as the run sheet's Play), back returns to the plan
 3b. each step / segment heading is itself the link (no 📋 since 24 Nov b) → the run sheet at that step's line, else its block,
     else a toast; not on a drag / text selection / long press; Enter works
 4. HW Key fallback (24 Nov b): no homework key in the plan → the previous lesson's (same student, latest earlier date)
    last "HWnn" material, as a menu link "🔑 Open <t> (key at the end)"; none → no button; the plan's own key wins
 3c. none of it reaches a student link, a class link or live messages
Fixtures: plan_1124.py (sanitised copies of the relevant parts of the three plans)."""
import json, os, re
from lg import *
from plan_1124 import LUCAS, AUSTIN, JUSTIN
APP2 = APP.replace("window.__T={", "window.__T={get SMODE(){return SMODE},", 1)
DOCS = {"1PlanLucasLP313_ForTestsOnlyAAAA": LUCAS, "1PlanAustinLP28_ForTestsOnlyBBBB": AUSTIN, "1PlanJustinLP28_ForTestsOnlyCCCC": JUSTIN,
        "1PlanKaiLP5_NoHWKey_ForTestsOnlyDD": AUSTIN}
HW27 = "1xdIOsEJg7jdynHSOkXKXjiZve4fuqWwP"   # austin-lp27's homework file (key on the last page)
def MAT(t, i, seg="4", pg=None): return dict({"t":t, "id":i, "seg":[seg]}, **({"p":pg} if pg else {}))
def HG(i, title): return {"id":"g%d" % i, "type":"hangman", "title":title, "block":"went\nsaw\nate", "options":{}}
def cue(l): return {"type":"cue", "label":l}
packs = [
  {"id":"leo-lp313", "student":"Leo", "lp":313, "title":"Leo · LP313", "date":"2026-11-23", "updatedAt":"x", "plan":{"docId":"1PlanLucasLP313_ForTestsOnlyAAAA"},
   "games":[HG(1, "LP313 Taboo"), HG(2, "LP313 Spelling")],
   "runsheet":{"student":"Leo", "lp":313, "date":"2026-11-23", "start":"10:00", "length":22, "blocks":[
     {"label":"0 Arrival", "mins":10, "lines":[cue("0A HW312 check"), cue("0B Spelling")]}, {"label":"1 Game: Taboo", "mins":10, "lines":[cue("1A Taboo")]}, {"label":"Buffer", "mins":2, "lines":[cue("Overrun only")]}]}},
  {"id":"ari-lp28", "student":"Ari", "lp":28, "title":"Ari · LP28", "date":"2026-11-23", "updatedAt":"x", "plan":{"docId":"1PlanAustinLP28_ForTestsOnlyBBBB"},
   "games":[HG(1, "Dog Days Quiz"), HG(2, "S9 Spelling Test"), HG(3, "Examiner's Traps"), HG(4, "U3–U4 Taboo")]},
  # HW Key fallback: the previous lesson (same student, latest date before) has the homework file in its materials
  {"id":"ari-lp27", "student":"Ari", "lp":27, "title":"Ari · LP27", "date":"2026-11-16", "updatedAt":"x", "games":[],
   "materials":[MAT("WS27 p.1", "1WorksheetWS27_abcdefghij"), MAT("Austin_HW27_20261116", HW27, pg="key on the last page")]},
  {"id":"ari-lp26", "student":"Ari", "lp":26, "title":"Ari · LP26", "date":"2026-11-09", "updatedAt":"x", "games":[], "materials":[MAT("Austin_HW26_20261109", "1OlderHW26file_abcdefghij")]},
  {"id":"ari-nodate", "student":"Ari", "lp":99, "title":"Ari · no date", "updatedAt":"x", "games":[], "materials":[MAT("Austin_HW99", "1NoDateHW99file_abcdefghij")]},
  {"id":"ari-lp29", "student":"Ari", "lp":29, "title":"Ari · LP29", "date":"2026-11-30", "updatedAt":"x", "games":[], "materials":[MAT("Austin_HW29_20261130", "1LaterHW29file_abcdefghijk")]},
  {"id":"bo-lp28", "student":"Bo", "lp":28, "title":"Bo · LP28", "date":"2026-11-23", "updatedAt":"x", "games":[], "materials":[MAT("Bo_HW28", "1BoOtherStudentHW_abcdefg")]},
  {"id":"kai-lp5", "student":"Kai", "lp":5, "title":"Kai · LP5", "date":"2026-11-23", "updatedAt":"x", "plan":{"docId":"1PlanKaiLP5_NoHWKey_ForTestsOnlyDD"}, "games":[]},
  {"id":"kai-lp4", "student":"Kai", "lp":4, "title":"Kai · LP4", "date":"2026-11-16", "updatedAt":"x", "games":[], "materials":[MAT("Kai worksheet 4", "1KaiWorksheet4_abcdefghij")]},
  {"id":"kai-lp3", "student":"Kai", "lp":3, "title":"Kai · LP3", "date":"2026-11-09", "updatedAt":"x", "games":[], "materials":[MAT("Kai_HW3", "1KaiHW3file_abcdefghijk")]},
  {"id":"leo-lp312", "student":"Leo", "lp":312, "title":"Leo · LP312", "date":"2026-11-16", "updatedAt":"x", "games":[], "materials":[MAT("Lucas_HW312", "1LucasHW312file_abcdefghij")]},
  {"id":"jo-lp28", "student":"Jo", "lp":28, "title":"Jo · LP28", "date":"2026-11-23", "updatedAt":"x", "plan":{"docId":"1PlanJustinLP28_ForTestsOnlyCCCC"},
   "games":[HG(1, "Set 6 test"), HG(2, "Verb Bingo")], "liveRoom":"0123456789abcdef0123456789abcdef",
   "runsheet":{"student":"Jo", "lp":28, "date":"2026-11-23", "start":"19:00", "length":60, "blocks":[
     {"label":"0 Arrival", "mins":10, "lines":[cue("0A Warm-up"), cue("0B Set 6 test")]},
     {"label":"1 SPINE Task: the police file", "mins":30, "lines":[cue("1A The photo")] + [cue("1B P.15 draft")] + [{"type":"box", "text":"draft line %d" % i} for i in range(14)]},
     {"label":"2 GAME: Verb Bingo", "mins":8, "lines":[{"type":"app", "label":"2A Verb Bingo", "game":"g2"}] + [{"type":"box", "text":"call %d" % i} for i in range(8)] + [cue("2B HW27 fixes"), {"type":"box", "text":"4, 8, 9 fixed"}]},
     {"label":"3 New book test", "mins":4, "lines":[cue("Cold read")]},
     {"label":"Buffer", "mins":8, "lines":[cue("Overrun only")]}]}}]

def tpage(ctx, errs, calls):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("T: " + str(e)))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed_db(packs), "session":{"user":{"email":"t@x"}, "access_token":"TOK"}}))
    def h(r):
        u = r.request.url
        if u.endswith("/functions/v1/plan-doc"):
            d = json.loads(r.request.post_data or "{}").get("docId"); calls.append(d)
            return r.fulfill(body=json.dumps({"html": DOCS[d], "name":"plan.docx", "modified":"2026-11-23T01:00:00Z"}), content_type="application/json")
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg
def open_plan(t, title):
    go_lesson(t, title); t.wait_for_selector(".rs-blk, .head h2")
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc", timeout=5000); t.wait_for_timeout(250)
def top_of(pg, sel):
    return pg.evaluate("s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top) : null; }", sel)
def visible(pg, text):
    return pg.evaluate("""t => { const w = document.createTreeWalker(document.querySelector('.pl-doc'), NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const e = n.parentElement; if (n.nodeValue.includes(t) && e.getClientRects().length && !e.closest('details:not([open]) > .pl-in')) return true; } return false; }""", text)
def bold_keys(html): return len(re.findall(r"<p><strong>Key\b", html))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []; calls = []
    t = tpage(ctx, errs, calls)

    # ===== 1. Austin: long key headings fold =====
    open_plan(t, "Ari · LP28")
    sums = t.locator("details.pl-key > summary").all_inner_texts()
    check(any("Key — WS28 p.2–3 (mock" in s for s in sums), "Austin: the 68-char 'Key — WS28 p.2–3 …' heading is a folded key %s" % sums)
    check(any("Key — Examiner’s Traps" in s for s in sums), "Austin: the long 'Key — Examiner’s Traps (…)' heading is a folded key")
    check(t.evaluate("[...document.querySelectorAll('details.pl-key')].every(d => !d.open)"), "…all keys start folded")
    check(not visible(t, "1 C · 2 A") and not visible(t, "5 were playing") and not visible(t, "11 did · 12"), "nothing after the long keys leaks (answers hidden)")
    check(visible(t, "both pages done") and visible(t, "twelve items said"), "the Done when lines after them stay open")
    long = t.locator("details.pl-key > summary:has-text('Examiner')")
    lt = long.inner_text(); full = long.get_attribute("title") or ""
    check(len(lt) <= 84 and lt.endswith("…") and full.startswith("Key — Examiner’s Traps") and full.endswith("U4 P.87–89 rules)"), "the label is shortened for display, the full heading is its title (%d chars)" % len(lt))
    # HW Key fallback: no key in the plan → the previous lesson's homework file
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 1, "Austin: no homework key in the plan, but LP27 has the HW27 file → HW Key shows")
    check(t.locator("details.pl-key[id^=pl-hw]").count() == 0, "…(the plan itself still has no homework key)")
    t.click(".pl-top [data-a=pl-hw]"); t.wait_for_selector("#plHwMenu")
    links = t.evaluate("[...document.querySelectorAll('#plHwMenu a')].map(a => [a.textContent, a.getAttribute('href'), a.target, a.rel])")
    check(links == [["🔑 Open Austin_HW27_20261116 (key at the end)", "https://drive.google.com/file/d/%s/view" % HW27, "_blank", "noopener noreferrer"]],
          "…a menu with one link: LP27's HW27 (not LP26's, not the undated or later pack's, not another student's) %s" % links)
    check(t.locator("#plHwMenu button[data-a=pl-hw]").count() == 0, "…and no jump-to-key buttons")
    t.click("#plHwMenu [data-a=pl-hw-x]:not(a)"); t.wait_for_timeout(200)
    check(t.locator("#plHwMenu").count() == 0, "Close shuts the menu")
    check(t.locator("details.pl-key").count() == bold_keys(AUSTIN), "sweep: every bold 'Key…' line is a folded key (%d of %d)" % (t.locator("details.pl-key").count(), bold_keys(AUSTIN)))
    check(t.locator(".pl-rs").count() == 0, "no run sheet on this lesson → headings stay plain")
    # chips: both games, a colon after Lesson Games too
    chips = t.locator(".pl-doc .pl-game").all_inner_texts()
    check(chips.count("🎲 S9 Spelling Test") == 3 and chips.count("🎲 Dog Days Quiz") == 2, "Austin: 'S9 Spelling Test' (also after 'Lesson Games:') and 'Dog Days Quiz' are chips %s" % chips)
    # BEFORE CLASS: "Lesson Games pack austin-lp28: “…” · “…” (after the paper) · “…” · “…” · image search ready: “Icehotel …”"
    bc = "[...document.querySelectorAll('.pl-doc p')].find(p => p.textContent.includes('Icehotel'))"
    bchips = t.evaluate("[...(%s).querySelectorAll('.pl-game')].map(b => b.dataset.g + ' ' + b.textContent)" % bc)
    check(bchips == ["g1 🎲 Dog Days Quiz", "g2 🎲 S9 Spelling Test", "g3 🎲 Examiner's Traps", "g4 🎲 U3–U4 Taboo"], "BEFORE CLASS: all four of Austin's titles are chips (pack id, · and a bracketed note between them) %s" % bchips)
    btxt = t.evaluate("(%s).textContent" % bc)
    check("(after the paper)" in btxt and "image search ready: “Icehotel …”" in btxt and "austin-lp28:" in btxt, "…the note, the pack id and the image search stay plain text: %s" % btxt)

    # ===== 2. Justin: HW Key → the key under 2B · HW27 fixes =====
    t.click("[data-a=home]"); open_plan(t, "Jo · LP28")
    check(t.locator("details.pl-key").count() == bold_keys(JUSTIN), "sweep (Justin): every bold 'Key' line is folded (%d)" % bold_keys(JUSTIN))
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 1, "Justin: the HW Key button shows")
    t.evaluate("window.scrollTo(0, 0)"); t.wait_for_timeout(300)
    t.click(".pl-top [data-a=pl-hw]"); t.wait_for_timeout(500)
    hk = "document.querySelector('details.pl-key[id^=pl-hw]')"
    check(t.evaluate(hk + ".open && " + hk + ".textContent.includes('Our class has a test')"), "HW Key unfolds the key under 2B (items 4, 8, 9)")
    check(t.evaluate("document.querySelectorAll('details.pl-key[id^=pl-hw]').length") == 1, "…only that key counts as homework (not the 0B / 1C / 2A keys)")
    y = top_of(t, "details.pl-key[id^=pl-hw]"); check(y is not None and 40 <= y <= 120, "…and scrolls it to the top (%s)" % y)
    # Lucas: unchanged, main rule
    t.click("[data-a=home]"); open_plan(t, "Leo · LP313")
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 1 and t.evaluate("document.querySelectorAll('details.pl-key[id^=pl-hw]').length") == 1 and "HW312" in t.inner_text("details.pl-key[id^=pl-hw] > summary"), "Lucas: HW Key → 'Key — HW312' as before")
    t.evaluate("window.scrollTo(0, 0)"); t.click(".pl-top [data-a=pl-hw]"); t.wait_for_timeout(400)
    check(t.locator("#plHwMenu").count() == 0 and t.evaluate("document.querySelector('details.pl-key[id^=pl-hw]').open"), "Lucas: the plan's own key wins over LP312's HW file (no menu, no link; the key opens)")
    check(t.locator("a[href*='1LucasHW312file']").count() == 0, "…no link to the previous homework file anywhere")
    # Kai: no key in the plan, and the previous lesson (LP4) has no HW file → no button (LP3's HW3 isn't the previous lesson)
    t.click("[data-a=home]"); open_plan(t, "Kai · LP5")
    check(t.locator(".pl-top [data-a=pl-hw]").count() == 0 and t.locator("a[href*='1KaiHW3file']").count() == 0, "Kai: previous lesson has no HW file → no HW Key button")
    t.click("[data-a=home]"); open_plan(t, "Leo · LP313")
    check(t.locator("details.pl-key").count() == bold_keys(LUCAS), "sweep (Lucas): every bold 'Key' line is folded")
    check(not visible(t, "I have went") and not visible(t, "1 has been"), "Lucas: HW312 answers start hidden")

    # ===== 3a. game chips =====
    chips = t.locator(".pl-doc .pl-game")
    texts = chips.all_inner_texts()
    check(texts[:2] == ["🎲 LP313 Taboo", "🎲 LP313 Spelling"] and len(texts) == 4, "Lucas: both titles after one 'Lesson Games' are chips, matched case-insensitively (pack's title shown) %s" % texts)
    check("“Old Game From LP200”" in t.inner_text(".pl-doc") and t.locator(".pl-game:has-text('Old Game')").count() == 0, "an unmatched title stays plain text")
    check(t.evaluate("[...document.querySelectorAll('.pl-game')].every(b => ['g1','g2'].includes(b.dataset.g) && b.dataset.a === 'pl-play')"), "chips carry the pack's own game ids")
    check(t.evaluate("getComputedStyle(document.querySelector('.pl-game')).fontSize") in ("17px",), "chip text readable")
    t.locator(".pl-game:has-text('LP313 Taboo')").first.click(); t.wait_for_function("__T.UI.view === 'play'", timeout=4000)
    check(t.evaluate("__T.UI.run && __T.UI.run.gameId") == "g1" and t.evaluate("__T.UI.run.packId") == "leo-lp313", "tapping 🎲 LP313 Taboo opens that game")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "plan", "leaving the game goes back to the plan")
    t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2"); t.click("[data-a=play][data-g=g2]"); t.wait_for_function("__T.UI.view === 'play'")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "pack", "a game started from the games page still goes back to the games page")

    # ===== 3b. 📋 → run sheet =====
    t.click("[data-a=home]"); open_plan(t, "Jo · LP28")
    n = t.locator(".pl-doc .pl-rs").count()
    check(n == t.locator(".pl-doc [id^=pl-step-], .pl-doc [id^=pl-seg-]").count() and n == 12, "every step and segment heading is a run sheet link (%d)" % n)
    check(t.locator(".pl-doc h2.pl-rs:has-text('BEFORE CLASS'), .pl-doc h2.pl-rs:has-text('PLANNING'), .pl-doc h2.pl-rs:has-text('AT A GLANCE')").count() == 0, "other headings don't")
    check(t.evaluate("[...document.querySelectorAll('.pl-doc .pl-rs')].every(h => /^H[23]$/.test(h.tagName) && h.getAttribute('role') === 'link' && h.tabIndex === 0 && h.title === 'Open the run sheet here' && h.dataset.a === 'pl-rs' && (h.dataset.c || h.dataset.s))"),
          "the step / segment headings themselves are the links (role=link, tabindex 0, title, data-c / data-s)")
    check(t.locator(".pl-doc button.pl-rs").count() == 0 and "📋" not in t.inner_text(".pl-doc"), "no 📋 buttons in the plan any more")
    look = t.evaluate("""(() => { const a = getComputedStyle(document.getElementById('pl-step-2B')), b = getComputedStyle(document.querySelector('.pl-doc h2:not(.pl-rs)')), s = getComputedStyle(document.getElementById('pl-seg-2'));
      return [a.color === b.color, a.fontWeight === b.fontWeight, a.textDecorationLine, a.textDecorationStyle, s.color === b.color]; })()""")
    check(look == [True, True, "underline", "dotted", True], "…normal colour and weight, a dotted underline only %s" % look)
    hh = t.evaluate("Math.round(document.getElementById('pl-step-2B').getBoundingClientRect().height)")
    check(hh <= 50, "the 2B heading still one line on the iPad (%s)" % hh)
    # a text selection or a drag on the heading doesn't open the run sheet
    t.evaluate("document.getElementById('pl-step-1A').scrollIntoView({ block:'center' })"); t.wait_for_timeout(300)
    r = t.evaluate("(() => { const r = document.getElementById('pl-step-1A').getBoundingClientRect(); return [r.left, r.top, r.height]; })()")
    t.mouse.move(r[0] + 6, r[1] + r[2] / 2); t.mouse.down(); t.mouse.move(r[0] + 120, r[1] + r[2] / 2, steps=8); t.mouse.up(); t.wait_for_timeout(300)
    check(t.evaluate("__T.UI.view") == "plan", "dragging across a heading (selecting its text) doesn't open the run sheet")
    t.evaluate("getSelection().removeAllRanges()")
    t.mouse.move(r[0] + 6, r[1] + r[2] / 2); t.mouse.down(); t.wait_for_timeout(800); t.mouse.up(); t.wait_for_timeout(300)
    check(t.evaluate("__T.UI.view") == "plan", "a long press doesn't either")
    t.evaluate("window.scrollTo(0, 0)"); t.wait_for_timeout(200)
    t.evaluate("document.getElementById('pl-step-2B').scrollIntoView()"); t.wait_for_timeout(600); py = t.evaluate("scrollY")
    t.click("#pl-step-2B"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(300)
    check(t.evaluate("__T.UI.view") == "sheet", "tapping the 2B heading opens the run sheet")
    y = top_of(t, ".rs [data-sc='2B']"); txt = t.evaluate("document.querySelector('.rs [data-sc=\"2B\"]').textContent")
    check(y is not None and 40 <= y <= 120 and "2B HW27 fixes" in txt, "…at the 2B line (top %s, %s)" % (y, txt[:30]))
    check(t.locator(".rs [data-sc='2B'].pl-hit").count() == 1, "…with the brief highlight")
    t.wait_for_timeout(1800); check(t.locator(".rs .pl-hit").count() == 0, "the highlight goes")
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(250)
    check(abs(t.evaluate("scrollY") - py) <= 2, "📖 goes back to the plan where it was (%s vs %s)" % (t.evaluate("scrollY"), py))
    t.click("#pl-step-1C"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(300)
    y = top_of(t, ".rs .rs-blk[data-seg='1']"); check(y is not None and 40 <= y <= 120, "a step with no run sheet line (1C) lands on its block (top %s)" % y)
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(250)
    t.focus("#pl-seg-3"); t.keyboard.press("Enter"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(300)
    y = top_of(t, ".rs .rs-blk[data-seg='3']"); check(y is not None and 40 <= y <= 120, "Enter on the focused SEGMENT 3 heading lands on block 3 (top %s)" % y)
    t.evaluate("window.scrollTo(0, 300)"); t.wait_for_timeout(600)
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(250)
    t.click("#pl-seg-4"); t.wait_for_selector(".rs-blk"); t.wait_for_timeout(300)
    check("isn’t on the run sheet" in t.inner_text("body") and abs(t.evaluate("scrollY") - 300) <= 2, "no block for SEGMENT 4: a toast, the run sheet where it was (%s)" % t.evaluate("scrollY"))
    t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc"); t.wait_for_timeout(250)
    # the plan's chip for an app game opens the same game as the run sheet's Play button
    t.locator(".pl-game:has-text('Verb Bingo')").last.click(); t.wait_for_function("__T.UI.view === 'play'")
    check(t.evaluate("__T.UI.run.gameId") == "g2", "🎲 Verb Bingo opens Verb Bingo")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "plan", "…and back to the plan")
    t.click("[data-a=rs-open]"); t.wait_for_selector(".rs-blk"); t.click("[data-a=rs-play][data-g=g2]"); t.wait_for_function("__T.UI.view === 'play'")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "sheet", "the run sheet's Play still goes back to the run sheet")

    # ===== 3c. nothing reaches students: class link + live, student link =====
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); clink = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    t.click("[data-a=nav-games]"); t.wait_for_selector(".head h2")
    t.click("[data-a=slink][data-g=g1]"); t.wait_for_function("document.getElementById('slinkUrl') && document.getElementById('slinkUrl').value.length > 20")
    slink = t.input_value("#slinkUrl"); t.click("[data-a=slink-close]")
    REC = "window.__BC=[]; (function(){ const O = window.BroadcastChannel; window.BroadcastChannel = function(n){ const c = new O(n); c.addEventListener('message', e => window.__BC.push(JSON.stringify(e.data))); return c; }; })();"
    secrets = ["1PlanJustinLP28_ForTestsOnlyCCCC", "Our class has a test", "pl-game", "pl-rs", "pl-play", "sheetAt", "plRet", "HW27 fixes"]
    for name, url in (("class link", clink), ("student link", slink)):
        s = ctx.new_page(); e2 = []; s.on("pageerror", lambda e: e2.append(str(e))); s.add_init_script(REC)
        def sh(r):
            u = r.request.url
            if u.endswith("supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
            if "/lesson-games/" in u: return r.fulfill(body=APP2, content_type="text/html")
            return r.abort()
        s.route("**/*", sh); s.goto(url); s.wait_for_timeout(900)
        if name == "class link":   # the teacher opens a game from the plan's chip while the class screen is open
            t.click("header.nav [data-a=pl-open]"); t.wait_for_selector(".pl-doc")
            t.locator(".pl-game:has-text('Set 6 test')").first.click(); t.wait_for_function("__T.UI.view === 'play'")
            s.wait_for_function("() => __T.UI.run && __T.UI.run.gameId === 'g1'", timeout=6000); t.wait_for_timeout(400)
            check(True, "class link: a game opened from the plan's chip goes on the class screen")
        elif s.locator("[data-a=s-start]").count(): s.click("[data-a=s-start]"); s.wait_for_timeout(500)
        # (localStorage is left out: in this one test browser it is the teacher's too)
        d = json.loads(s.evaluate("JSON.stringify({ smode: __T.SMODE, packs: __T.PACKS, ui: __T.UI, bc: window.__BC })"))
        held = json.dumps(d) + s.inner_text("body")
        check(not [x for x in secrets if x in held], "%s: nothing from the plan or its links in what the student page holds or receives %s" % (name, [x for x in secrets if x in held]))
        check(s.locator(".pl-game, .pl-rs, .pl-doc, [data-sc]").count() == 0, "%s: no plan chips, heading links or run sheet lines on the student page" % name)
        check(not e2, "%s: no page errors %s" % (name, e2[:2]))
        s.close()
    check(t.evaluate("JSON.stringify(__T.UI.run || {})").find("pl-") == -1 and t.evaluate("JSON.stringify(__T.UI.run || {})").find("1PlanJustin") == -1, "the teacher's game state carries nothing from the plan")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    check(not errs, "no page errors %s" % errs[:3])
    ctx.close()

    # ===== phone and iPad: headings still read cleanly, nothing wider than the screen =====
    for vw, vh, name in ((1180, 820, "iPad landscape"), (820, 1180, "iPad portrait"), (390, 844, "phone")):
        c = b.new_context(viewport={"width":vw, "height":vh}, device_scale_factor=1); e4 = []; c4 = []
        pg = tpage(c, e4, c4); open_plan(pg, "Jo · LP28")
        wide = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
        h = pg.evaluate("(() => { const h = document.getElementById('pl-step-2A'); return [Math.round(h.getBoundingClientRect().height), parseFloat(getComputedStyle(h).lineHeight)]; })()")
        check(wide <= 1 and h[0] <= h[1] * 2 + 12, "%s: no sideways scroll (%d); '2A · Verb Bingo (…)' fits in two lines at most (%s)" % (name, wide, h))
        pg.click("#pl-step-2B"); pg.wait_for_selector(".rs-blk"); pg.wait_for_timeout(300)
        y = top_of(pg, ".rs [data-sc='2B']"); hb = pg.evaluate("Math.round(document.querySelector('header.nav').getBoundingClientRect().bottom)")
        check(y is not None and hb <= y <= hb + 60, "%s: tapping 2B lands just under the header (top %s, header %s)" % (name, y, hb))
        if name == "phone":
            pg.click("header.nav [data-a=pl-open]"); pg.wait_for_selector(".pl-doc"); pg.wait_for_timeout(200)
            pg.evaluate("document.getElementById('pl-seg-2').scrollIntoView()"); pg.wait_for_timeout(200)
            pg.screenshot(path=os.path.join(HERE, "plan_links_phone.png"))
        check(not e4, "%s: no page errors %s" % (name, e4[:2]))
        c.close()
done()
