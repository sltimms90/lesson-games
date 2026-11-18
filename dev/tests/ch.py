"""Challenge button: Snakes & Ladders and Higher or Lower. Teacher-triggered, blocks play until marked, logged."""
from lg import *
games = [
  {"id":"g1","type":"snakes","title":"Race","block":"Mia\nTeacher","options":{"boardId":"b1","auto":True}},
  {"id":"g2","type":"hilo","title":"Cards","block":"Mia\nTeacher","options":{}},
  {"id":"g3","type":"hangman","title":"Words","block":"cat\ndog","options":{}},
]
pack = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-15","updatedAt":"x","games":games,
        "bank":"castle | a king lives here | The castle is old.\nbridge | you cross a river on it"}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, seed_db([pack]), errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    # in person, one screen
    t.click("[data-a=play][data-g=g3]"); t.wait_for_timeout(300)
    check(t.locator("header [data-a=challenge]").count() == 0, "no ⚡ on games other than Snakes & Ladders / Higher or Lower")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(200)
    t.click("[data-a=play][data-g=g1]"); t.wait_for_timeout(400)
    check(t.locator("header [data-a=challenge]").count() == 1, "⚡ in the header")
    t.click("header [data-a=challenge]"); t.wait_for_timeout(300)
    q = t.inner_text(".chq")
    check("castle" in q or "bridge" in q, "prompt comes from the word bank: %s" % q)
    check(t.locator("header [data-a=challenge]").is_disabled(), "⚡ greyed while one is open")
    t.evaluate("document.querySelector('[data-a=sn-roll]').click()"); t.wait_for_timeout(300)
    check(t.evaluate("__T.UI.run.st.phase") == "roll", "rolling waits for the challenge")
    t.click("[data-a=ch-mark][data-m=again]"); t.wait_for_timeout(200)
    q2 = t.inner_text(".chq"); check(q2 != q, "↻ gives another prompt: %s" % q2)
    t.click("[data-a=ch-mark][data-m=good]"); t.wait_for_timeout(300)
    check(t.locator(".chov").count() == 0 and len(t.evaluate("__T.UI.run.st.chLog")) == 1, "Good closes it and logs it")
    t.click("header [data-a=challenge]"); t.wait_for_timeout(200); t.click("[data-a=ch-mark][data-m=no]"); t.wait_for_timeout(200)
    t.click("[data-a=finish-ask]"); t.click("[data-a=finish]"); t.wait_for_timeout(500)
    r = t.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1')[0]")
    check(r and "challenges:" in r["summary"] and "✓" in r["summary"] and "✗" in r["summary"], "summary lists the challenges: %s" % (r and r["summary"]))
    check(r and len([x for x in r["items"] if x.get("challenge")]) == 2, "challenges are items in the result")
    check(t.locator("[data-a=retry]").count() == 0, "a missed challenge doesn't offer Retry the misses")
    # live, with a class link: the student sees the prompt, the teacher marks it
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl", timeout=5000); url = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    s = student(ctx, url, errs); s.wait_for_timeout(900)
    t.click("[data-a=play][data-g=g2]"); s.wait_for_selector("[data-a=hl-call]", timeout=5000); t.wait_for_timeout(300)
    t.click("header [data-a=challenge]"); s.wait_for_selector(".chq", timeout=3000)
    check(s.locator("[data-a=ch-mark]").count() == 0 and "Say it to your teacher" in s.inner_text(".chpop"), "student sees only the prompt")
    check(s.locator("header [data-a=challenge]").count() == 0, "student has no ⚡")
    s.evaluate("document.querySelector('[data-a=hl-call]').click()"); s.wait_for_timeout(300)
    check(s.evaluate("__T.UI.run.st.phase") == "call", "student can't call until it's marked")
    t.click("[data-a=ch-mark][data-m=good]"); s.wait_for_timeout(500)
    check(s.locator(".chov").count() == 0, "prompt closes on the student's screen")
    s.click("[data-a=hl-call] >> nth=0"); s.wait_for_timeout(500)
    check(s.evaluate("__T.UI.run.st.phase") != "call", "student plays on after the mark")
    check(not errs, "no page errors %s" % errs[:3])
    t.screenshot(path=HERE + "/shots/ch-teacher.png")
done()
