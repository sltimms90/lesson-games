"""19 Nov feedback: Look selects don't overlap on the PC; run sheet paste box lives under Advanced; Quick game shows its word source;
spelling box: no size jumps per word with the keyboard open, hands off when pinch-zoomed, never under 16px on screen."""
from lg import *
import lg
lg.APP = lg.APP.replace(HOOK, HOOK + "window.__F={fitStage:fitStage};")
bank = "\n".join("%s | clue for %s" % (w, w) for w in "castle bridge garden market tower river".split())
old = {"id":"mia-lp8","student":"Mia","lp":8,"title":"Mia · LP8","date":"2026-11-10","updatedAt":"x","games":[],"bank":"forest | lots of trees\nisland | water all round\nvillage | small town"}
pk = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-17","updatedAt":"x","bank":bank,
      "games":[{"id":"g1","type":"spelling","title":"Spell","block":"castle\nbridge\ngarden\nmarket\ntower\nriver","options":{}}],
      "runsheet":{"start":"16:00","length":30,"format":"online","blocks":[{"mins":30,"label":"1 Spelling","lines":[{"game":"g1","type":"app","label":"Spell"}]}]}}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1920, "height":1000}); errs = []
    t = teacher(ctx, seed_db([old, pk]), errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    if t.evaluate("__T.UI.view") == "sheet": t.click("[data-a=rs-games]"); t.wait_for_timeout(300)
    check(t.locator(".rs-card #rsSpecIn").count() == 0, "run sheet card has no paste box")
    t.click("#advSec > summary"); t.click("#lookSec > summary"); t.wait_for_timeout(100)
    r1, r2 = [t.evaluate("(() => { const r = document.getElementById('%s').getBoundingClientRect(); return [r.left, r.right]; })()" % i) for i in ("lkStu", "lkPack")]
    check(r1[1] <= r2[0], "Look selects side by side without overlapping %s %s" % (r1, r2))
    check(t.locator("#rsPasteSec").count() == 1 and "Replace the run sheet" in t.inner_text("#rsPasteSec summary"), "Replace the run sheet is under Advanced")
    t.click("#rsPasteSec > summary"); t.wait_for_timeout(100)
    ta, sec = [t.evaluate("document.querySelector('%s').getBoundingClientRect().right" % s) for s in ("#rsSpecIn", "#rsPasteSec")]
    check(ta <= sec + 1, "its box stays inside (%d <= %d)" % (ta, sec))
    q = t.inner_text("#quickSec")
    check("Words from:" in q and "Today · 6 words: castle" in q, "Quick game says where its words come from: %s" % q[:160])
    t.click("[data-a=qscope][data-v=recent]"); t.wait_for_timeout(200); q = t.inner_text("#quickSec")
    check("This lesson and the one before · 9 words" in q and "forest" in q, "Last 2 lessons lists the words it adds: %s" % q[:200])
    ctx.close()
    # phone: a keyboard shrinking the window doesn't shrink the spelling game, and the box is never under 16px on screen
    ctx = b.new_context(viewport={"width":390, "height":560}, has_touch=True); errs2 = []
    t = teacher(ctx, seed_db([old, pk]), errs2); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    t.locator("[data-a=rs-play][data-g=g1]").first.click(); t.wait_for_selector("#spIn")
    z0 = t.evaluate("document.querySelector('main.stage').style.zoom || '1'")
    fs = t.evaluate("parseFloat(getComputedStyle(document.getElementById('spIn')).fontSize) * (parseFloat(document.querySelector('main.stage').style.zoom) || 1)")
    check(fs >= 16, "spelling box text is at least 16px on screen (%.1f)" % fs)
    zs = []
    for w in ["castle", "bridge", "gardn"]:
        t.set_viewport_size({"width":390, "height":300}); t.evaluate("__F.fitStage()")   # keyboard open
        t.fill("#spIn", w); t.press("#spIn", "Enter"); t.wait_for_timeout(300)
        t.evaluate("__F.fitStage()"); zs.append(t.evaluate("document.querySelector('main.stage').style.zoom || '1'"))
    check(len(set(zs)) == 1 and zs[0] == z0, "size stays the same word to word with the keyboard open: %s (start %s)" % (zs, z0))
    check(not errs and not errs2, "no errors %s %s" % (errs, errs2))
    b.close()
done()
