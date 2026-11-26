"""Screen-fit sweep: every game type with long content at landscape iPad, desktop and phone.
Nothing may scroll or spill off screen. Screenshots go to dev/tests/shots/ (not committed).
Also the class-link bar (#clsBar) on the lesson page and run sheet, from phone to wide desktop:  python3 fit.py clsbar"""
import os, sys
from lg import *
LONG = "internationalisation"
S = "My grandmother always tells me wonderful stories about the old fishing village where she grew up"
blocks = {
 "bingo": "\n".join(["castle", "uncomfortable", "responsibility", "photographer", "extraordinary", "temperature", "environment", "neighbourhood", "comfortable", "dangerous", "vegetables", "playground", "basketball", "strawberry", "helicopter", "thunderstorm", "earthquake", "dinosaur", "butterfly", "television", "restaurant", "supermarket", "underground", "fireworks", LONG]),
 "hangman": LONG + " | the act of making something work in many different countries all around the world\nresponsibility | a job or duty that you must do\ncastle",
 "anagrams": LONG + " | the act of making something work in many different countries all around the world\nresponsibility | a job you must do",
 "cards": S + " = " + S + "\n" + LONG + " = " + LONG + "\nshort = long",
 "typeit": S + " (grow) = she grew up in the old fishing village by the sea\nthe past of go = went",
 "build": S + ".\nWhere did your grandmother grow up when she was a little girl? | make a question",
 "spot": "My grandmother always tell me wonderful stories about the old fishing village where she grow up. = My grandmother always tells me wonderful stories about the old fishing village where she grew up.\nShe don't like apples. = She doesn't like apples.",
 "match": "\n".join(["%s%d = %s" % (LONG, i, S) for i in range(8)]),
 "odd": "responsibility, temperature, *" + LONG + ", neighbourhood, photographer | " + S + "\napple, banana, *carrot, grape | carrot is a vegetable",
 "phon": "a_e: " + ", ".join(["cake", "name", "gate", "lake", "grape", "snake", "plane", "skate"]) + "\nai: " + ", ".join(["rain", "train", "paint", "snail", "waist", "complaint", "explain", "Spain"]) + "\nay: " + ", ".join(["day", "play", "stay", "tray", "yesterday", "birthday", "holiday", "crayon"]) + "\neigh: eight, weigh, neighbour, sleigh",
 "whack": "Hit the words that are spelled correctly in British English, please!\nHIT: " + ", ".join(["responsibility", "neighbourhood", "colourful", "temperature", "extraordinary", "photographer"]) + "\nMISS: " + ", ".join(["responsability", "neighborhod", "colorfull", "temprature", "extrordinary", "fotographer"]),
 "cross": "\n".join(["%s %d = %s" % (S[:50], i, w) for i, w in enumerate(["responsibility", "temperature", "neighbourhood", "photographer", "extraordinary", "environment", "dangerous", "comfortable", "playground", "basketball", "strawberry", "helicopter"])]),
 "snakes": "Maximilian-Alexander\nTeacher",
 "hilo": "Maximilian-Alexander\nTeacher",
 "wheel": "\n".join([S + "?"] * 3 + ["What is the most " + LONG + " thing you know?"] * 9),
 "slot": "SLOT REELS\nWHO: my extraordinary grandmother | the photographer | a dragon\nVERB: " + LONG + " | climb | borrow\nWHERE: at the underground station | in the kitchen",
 "dice": "\n".join(["responsibility", "temperature", "neighbourhood", "photographer", "extraordinary", "environment", LONG]),
 "quiz": "\n\n".join([S + "?\n" + S + "\n*" + S + " again\n" + LONG + "\n" + LONG + " too"] * 4),
 "taboo": "TABOO CARDS\nTARGET: " + LONG + "\nFORBIDDEN: responsibility, temperature, neighbourhood, photographer, extraordinary, environment",
 "auction": "1. " + S + ". [CORRECT]\n2. " + S.replace("tells", "tell") + ". [WRONG — tells]\n3. My sister is taller than me. [CORRECT]",
 "spelling": LONG + "\nresponsibility\ncolour / color",
 "typhoon": "Maximilian-Alexander\nCharlotte-Elisabeth\nTeacher",
 "battleships": "Maximilian-Alexander\nTeacher",
 "td": "",
}
VIEWS = [("ipad", 1180, 820), ("desktop", 1440, 860), ("phone", 390, 844), ("phonel", 844, 390)]
only = sys.argv[1:]  # e.g. python3 fit.py quiz taboo
games = [{"id":"g_" + t, "type":t, "title":t.title() + " with a very long title for " + LONG, "block":b, "options":({"boardId":"b1"} if t == "snakes" else {"show":"all", "cards":"Maximilian-Alexander", "tk":0} if t == "bingo" else {})} for t, b in blocks.items() if not only or t in only]
pack = {"id":"fit","student":"Maximilian-Alexander","lp":3,"title":"Fit","date":"2026-11-14","updatedAt":"x","games":games}
os.makedirs(os.path.join(HERE, "shots"), exist_ok=True)
def fit_check(view, ok, msg):
    """iPad and desktop must fit (Sam's rule). Phones get as close as half size allows: reported, not failed."""
    if view.startswith("phone"):
        print(("PASS " if ok else "NOTE ") + msg[:160])
    else: check(ok, msg)
def steps(pg, t):
    """A couple of taps into each game, so later screens are checked too."""
    tap = {"hangman":["[data-a=hm-show]"], "anagrams":["[data-a=an-show]"], "cards":["[data-a=fc-flip]"], "quiz":["[data-a=qz-ans]"],
           "taboo":["[data-a=tb-show]"], "wheel":["[data-a=wh-spin]"], "dice":["[data-a=sd-roll]"], "spot":["[data-a=se-tap]"], "odd":["[data-a=od-tap]"],
           "build":["[data-a=bd-put]"], "match":["[data-a=mu-tile]"], "auction":["[data-a=au-mark]"], "hilo":["[data-a=hl-call]"], "bingo":["[data-a=bg-next]"], "snakes":["[data-a=sn-roll]"],
           "typhoon":["[data-a=tp-unlock]", "[data-a=tp-pick]"], "battleships":["[data-a=bs-random]", "[data-a=bs-ready]"], "td":["[data-a=td-go]", "[data-a=td-start]"]}.get(t, [])
    for s in tap:
        if pg.locator(s).count():
            try: pg.locator(s).first.click(timeout=1500)
            except Exception: pass
            pg.wait_for_timeout(2600 if t in ("wheel", "snakes", "dice", "slot") else 350)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for name, w, h in VIEWS:
        ctx = b.new_context(viewport={"width":w, "height":h}, has_touch=name.startswith("phone"))
        errs = []; pg = teacher(ctx, seed_db([pack]), errs)
        go_lesson(pg, "Fit", "Maximilian"); pg.wait_for_timeout(300)
        for g in games:
            pg.evaluate("UI => 0", None)
            pg.click("[data-a=play][data-g=%s]" % g["id"]); pg.wait_for_timeout(450)
            if pg.evaluate("__T.UI.view") != "play":
                check(False, "%s %s didn't start: %s" % (name, g["type"], pg.evaluate("(document.querySelector('.toast')||{}).textContent"))); continue
            o = overflow(pg); pg.screenshot(path=os.path.join(HERE, "shots", "%s-%s-1.png" % (name, g["type"])))
            fit_check(name, not o, "%s %s start fits %s" % (name, g["type"], o))
            steps(pg, g["type"]); o = overflow(pg); pg.screenshot(path=os.path.join(HERE, "shots", "%s-%s-2.png" % (name, g["type"])))
            fit_check(name, not o, "%s %s after a move fits %s" % (name, g["type"], o))
            pg.evaluate("UI => { __T.UI.finishAsk=false; __T.UI.settingsOpen=false; }")
            if pg.evaluate("__T.UI.view") == "play":
                pg.click("[data-a=finish-ask]"); pg.wait_for_timeout(150); pg.click("[data-a=discard]"); pg.wait_for_timeout(250)
            elif pg.locator("[data-a=backlesson]").count(): pg.click("[data-a=backlesson]"); pg.wait_for_timeout(250)
        check(not errs, "%s no page errors %s" % (name, errs[:3]))
        ctx.close()
    # Class-link bar (19 Nov: "In person · class link only if needed" became a one-word column over the run sheet,
    # a laptop at half width): full width, text and Class link on one line or the button cleanly below, nothing overlapping.
    if not only or "clsbar" in only:
        rs = {"student":"Maximilian-Alexander", "lp":3, "date":"2026-11-14", "start":"17:00", "length":20, "format":"in person",
              "blocks":[{"label":"0 Arrival", "mins":10, "lines":[{"type":"cue", "label":"0A Warm-up chat"}]}, {"label":"1 Game", "mins":10, "lines":[{"type":"cue", "label":"1A Hangman"}]}]}
        cpacks = [dict(pack, id="cls-in", title="Bar in person", runsheet=rs, games=games[:2]),
                  dict(pack, id="cls-on", title="Bar online", runsheet=dict(rs, format="online · Google Meet"), games=games[:2])]
        BAR = """() => { const b = document.getElementById('clsBar'); if (!b) return { err: 'no bar' };
          const R = e => e.getBoundingClientRect(), br = R(b), par = b.parentElement, pc = getComputedStyle(par);
          const inner = par.clientWidth - parseFloat(pc.paddingLeft) - parseFloat(pc.paddingRight);
          const sp = R(b.querySelector(':scope > span')), bt = R(b.querySelector(':scope > button')), nx = b.nextElementSibling ? R(b.nextElementSibling) : null;
          const inside = r => r.left >= br.left - 1 && r.right <= br.right + 1 && r.top >= br.top - 1 && r.bottom <= br.bottom + 1;
          const sameRow = bt.top < sp.bottom && sp.top < bt.bottom, below = bt.top >= sp.bottom - 1;
          const out = [];
          if (br.width < inner - 2) out.push('bar ' + Math.round(br.width) + ' of ' + Math.round(inner) + ' wide');
          if (!inside(sp) || !inside(bt)) out.push('content spills out of the bar');
          if (sameRow ? bt.left < sp.right - 1 : !below) out.push('text and button overlap');
          if (sp.width < Math.min(200, br.width - 40)) out.push('text squeezed to ' + Math.round(sp.width) + 'px');
          if (nx && nx.top < br.bottom - 1) out.push('overlaps what follows');
          return { out, rows: sameRow ? 1 : 2, h: Math.round(br.height) }; }"""
        for w in (320, 390, 480, 560, 640, 720, 820, 1024, 1180, 1440):
            ctx = b.new_context(viewport={"width":w, "height":800}); errs = []; pg = teacher(ctx, seed_db(cpacks), errs)
            for cp in cpacks:
                go_lesson(pg, cp["title"], "Maximilian"); pg.wait_for_selector(".rs-blk"); pg.wait_for_timeout(150)
                for where in ("run sheet", "lesson page"):
                    if where == "lesson page": pg.click("[data-a=nav-games]"); pg.wait_for_selector(".head h2"); pg.wait_for_timeout(150)
                    r = pg.evaluate(BAR)
                    check(not r.get("err") and not r["out"], "class-link bar, %s, %s, %dpx: %s" % (("in person" if cp["id"] == "cls-in" else "online"), where, w, r.get("err") or r["out"] or "fits (%d row%s, %dpx tall)" % (r["rows"], "s" if r["rows"] > 1 else "", r["h"])))
                    if w in (390, 720): pg.screenshot(path=os.path.join(HERE, "shots", "clsbar-%s-%s-%d.png" % (cp["id"], where.split()[0], w)))
                pg.click("header.nav [data-a=student]") if pg.locator("header.nav [data-a=student]").count() else None
            check(not errs, "class-link bar sweep %dpx: no page errors %s" % (w, errs[:2]))
            ctx.close()
done()
