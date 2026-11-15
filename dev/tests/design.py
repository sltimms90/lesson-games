"""Design changes from the review: lesson page layout (Quick game on top, folded sections), Hard mode name, Undo toast."""
from lg import *
G = lambda i, ty, title, opts=None, block="castle | a king lives here\nbridge | you cross a river on it\ngarden | flowers grow here": {"id":"g%d" % i, "type":ty, "title":title, "block":block, "opts":opts or {}}
bank = "castle | a king lives here\nbridge | you cross a river on it\ngarden | flowers grow here\nmarket | you buy food here"
packs = [{"id":"mia-lp8", "student":"Mia", "lp":8, "title":"Mia · LP8", "date":"2026-11-10", "updatedAt":"x", "games":[], "bank":"castle | a king lives here"},
         {"id":"mia-lp9", "student":"Mia", "lp":9, "title":"Mia · LP9", "date":"2026-11-17", "updatedAt":"x", "bank":bank,
          "games":[G(1, "hangman", "Castle words"), G(2, "cards", "Cards", block="a king lives here = castle\nyou cross a river on it = bridge\nflowers grow here = garden"), G(3, "anagrams", "Mix-up")]}]
results = [{"id":"r1", "packId":"mia-lp8", "gameId":"g1", "type":"hangman", "title":"h", "at":"2026-11-10T03:00:00Z", "summary":"h", "items":[{"item":"castle", "ok":False}]}]
def top(pg, sel): return pg.evaluate("s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top + scrollY) : -1 }", sel)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, seed_db(packs, results=results), errs); t.wait_for_selector("text=Mia · LP9", timeout=8000)
    t.click("text=Mia · LP9"); t.wait_for_timeout(300)
    # --- 1. lesson page layout
    q, rs, g1 = top(t, "#quickSec"), top(t, ".rs-card"), top(t, ".game")
    check(0 < q < rs < g1, "Quick game comes before the run sheet and the games (%d < %d < %d)" % (q, rs, g1))
    check(q < 400, "Quick game starts in the top half of the iPad screen (%d)" % q)
    check(t.locator("#quickSec [data-a=qscope][data-v=missed]").is_visible(), "Missed lately button is visible at the top")
    check(not t.evaluate("document.getElementById('addSec').open") and not t.evaluate("document.getElementById('lookSec').open"), "Add a game and Look start folded")
    check(t.locator("[data-a=addgame]").first.is_hidden() and t.locator("#lkPack").is_hidden(), "their controls are hidden until opened")
    check(t.locator("details.help[open]").count() == 0 and t.locator("details.help").count() >= 2, "help text is folded behind ⓘ (%d tips)" % t.locator("details.help").count())
    check("Bright" in t.inner_text("#lookSec summary"), "Look summary names the current look: %s" % t.inner_text("#lookSec summary"))
    h = t.evaluate("document.documentElement.scrollHeight"); print("lesson page height %d px = %.1f iPad screens" % (h, h / 820.0))
    t.screenshot(path=HERE + "/shots/lesson_ipad.png"); t.screenshot(path=HERE + "/shots/lesson_ipad_full.png", full_page=True)
    t.click("#addSec > summary"); t.click("#lookSec > summary"); t.wait_for_timeout(100)
    t.select_option("#lkPack", "bats"); t.wait_for_timeout(300)
    check(t.evaluate("document.getElementById('addSec').open && document.getElementById('lookSec').open"), "opened sections stay open after a re-render")
    check("Midnight bats (this lesson only)" in t.inner_text("#lookSec summary"), "summary shows a one-off look")
    t.click("#lookSec > summary"); t.click("[data-a=qscope][data-v=today]"); t.wait_for_timeout(200)
    check(not t.evaluate("document.getElementById('lookSec').open") and t.evaluate("document.getElementById('addSec').open"), "a folded section stays folded after a re-render")
    np = [{"id":"new-lp1", "student":"Ned", "lp":1, "title":"Ned · LP1", "date":"2026-11-17", "updatedAt":"x", "games":[]}]
    ctx2 = b.new_context(viewport={"width":1180, "height":820}); t2 = teacher(ctx2, seed_db(np), errs); t2.wait_for_selector("text=Ned · LP1", timeout=8000); t2.click("text=Ned · LP1"); t2.wait_for_timeout(300)
    check(t2.evaluate("document.getElementById('addSec').open"), "a lesson with no games opens Add a game")
    ctx2.close()
    check(not errs, "no page errors %s" % errs[:3])
done()
