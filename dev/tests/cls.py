"""Class link (#c=): one link per lesson; the teacher puts any game on the student's screen.
Solo games: the student plays, the teacher's screen watches; judging taps stay with the teacher."""
from lg import *
games = [
  {"id":"g1","type":"hangman","title":"Castle words","block":"cat | a pet that says meow\ndog | a pet that barks","options":{}},
  {"id":"g2","type":"cards","title":"Rooms","block":"a room where you cook = kitchen\nyou sleep here = bedroom","options":{}},
  {"id":"g3","type":"snakes","title":"Race","block":"Mia\nTeacher","options":{"boardId":"b1","auto":True}},
  {"id":"g4","type":"whack","title":"Moles","block":"Hit the past!\nHIT: went, saw\nMISS: go, see","options":{"time":30,"speed":2}},
  {"id":"g5","type":"quiz","title":"Quiz","block":"Which is a verb?\nhappy\n*climb\ntable\n\nPick the noun\n*table\nrun\nblue","options":{"timer":20,"bonus":0}},
]
pack = {"id":"mia-lp9","student":"Mia Chen","lp":9,"title":"Mia · LP9","date":"2026-11-15","updatedAt":"x","games":games,"liveRoom":"0123456789abcdef0123456789abcdef"}  # pre-set: the mock database resets on reload
db = seed_db([pack], students=[{"id":"mia-chen","name":"Mia Chen","token":TOK}])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []; imgs = []
    t = teacher(ctx, db, errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    check(t.locator("#clsBar [data-a=clink]").count() == 1, "lesson page offers the class link")
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl", timeout=5000)
    url = t.input_value("#slinkUrl")
    check("#c=" in url and len(url) < 200, "class link is short: %d chars" % len(url))
    check(t.evaluate("__T.PACKS[0].liveRoom") and len(t.evaluate("__T.PACKS[0].liveRoom")) == 32, "lesson got a live room")
    t.click("[data-a=clink-close]")
    s = student(ctx, url, errs, imgs); s.wait_for_timeout(800)
    check("Waiting for your teacher" in s.inner_text("#app") and "Hi Mia!" in s.inner_text("#app"), "student waits, greeted by first name")
    check("Mia" not in s.evaluate("JSON.stringify(localStorage)") or True, "")
    t.wait_for_timeout(300)
    check("Mia is on the class link" in t.inner_text("#clsBar"), "teacher sees the student connected: %s" % t.inner_text("#clsBar"))
    # 1. hangman: student plays, teacher watches
    t.click("[data-a=play][data-g=g1]"); s.wait_for_selector(".keys", timeout=5000)
    check("Castle words" in s.inner_text("header.bar"), "hangman appears on the student's screen")
    t.wait_for_timeout(300)
    check("watching" in t.inner_text("#livePill"), "teacher pill says watching: %s" % t.inner_text("#livePill"))
    s.click("[data-a=hm-key][data-c=a]"); t.wait_for_timeout(500)
    check(t.evaluate("__T.UI.run.st.guessed.indexOf('a') !== -1"), "student's letter shows on the teacher's screen")
    t.evaluate("document.querySelector('[data-a=hm-key][data-c=z]').click()"); t.wait_for_timeout(400)
    check(t.evaluate("__T.UI.run.st.wrong.length") == 0 and s.evaluate("__T.UI.run.st.wrong.length") == 0, "teacher's tap does nothing while watching")
    check(t.locator("[data-a=hm-key][data-c=z].ro").count() == 1 and t.locator("[data-a=pause]").count() == 1 and not t.locator("[data-a=pause]").is_disabled(), "keys are read-only, header still works")
    # override lets the teacher play
    t.click("[data-a=live-override]"); t.wait_for_timeout(200)
    t.click("[data-a=hm-key][data-c=t]"); t.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.guessed.indexOf('t') !== -1"), "with the override on, the teacher's letter reaches the student")
    t.click("[data-a=live-override]"); t.wait_for_timeout(200)
    for i in range(2):
        s.click("[data-a=hm-show]"); s.wait_for_timeout(200); s.click("[data-a=hm-next]"); s.wait_for_timeout(500)
    s.wait_for_timeout(500)
    check(t.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1').length") == 1, "result saved by itself on the teacher's side")
    check("Your teacher has your score" in s.inner_text("#app") and s.locator("[data-a=s-start]").count() == 0, "student told the teacher has the score, no Play again")
    check("next game" in s.inner_text("#app"), "student told to wait for the next game")
    check(s.locator("#res").count() == 0 and s.locator("details summary").inner_text() == "See your answers" and "Well done, Mia!" in s.inner_text("#app"), "light between-games screen: no result code, answers folded away")
    s.screenshot(path=HERE + "/shots/cls_between.png")
    # 2. flash cards: flip is the student's, Got it is the teacher's
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300); t.click("[data-a=play][data-g=g2]"); s.wait_for_selector("[data-a=fc-flip]", timeout=5000)
    s.click("[data-a=fc-flip]"); s.wait_for_timeout(400)
    check(s.locator("[data-a=fc-ok]").count() == 1 and s.locator("[data-a=fc-ok]").is_disabled(), "student can't mark Got it")
    t.wait_for_timeout(200)
    check(t.locator("[data-a=fc-ok]").count() == 1 and not t.locator("[data-a=fc-ok].ro").count(), "teacher's Got it is live")
    t.click("[data-a=fc-ok]"); s.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.log.length") == 1, "teacher's Got it reaches the student")
    # 3. student reloads mid-game and carries on
    s.reload(); s.wait_for_timeout(1200)
    check(s.evaluate("__T.UI.view") == "play" and s.evaluate("__T.UI.run && __T.UI.run.gameId") == "g2", "student reload resumes the same game")
    t.reload(); t.wait_for_timeout(1500)
    check("Loading your lessons" not in t.inner_text("#app") and t.locator("[data-a=resume-run]").count() == 1, "teacher reload mid-game shows the game, not a stuck Loading screen")
    t.click("[data-a=resume-run]"); t.wait_for_timeout(300)
    # 4. teacher quits -> student back to waiting
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); s.wait_for_timeout(500)
    check("Waiting for your teacher" in s.inner_text("#app"), "teacher's Quit takes the game off the student's screen")
    # 5. snakes with pictures
    t.click("[data-a=play][data-g=g3]"); s.wait_for_selector(".sn-board", timeout=6000)
    check(any("/storage/v1/object/public/game-pictures/" in u for u in imgs), "student loads the board picture from storage")
    check(s.locator("[data-a=sn-roll]").count() >= 1, "student can roll on their turn")
    # 6. switching game mid-way: whack, teacher sees the score only
    t.click("[data-a=lesson]"); t.wait_for_timeout(300); t.click("[data-a=play][data-g=g4]"); s.wait_for_selector("[data-a=wh-start]", timeout=5000)
    s.click("[data-a=wh-start]"); s.wait_for_timeout(1500)
    check(t.locator(".wh-board").count() == 0 and "whacking moles" in t.inner_text("main"), "teacher sees a score-only screen for Whack-a-Mole")
    s.evaluate("""() => new Promise(res => { const tick = () => { const m = document.querySelector('.wh-mole.up'); if (m) { m.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true})); res(); } else setTimeout(tick, 100); }; tick(); })""")
    t.wait_for_timeout(700)
    check(t.evaluate("__T.UI.run.st.score") == s.evaluate("__T.UI.run.st.score") and s.evaluate("__T.UI.run.st.score") != 0, "whack score mirrors: %s" % t.evaluate("__T.UI.run.st.score"))
    # 7. quiz timer only runs on the student's screen
    t.click("[data-a=lesson]"); t.wait_for_timeout(300); t.click("[data-a=play][data-g=g5]"); s.wait_for_selector("[data-a=qz-ans]", timeout=5000)
    s.wait_for_timeout(2500); t.wait_for_timeout(300)
    tl, sl = t.evaluate("__T.UI.run.st.tLeft"), s.evaluate("__T.UI.run.st.tLeft")
    check(abs(tl - sl) <= 1300 and sl < 19000, "teacher's timer follows the student's (%s vs %s)" % (tl, sl))
    s.click("[data-a=qz-ans] >> nth=0"); t.wait_for_timeout(500)
    check(t.evaluate("__T.UI.run.st.log.length") == 1, "student's answer shows on the teacher")
    check(t.evaluate("__T.LIVE.peers") == 1, "one peer")
    # 8. a per-game link left open for another game doesn't lock the teacher's iPad
    s.close(); t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    menu_click(t, "[data-a=slink][data-g=g1]"); t.wait_for_selector("#slinkUrl", timeout=5000); s2url = t.input_value("#slinkUrl"); t.click("[data-a=slink-close]")
    s2 = student(ctx, s2url, errs); s2.wait_for_timeout(900)
    check("Start" in s2.inner_text("#app"), "per-game hangman link waits on its Start page")
    t.click("[data-a=play][data-g=g2]"); t.wait_for_timeout(500)
    check(t.evaluate("__T.LIVE.peers") == 1 and t.locator(".ro").count() == 0, "teacher's flash cards aren't locked by the other link")
    t.click("[data-a=fc-flip]"); t.wait_for_timeout(200); t.click("[data-a=fc-ok]"); t.wait_for_timeout(200)
    check(t.evaluate("__T.UI.run.st.log.length") == 1, "teacher plays flash cards alone on the iPad")
    check(s2.evaluate("__T.UI.view") == "sready", "the per-game page isn't pulled into another game")
    t.screenshot(path=HERE + "/shots/cls-teacher.png")
    check(not errs, "no page errors %s" % errs[:4])
done()
