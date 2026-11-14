"""Screen-fit sweep: every game type with long content at landscape iPad, desktop and phone.
Nothing may scroll or spill off screen. Screenshots go to dev/tests/shots/ (not committed)."""
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
           "build":["[data-a=bd-put]"], "match":["[data-a=mu-tile]"], "auction":["[data-a=au-mark]"], "hilo":["[data-a=hl-call]"], "bingo":["[data-a=bg-next]"], "snakes":["[data-a=sn-roll]"]}.get(t, [])
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
        pg.wait_for_selector("text=Fit", timeout=8000); pg.click("text=Fit"); pg.wait_for_timeout(300)
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
done()
