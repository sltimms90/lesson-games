"""Missed-words warm-up (Quick game from the last three lessons' misses) and the progress view in a student folder."""
from lg import *
def pk(i, date, bank=""):
    return {"id":"mia-lp%d" % i, "student":"Mia", "lp":i, "title":"Mia · LP%d" % i, "date":date, "updatedAt":"x", "games":[], "bank":bank}
packs = [pk(5, "2026-10-20"), pk(6, "2026-10-27", "castle | a king lives here\nbridge | you cross a river on it"), pk(7, "2026-11-03"), pk(8, "2026-11-10"), pk(9, "2026-11-17", "garden | flowers grow here")]
def res(rid, pid, ty, at, items):
    return {"id":rid, "packId":pid, "gameId":"g1", "type":ty, "title":ty, "at":at, "summary":ty + " — test", "items":items}
I = lambda item, ok, note="": {"item":item, "ok":ok, "note":note}
results = [
  res("r1", "mia-lp5", "hangman", "2026-10-20T03:00:00Z", [I("castle", False), I("tower", True)]),   # LP5 is too old for the warm-up
  res("r2", "mia-lp6", "spelling", "2026-10-27T03:00:00Z", [I("castle", False, "should be “castle”"), I("bridge", False), I("market", False)]),
  res("r3", "mia-lp7", "cards", "2026-11-03T03:00:00Z", [I("a big old house for a king", False, "answer: castle"), I("you cross a river on it", False, "answer: bridge · 2 tries")]),
  res("r4", "mia-lp8", "quiz", "2026-11-10T03:00:00Z", [I("Which word is a verb?", False, "answer “happy”"), I("Pick the noun", True)]),
  res("r5", "mia-lp8", "hangman", "2026-11-10T04:00:00Z", [I("bridge", True), I("castle", False, "wrong letters: e")]),
  res("r10", "mia-lp8", "spelling", "2026-11-10T08:00:00Z", [I("market", False, "should be “market”")]),
  res("r6", "mia-lp8", "whack", "2026-11-10T05:00:00Z", [I("went", False, "a right answer · appeared 3"), I("goed", False, "a wrong answer · appeared 2")]),
  res("r8", "mia-lp7", "quiz", "2026-11-03T04:00:00Z", [I("Which of these is a verb?", False, "answer “climb”")]),
  res("r9", "mia-lp8", "quiz", "2026-11-10T07:00:00Z", [{"item":"Pick the action word", "ans":"climb", "ok":False, "note":"answer “climb”"}, {"item":"Pick the colour", "ans":"blue", "ok":True, "note":""}]),
  res("r7", "mia-lp8", "snakes", "2026-11-10T06:00:00Z", [{"item":"Challenge: Make a sentence with “river”.", "ok":False, "note":"word: river", "w":"river", "challenge":True}]),
]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, seed_db(packs, results=results), errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    picker(t); btn = t.locator("[data-a=qscope][data-v=missed]")
    check(btn.count() == 1, "Quick game offers Missed lately")
    words = t.evaluate("(() => { const p = __T.PACKS.find(x => x.id === 'mia-lp9'); return null; })()")
    scope(t, "missed"); t.wait_for_timeout(200)
    txt = t.inner_text(".section >> nth=0") if False else t.inner_text("#app")
    import re
    m = re.search(r"Warm-up · \d+ words: ([^\n]*)", txt); wl = m.group(1) if m else ""
    check("castle" in wl and "bridge" in wl and "market" in wl and "went" in wl and "river" in wl, "warm-up words from the last 3 lessons: %s" % wl)
    check("goed" not in wl and "tower" not in wl and "verb" not in wl, "leaves out distractors, right answers and sentences")
    check("Missed lately (5)" in btn.inner_text(), "count on the button: %s" % btn.inner_text())
    quick(t, "hangman"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "play" and "missed words" in t.evaluate("__T.UI.run.title"), "Hangman built from the missed words: %s" % t.evaluate("__T.UI.run.title"))
    ws = t.evaluate("__T.UI.run.st.words.map(w => w.w + '|' + (w.c||''))")
    check(any(x.startswith("castle|a king lives here") for x in ws), "clue taken from the word bank: %s" % ws)
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(200)
    # progress view
    t.click("[data-a=student][data-s=Mia] >> nth=0"); t.wait_for_timeout(300)
    check(t.locator(".pg").count() == 1, "student folder has a Progress section")
    pg = t.inner_text(".pg")
    check(t.locator(".pg-row").count() == 4, "one bar per lesson with results (%d)" % t.locator(".pg-row").count())
    keeps = pg.split("Keeps coming up")[1] if "Keeps coming up" in pg else ""
    check("castle" in keeps and "4 lessons" in keeps, "castle keeps coming up across 4 lessons: %s" % keeps[:200])
    check("bridge" not in keeps.split("Got right last time")[0], "bridge (right last time) isn't in Keeps coming up")
    check("Got right last time (1)" in pg, "bridge counted as got right last time")
    check("climb" in keeps and "(“Pick the action word”)" in keeps, "a quiz miss shows its answer word, with the question as a hint: %s" % keeps[:300])
    check("Which word is a verb?" not in pg and "Which of these is a verb?" not in keeps.split("climb")[0], "whole quiz questions aren't listed as words")
    once = t.evaluate("[...document.querySelectorAll('.pg details')].map(d => d.textContent).join(' | ')")
    check("happy" in once.split("Missed once")[1] if "Missed once" in once else False, "a quiz answer missed once goes under Missed once: %s" % once[-120:])
    t.screenshot(path=HERE + "/shots/prog.png", full_page=True)
    # Quick game from these → newest lesson, Quick game on Keeps coming up
    check(t.locator("[data-a=pg-quick]").count() == 1, "Keeps coming up offers Quick game from these")
    t.click("[data-a=pg-quick]"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.view") == "pack" and t.evaluate("__T.UI.packId") == "mia-lp9", "it opens the newest lesson: %s" % t.evaluate("__T.UI.packId"))
    sb = t.locator("[data-a=qscope][data-v=stuck]")
    check(t.locator(".picker").count() == 1 and sb.count() == 1 and "btn sm ghost" not in sb.get_attribute("class") and "Keeps coming up ·" in t.inner_text(".picker") and "castle" in t.inner_text(".picker") and "climb" in t.inner_text(".picker"), "the picker opens set to Keeps coming up: %s" % t.inner_text(".picker")[:200])
    tile(t, "matching"); t.click("[data-a=pick-mode][data-m=cards]")
    check(t.locator("[data-a=pick-go]").is_disabled() and "Needs 3 words with clues" in t.inner_text(".pk-go"), "Flash Cards needs 3 words with clues (market has none), so Start is off: %s" % t.inner_text(".pk-go"))
    quick(t, "hangman"); t.wait_for_timeout(400)
    ws = t.evaluate("__T.UI.run.st.words.map(w => w.w + '|' + (w.c||''))")
    check(t.evaluate("__T.UI.view") == "play" and sorted(x.split("|")[0] for x in ws) == ["castle", "climb", "market"] and "climb|Pick the action word" in ws, "Hangman built from them, the quiz question as climb's clue: %s" % ws)
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(200)
    check(not errs, "no page errors %s" % errs[:3])
done()
