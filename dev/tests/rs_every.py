"""19 Nov 2026: the run sheet opens for every lesson (in person too), and is comfortable on a phone and the landscape iPad.
Home lists today's lessons (‹ › by day), Students is a folded list; the lesson page order; edited games on top."""
import datetime
from lg import *
import lg
exec(open("bf.py").read().split("def lesson(pg):")[0].split("from lg import *")[1])
TODAY = datetime.date.today().isoformat()
p_in = dict(pack, id="jl", date=TODAY)                              # format "in person"
p_in["runsheet"] = dict(pack["runsheet"], blocks=pack["runsheet"]["blocks"] + [{"mins":5,"label":"4 Wrap","lines":[{"type":"score","n":10,"label":"4A spelling score"},{"type":"cue","text":"note mistakes","label":"4B Mistakes"}]}])
p_none = {"id":"tim","student":"Tim","lp":192,"title":"Tim · LP192","date":TODAY,"updatedAt":"x","games":[{"id":"g1","type":"hangman","title":"H","block":"castle | a king lives here\nbridge | over a river\ngarden | flowers grow"}]}
stu = [{"id":"cathy-lily","name":"Cathy & Lily","runsheet":"online","updatedAt":"x"}]   # old setting: no longer matters
VIEWS = [("phone", 390, 844), ("phone-land", 844, 390), ("ipad-land", 1180, 820), ("ipad", 820, 1180), ("desktop", 1440, 900)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for name, w, h in VIEWS:
        print("==", name)
        ctx = b.new_context(viewport={"width":w, "height":h}, has_touch=name != "desktop"); errs = []
        db = seed_db([p_in, p_none], students=stu)
        t = teacher(ctx, db, errs); t.wait_for_selector(".daybar ~ .list >> text=JL", timeout=8000)
        check(t.locator(".daybar ~ .list .item").count() == 2, "today's two lessons on the home page")
        t.click(".daybar ~ .list >> text=JL"); t.wait_for_timeout(300)
        check(t.evaluate("__T.UI.view") == "sheet", "an in-person lesson opens on its run sheet (student was set to online-only before)")
        check(t.evaluate("!__MOCK.db.sheets.jl"), "opening it writes nothing: an unmarked lesson stays null for Phase B")
        ov = t.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        check(ov[0] <= ov[1], "no sideways scrolling on the run sheet %s" % ov)
        off = t.evaluate("""[...document.querySelectorAll('main.rs *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className + ' ' + (e.textContent||'').trim().slice(0,20)).slice(0,4)""")
        check(not off, "nothing on the run sheet sticks out sideways %s" % off)
        small = t.evaluate("""[...document.querySelectorAll('main.rs button, main.rs input:not([type=hidden]), .rs-top button')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.height < 40 || r.width < 40); }).map(e => (e.className||e.tagName) + ' ' + (e.textContent||'').trim().slice(0,12) + ' ' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height)).slice(0,6)""")
        check(not small, "every tick box and button is at least 40×40 %s" % small)
        tk = t.evaluate("(() => { const r = document.querySelector('.rs-tk').getBoundingClientRect(); return [r.width, r.height]; })()")
        check(tk[0] >= 44 and tk[1] >= 44, "tick boxes are 44×44 or more %s" % tk)
        # the last box on the page can sit in the top half, above a keyboard
        t.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); t.wait_for_timeout(100)
        top = t.evaluate("document.querySelector('[data-rsin=\"end.other\"]').getBoundingClientRect().top")
        check(top < h * 0.5, "the last text box can scroll into the top half of the screen (%d of %d)" % (top, h))
        t.evaluate("scrollTo(0, 0)"); t.wait_for_timeout(100)
        box = t.locator("[data-rsin='end.other']"); box.focus(); t.wait_for_timeout(600)
        r = t.evaluate("(() => { const r = document.querySelector('[data-rsin=\"end.other\"]').getBoundingClientRect(); return [r.top, r.bottom]; })()")
        check(r[0] >= 60 and r[1] <= h, "a focused box is scrolled into view below the header %s" % r)
        box.fill("goed for went"); t.wait_for_timeout(1200)
        check(t.evaluate("__T.UI.view") == "sheet" and t.evaluate("document.activeElement && document.activeElement.dataset.rsin") == "end.other", "typing keeps the box focused (no re-render)")
        # sheet -> game -> sheet: one tap each way
        t.locator("[data-a=rs-play][data-g=g4]").first.click(); t.wait_for_timeout(300)
        check(t.evaluate("__T.UI.view") == "play", "Play on a run sheet row opens the game in one tap")
        t.click("[data-a=lesson]"); t.wait_for_timeout(300)
        check(t.evaluate("__T.UI.view") == "sheet", "‹ in the game comes straight back to the run sheet")
        # ‹ Games -> lesson page -> a game there -> back to the run sheet
        t.click("[data-a=nav-games]"); t.wait_for_timeout(300)
        check(t.locator("header.nav [data-a=rs-open]").count() == 1 and t.locator("header.nav [data-a=rs-open]").is_visible(), "the games page has one 📋 run sheet tab (no extra ‹ Run sheet)")
        check(t.locator("[data-a=rs-mode]").count() == 0 and "Every lesson" not in t.inner_text("#app"), "no per-student run sheet toggle any more")
        t.click("[data-a=play][data-g=g1]"); t.wait_for_timeout(300); t.click("[data-a=lesson]"); t.wait_for_timeout(300)
        check(t.evaluate("__T.UI.view") == "pack", "a game started from the games page comes back to the games page")
        t.click("[data-a=rs-open]"); t.wait_for_timeout(300)
        # marking still writes the same row: sheets keyed by pack id, marks inside
        t.locator(".rs-tk").first.click(); t.wait_for_timeout(1500)
        row = t.evaluate("__MOCK.db.sheets.jl && __MOCK.db.sheets.jl.data")
        check(row and row.get("packId") == "jl" and row.get("marks") and "rows" in row and "summary" in row, "a tick saves sheets/jl with marks, rows and summary")
        # a lesson without a run sheet still opens its lesson page; home -> it -> home
        t.click("[data-a=nav-games]"); t.wait_for_timeout(200); t.click("header.nav [data-a=student]"); t.wait_for_timeout(200); t.click("[data-a=home]"); t.wait_for_timeout(200)
        t.click(".daybar ~ .list >> text=Tim · LP192"); t.wait_for_timeout(300)
        check(t.evaluate("__T.UI.view") == "pack" and t.locator("[data-a=rs-open]").count() == 0, "a lesson with no run sheet opens on its games")
        if name in ("phone", "ipad-land"):
            t.click("header.nav [data-a=student]"); t.wait_for_timeout(200); t.click("[data-a=home]"); t.wait_for_timeout(200); t.click(".daybar ~ .list >> text=JL"); t.wait_for_timeout(300)
            t.screenshot(path=HERE + "/shots/rs_%s.png" % name)
        check(not errs, "no errors %s" % errs)
        ctx.close()
    b.close()
done()
