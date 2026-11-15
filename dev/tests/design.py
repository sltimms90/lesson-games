"""Design changes from the review: lesson page layout (Quick game on top, folded sections), Hard mode name, Undo toast."""
from lg import *
G = lambda i, ty, title, opts=None, block="castle | a king lives here\nbridge | you cross a river on it\ngarden | flowers grow here": {"id":"g%d" % i, "type":ty, "title":title, "block":block, "opts":opts or {}}
P15 = [("kitchen","the room where you cook dinner every evening"),("bedroom","the room where you sleep at night"),("bathroom","you have a shower or a bath here"),("garden","flowers and vegetables grow here"),("garage","you keep the car in here"),("library","you borrow books from this place"),("museum","you look at old and famous things here"),("station","you wait here for a train"),("airport","planes take off and land here"),("market","you buy fresh fruit and fish here"),("castle","a king and queen used to live here"),("bridge","you cross a river on it"),("island","land with water all around it"),("forest","a big place with lots of trees"),("village","a very small town in the country")]
CW = list(zip(["being in charge of something","how hot or cold it is","the area around your home","someone who takes pictures","very, very unusual","the air, water and land around us","it could hurt you","nice and soft to sit on","children play here at school","a sport with a tall net","a small red fruit","it flies with blades on top"], ["responsibility","temperature","neighbourhood","photographer","extraordinary","environment","dangerous","comfortable","playground","basketball","strawberry","helicopter"]))
BW = "\n".join("castle bridge garden market tower river forest island village museum library station kitchen bedroom bathroom garage".split())
bank = "castle | a king lives here\nbridge | you cross a river on it\ngarden | flowers grow here\nmarket | you buy food here"
packs = [{"id":"mia-lp8", "student":"Mia", "lp":8, "title":"Mia · LP8", "date":"2026-11-10", "updatedAt":"x", "games":[], "bank":"castle | a king lives here"},
         {"id":"mia-lp9", "student":"Mia", "lp":9, "title":"Mia · LP9", "date":"2026-11-17", "updatedAt":"x", "bank":bank,
          "games":[G(1, "hangman", "Castle words"), G(2, "cards", "Cards", block="a king lives here = castle\nyou cross a river on it = bridge\nflowers grow here = garden"), G(3, "anagrams", "Mix-up"), G(4, "bingo", "Bingo", {"size":4, "show":"student", "tk":0}, block=BW), G(5, "match", "Places", {"mode":"match", "perPage":12}, block="\n".join("%s = %s" % x for x in P15)), G(6, "cross", "Big words", block="\n".join("%s = %s" % x for x in CW))]}]
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
    # --- A. Bingo cards fill the landscape screen
    for show in ("student", "all"):
        t.click("[data-a=play][data-g=g4]"); t.wait_for_selector(".grid .cell", timeout=5000)
        if show == "all": t.click("[data-a=settings]"); t.click("[data-a=bg-show][data-v=all]"); t.wait_for_timeout(200); t.evaluate("__T.UI.settingsOpen && document.querySelector('[data-a=settings]').click()"); t.wait_for_timeout(300)
        t.click("[data-a=bg-next]"); t.wait_for_timeout(1500)
        hs = t.evaluate("[...document.querySelectorAll('.cards .card')].map(c => Math.round(c.getBoundingClientRect().height))")
        sc = t.evaluate("[document.documentElement.scrollHeight, innerHeight, document.querySelector('main.stage').style.zoom || '1']")
        cell = t.evaluate("(() => { const c = document.querySelector('.grid .cell').getBoundingClientRect(); return [Math.round(c.width), Math.round(c.height), parseFloat(getComputedStyle(document.querySelector('.grid .cell')).fontSize)] })()")
        check(all(h > 620 for h in hs) and sc[0] <= sc[1] + 1 and sc[2] == "1", "bingo (%s) cards fill the iPad height: %s, page %s, cell %s" % (show, hs, sc, cell))
        t.screenshot(path=HERE + "/shots/bingo_%s.png" % show)
        t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    # --- B. Match Up pages and Crossword stay full size
    t.click("[data-a=play][data-g=g5]"); t.wait_for_timeout(900)
    pg = t.evaluate("__T.UI.run.st.pages.map(p => p.rows.length)")
    check(pg == [5, 5, 5] and t.evaluate("document.querySelector('main.stage').style.zoom || '1'") == "1", "15 long pairs at 12 a page → %s, full size" % pg)
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    t.click("[data-a=play][data-g=g6]"); t.wait_for_timeout(900)
    check(t.evaluate("document.querySelector('main.stage').style.zoom || '1'") == "1" and t.evaluate("document.documentElement.scrollHeight") <= 821, "12-word crossword fits the iPad at full size")
    t.screenshot(path=HERE + "/shots/cross_ipad.png")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    # --- 2. Hard mode (was "Challenge", now kept for the ⚡ speaking prompt only)
    hb = t.locator(".game [data-a=play-ch]")
    check(hb.count() == 2 and all(x == "Hard mode" for x in hb.all_inner_texts()), "Hangman and Anagrams offer Hard mode: %s" % hb.all_inner_texts())
    check("Challenge" not in t.inner_text("#app"), "no 'Challenge' left on the lesson page")
    hb.first.click(); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.run.title").endswith("(hard mode)") and "Hard mode · Word 1" in t.inner_text("#app"), "Hard mode run: %s" % t.evaluate("__T.UI.run.title"))
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(200)
    # --- 3. Undo toast after a judging tap
    t.click("[data-a=play][data-g=g2]"); t.wait_for_selector("[data-a=fc-flip]", timeout=5000)
    t.click("[data-a=fc-flip]"); t.wait_for_timeout(200); t.click("[data-a=fc-ok]"); t.wait_for_timeout(150)
    ut = t.locator(".toast.undo")
    check(ut.count() == 1 and "Got it" in ut.inner_text() and ut.locator("[data-a=undo-toast]").inner_text().strip() == "↶", "Got it shows the Undo toast with an icon button: %s" % (ut.inner_text() if ut.count() else ""))
    t.screenshot(path=HERE + "/shots/undo_toast.png")
    t.click("[data-a=undo-toast]"); t.wait_for_timeout(200)
    check(t.evaluate("__T.UI.run.st.log.length") == 0 and t.locator(".toast.undo").count() == 0, "↶ takes the mark back and closes the toast")
    check(t.locator("[data-a=fc-ok]").count() == 1, "the card is back, ready to mark again")
    t.click("[data-a=fc-no]"); t.wait_for_timeout(3300)
    check(t.locator(".toast.undo").count() == 0 and t.evaluate("__T.UI.run.st.log.length") == 1, "the toast goes after 3 seconds; the mark stays")
    t.click("[data-a=fc-flip]"); t.wait_for_timeout(150); t.click("[data-a=fc-ok]"); t.wait_for_timeout(100)
    t.click("[data-a=fc-flip]"); t.wait_for_timeout(150)
    check(t.locator(".toast.undo").count() == 0, "any other tap closes the toast (its undo would take back more than the mark)")
    t.click("[data-a=fc-no]"); t.wait_for_timeout(100); t.click("[data-a=finish-ask]"); t.wait_for_timeout(100)
    check(t.locator(".toast.undo").count() == 0, "leaving for the Finish dialog closes it")
    t.click("[data-a=discard]"); t.wait_for_timeout(200)
    t.click("[data-a=play][data-g=g1]"); t.wait_for_selector(".keys", timeout=5000); t.click("[data-a=hm-key][data-c=a]"); t.wait_for_timeout(150)
    check(t.locator(".toast.undo").count() == 0, "an ordinary move (a Hangman letter) gets no toast")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(200)
    np = [{"id":"new-lp1", "student":"Ned", "lp":1, "title":"Ned · LP1", "date":"2026-11-17", "updatedAt":"x", "games":[]}]
    ctx2 = b.new_context(viewport={"width":1180, "height":820}); t2 = teacher(ctx2, seed_db(np), errs); t2.wait_for_selector("text=Ned · LP1", timeout=8000); t2.click("text=Ned · LP1"); t2.wait_for_timeout(300)
    check(t2.evaluate("document.getElementById('addSec').open"), "a lesson with no games opens Add a game")
    ctx2.close()
    # --- 3b. Undo toast in a live game: the student's screen follows the undo
    lp = dict(packs[1]); lp["liveRoom"] = "0123456789abcdef0123456789abcdef"
    ctx3 = b.new_context(viewport={"width":1180, "height":820})
    t3 = teacher(ctx3, seed_db([lp]), errs); t3.wait_for_selector("text=Mia · LP9", timeout=8000); t3.click("text=Mia · LP9"); t3.wait_for_timeout(300)
    t3.click("#clsBar [data-a=clink]"); t3.wait_for_selector("#slinkUrl", timeout=5000); url = t3.input_value("#slinkUrl"); t3.click("[data-a=clink-close]")
    s3 = student(ctx3, url, errs); s3.wait_for_timeout(1000)
    t3.click("[data-a=play][data-g=g2]"); s3.wait_for_selector("[data-a=fc-flip]", timeout=5000)
    s3.click("[data-a=fc-flip]"); t3.wait_for_timeout(500); t3.click("[data-a=fc-ok]"); s3.wait_for_timeout(500)
    check(s3.evaluate("__T.UI.run.st.log.length") == 1 and s3.locator(".toast.undo").count() == 0, "live: the mark reaches the student, who gets no toast")
    t3.click("[data-a=undo-toast]"); s3.wait_for_timeout(700)
    check(s3.evaluate("__T.UI.run.st.log.length") == 0 and t3.evaluate("__T.UI.run.st.log.length") == 0, "live: ↶ takes the mark back on the student's screen too")
    ctx3.close()
    check(not errs, "no page errors %s" % errs[:3])
done()
