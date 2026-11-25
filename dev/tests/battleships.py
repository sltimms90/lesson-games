"""Battleships + Finish later (25 Nov brief, part 2). Teacher vs student, each fleet placed on its own screen.
The teacher's unsunk ships never reach the student's page; the student's ships are drawn on the teacher's screen only
when sunk or with ⚙ Show outlines (local to the teacher's screen, off every time). Finish later keeps the game on the
student's record and the next lesson offers Continue · Discard."""
import json
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get UNDO(){return UNDO},get STUDENTS(){return STUDENTS},get BS_PEEK(){return BS_PEEK},", 1)
N = 8
def cells(r, c, d, n):
    return [(r + (j if d == "v" else 0)) * N + c + (0 if d == "v" else j) for j in range(n)]
# teacher: rows C..F, horizontal, from column 1; student: columns 8..5 vertical from row A
T_DRAFT = [{"r":2, "c":0, "d":"h"}, {"r":3, "c":0, "d":"h"}, {"r":4, "c":0, "d":"h"}, {"r":5, "c":0, "d":"h"}]
S_DRAFT = [{"r":0, "c":7, "d":"v"}, {"r":0, "c":6, "d":"v"}, {"r":0, "c":5, "d":"v"}, {"r":0, "c":4, "d":"v"}]
FLEET = [4, 3, 3, 2]
T_CELLS = [cells(o["r"], o["c"], o["d"], FLEET[k]) for k, o in enumerate(T_DRAFT)]
S_CELLS = [cells(o["r"], o["c"], o["d"], FLEET[k]) for k, o in enumerate(S_DRAFT)]
games = [{"id":"bs1", "type":"battleships", "title":"Battleships", "block":"", "options":{"size":8, "fleet":"4, 3, 3, 2"}},
         {"id":"ty1", "type":"typhoon", "title":"Typhoon", "block":"", "options":{"size":3, "grid":[{"t":x, "m":""} for x in ["10", "20", "T", "x2", "50", "5", "25", "30", "40"]]}}]
room = "0123456789abcdef0123456789abcdef"
pack1 = {"id":"lily-lp7", "student":"Lily", "lp":7, "title":"Lily · LP7", "date":"2026-11-25", "updatedAt":"x", "games":games, "liveRoom":room}
pack2 = {"id":"lily-lp8", "student":"Lily", "lp":8, "title":"Lily · LP8", "date":"2026-11-25", "updatedAt":"x", "games":[], "liveRoom":room}
db = seed_db([pack1, pack2])
def st(pg): return pg.evaluate("JSON.parse(JSON.stringify(__T.UI.run.st))")
def blob(s): return s.evaluate("String(localStorage.getItem('lessonGames.student.v1')) + document.documentElement.outerHTML + JSON.stringify(__T.LIVE.last)")
def tfleet_leaks(s, sunk=()):
    b = blob(s).replace(" ", ""); return [k for k, c in enumerate(T_CELLS) if k not in sunk and json.dumps(c).replace(" ", "") in b]
def link(t, title):
    go_lesson(t, title); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); u = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]"); return u
def place(pg, draft):
    pg.evaluate("d => { __T.UI.run.hid.draft = d; }", draft); pg.click("[data-a=bs-random]"); pg.evaluate("d => { __T.UI.run.hid.draft = d; }", draft)
    pg.evaluate("() => document.querySelector('[data-a=bs-ready]').disabled = false"); pg.click("[data-a=bs-ready]")
def fire(pg, i): pg.click(".bs-shots [data-a=bs-fire][data-c='%d']" % i)
def let(t, s): t.click("[data-a=bs-let]"); s.wait_for_selector(".bs-shots [data-a=bs-fire]", timeout=4000)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, db, errs); url = link(t, "Lily · LP7")
    s = student(ctx, url, errs); s.wait_for_timeout(900)
    t.click("[data-a=play][data-g=bs1]"); s.wait_for_selector(".bs-setup", timeout=6000); t.wait_for_timeout(300)
    # ---- 1. placement rules (teacher's screen)
    check(t.locator(".bs-place .bs-c").count() == 64 and t.locator("[data-a=bs-ready]").is_disabled(), "8×8 placement grid; Ready waits for every ship")
    t.click(".bs-place [data-c='0']")
    check(st(t)["phase"] == "place" and t.evaluate("JSON.stringify(__T.UI.run.hid.draft[0])") == json.dumps({"r":0, "c":0, "d":"h"}).replace(" ", ""), "tap a square: the 4-ship goes there")
    t.click(".bs-place [data-c='1']")
    check(t.evaluate("__T.UI.run.hid.draft[0].d") == "v", "tap the ship again: it turns")
    t.click(".bs-place [data-c='63']")
    check(t.evaluate("JSON.stringify(__T.UI.run.hid.draft[1])") == '{"r":7,"c":5,"d":"h"}', "near the edge it fits inwards, never off the grid: %s" % t.evaluate("JSON.stringify(__T.UI.run.hid.draft[1])"))
    t.click(".bs-place [data-c='63']")
    check(t.evaluate("__T.UI.run.hid.draft[1].d") == "h", "no room to turn at the edge: it stays")
    t.click("[data-a=bs-sel][data-k='2']"); t.click(".bs-place [data-c='60']")
    d2 = t.evaluate("JSON.stringify(__T.UI.run.hid.draft[2])")
    check(d2 == '{"r":7,"c":2,"d":"h"}', "against a ship it can't overlap: placed clear of it, on the grid (%s)" % d2)
    # drag ship 2 onto ship 0: refused
    a, z = t.locator(".bs-place [data-c='59']").bounding_box(), t.locator(".bs-place [data-c='17']").bounding_box()
    t.mouse.move(a["x"] + 10, a["y"] + 10); t.mouse.down(); t.mouse.move(z["x"] + 10, z["y"] + 10, steps=4); t.mouse.up(); t.wait_for_timeout(200)
    check(t.evaluate("JSON.stringify(__T.UI.run.hid.draft[2])") == d2, "drag onto another ship: refused")
    z2 = t.locator(".bs-place [data-c='42']").bounding_box()
    t.mouse.move(a["x"] + 10, a["y"] + 10); t.mouse.down(); t.mouse.move(z2["x"] + 10, z2["y"] + 10, steps=4); t.mouse.up(); t.wait_for_timeout(200)
    check(t.evaluate("JSON.stringify(__T.UI.run.hid.draft[2])") == '{"r":5,"c":1,"d":"h"}', "drag to move: %s" % t.evaluate("JSON.stringify(__T.UI.run.hid.draft[2])"))
    check(t.locator("[data-a=bs-ready]").is_disabled(), "Ready still waits for the last ship")
    t.click("[data-a=bs-random]"); dr = t.evaluate("__T.UI.run.hid.draft")
    occ = [c for k, o in enumerate(dr) for c in cells(o["r"], o["c"], o["d"], FLEET[k])]
    check(len(occ) == 12 and len(set(occ)) == 12 and all(0 <= c < 64 for c in occ) and all(o["c"] + (FLEET[k] if o["d"] == "h" else 1) <= 8 and o["r"] + (FLEET[k] if o["d"] == "v" else 1) <= 8 for k, o in enumerate(dr)), "Random: every ship on the grid, no overlaps")
    check(not t.locator("[data-a=bs-ready]").is_disabled(), "Ready once all are placed")
    # ---- 2. Ready gating
    place(t, T_DRAFT); s.wait_for_timeout(400)
    check(st(t)["tReady"] and st(t)["phase"] == "place" and "Waiting for Lily" in t.inner_text("main"), "teacher Ready: waits for the student")
    check("hid" not in json.dumps(st(s)) and not tfleet_leaks(s), "leak: the teacher's fleet isn't on the student's page %s" % tfleet_leaks(s))
    place(s, S_DRAFT); t.wait_for_timeout(600)
    check(st(t)["phase"] == "play" and st(t)["sFleet"] == S_CELLS and st(s)["phase"] == "play", "both Ready: play starts, the student's fleet arrives once")
    check(not tfleet_leaks(s), "leak: still no teacher fleet on the student's page")
    check(t.locator(".bs-shots .bs-c.ship, .bs-shots .bs-c.pk").count() == 0, "teacher's screen doesn't draw the student's ships (outlines off)")
    # ---- 3. turns: lock → Let them fire → one shot → auto-lock → teacher's turn
    check("Answer the question first" in s.inner_text("main") and s.locator("[data-a=bs-fire]").count() == 0, "student locked until Let them fire")
    let(t, s); fire(s, T_CELLS[3][0]); t.wait_for_timeout(600)
    check(st(t)["sShots"] == {str(T_CELLS[3][0]):1} and st(t)["turn"] == "t" and not st(t)["unlocked"], "student fires once: a hit, locked, teacher's turn")
    check("Hit at F1!" in s.inner_text("main") and "Lily hit your ship at F1!" in t.inner_text("main"), "hit message on both screens")
    check(s.locator("[data-a=bs-fire]").count() == 0 and "Teacher’s turn" in s.inner_text("main"), "auto-lock; Your turn / Teacher's turn line")
    fire(t, 0); s.wait_for_timeout(500)
    check(st(s)["tShots"] == {"0":0} and st(s)["turn"] == "s" and not st(s)["unlocked"], "teacher fires: a miss, back to the student (locked)")
    # tap while locked: a crafted shot is ignored
    s.evaluate("() => { const L = __T.LIVE, r = __T.UI.run, x = JSON.parse(JSON.stringify(r.st)); x.pick = 20; L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:r.gameId, p:r.packId, gen:r.liveGen, t0:r.liveT0, rev:(r.st._rev||0)+3, st:x, from:L.me, r:'s' } }); }")
    t.wait_for_timeout(500)
    check("20" not in st(t)["sShots"], "a shot sent while locked is ignored")
    # Extra shot / Skip my turn
    let(t, s); fire(s, 0); t.wait_for_timeout(500)
    check(st(t)["sShots"].get("0") == 0 and st(t)["turn"] == "t", "a miss: teacher's turn")
    t.click("[data-a=bs-extra]"); s.wait_for_selector(".bs-shots [data-a=bs-fire]", timeout=4000)
    check(st(s)["turn"] == "s" and st(s)["unlocked"], "Extra shot: the student fires again without the teacher firing")
    fire(s, 1); t.wait_for_timeout(500)
    t.click("[data-a=bs-skip]"); s.wait_for_timeout(400)
    check(st(s)["turn"] == "s" and not st(s)["unlocked"] and len(st(s)["tShots"]) == 1, "Skip my turn: straight back to the student")
    # undo a shot (Settings → Undo)
    let(t, s); fire(s, 2); t.wait_for_timeout(500)
    check("2" in st(t)["sShots"], "shot at A3")
    t.click("[data-a=settings]"); t.click("[data-a=undo]"); s.wait_for_timeout(500)
    check("2" not in st(t)["sShots"] and "2" not in st(s)["sShots"], "Settings → Undo takes the shot back on both screens")
    # ---- 4. peek
    t.click("[data-a=bs-lock]") if t.locator("[data-a=bs-lock]").count() else None
    s.wait_for_timeout(300); sbefore = s.inner_html("main")
    t.click("[data-a=settings]"); check(t.locator(".setpop [data-a=bs-peek]").inner_text().strip() == "Show outlines" and t.locator("header [data-a=bs-peek], main [data-a=bs-peek]").count() == 0, "peek: a plain toggle inside ⚙ only")
    t.click(".setpop [data-a=bs-peek]"); t.click(".setpop [data-a=settings]"); t.wait_for_timeout(300)
    pk = t.locator(".bs-shots .bs-c.pk").count()
    check(pk == 12 and t.locator(".bs-shots .bs-c.ship").count() == 0, "Show outlines: the student's 12 ship squares as faint outlines, no fill (%d)" % pk)
    col = t.evaluate("getComputedStyle(document.querySelector('.bs-shots .bs-c.pk')).backgroundColor === getComputedStyle(document.querySelector('.bs-shots .bs-c:not(.pk)')).backgroundColor")
    check(col, "outline squares have the sea's own colour (no colour fill)")
    s.wait_for_timeout(400)
    check(s.inner_html("main") == sbefore, "the student's screen is unchanged with outlines on")
    sent = t.evaluate("JSON.stringify(__T.LIVE.last) + JSON.stringify(__T.UI.run) + localStorage.getItem('lessonGames.ui.v2')")
    check("peek" not in sent.lower() and "outline" not in sent.lower(), "the outlines flag is in no state, message or saved copy")
    t.reload(); t.wait_for_timeout(1500)
    if t.locator("[data-a=resume-run]").count(): t.click("[data-a=resume-run]"); t.wait_for_timeout(300)
    check(t.evaluate("__T.BS_PEEK") is False and t.locator(".bs-shots .bs-c.pk").count() == 0, "outlines off after a reload")
    # ---- 5. hit / sunk messages
    let(t, s); fire(s, T_CELLS[3][1]); t.wait_for_timeout(600)
    check(st(s)["tSunk"] == [T_CELLS[3]] and "You sank a 2-ship!" in s.inner_text("main") and "Lily sank your 2-ship!" in t.inner_text("main"), "sunk: the message on both screens")
    check(s.locator(".bs-shots .bs-c.ship.sunk").count() == 2 and tfleet_leaks(s, sunk=(3,)) == [], "the sunk ship shows on the student's screen; the rest stay hidden %s" % tfleet_leaks(s, sunk=(3,)))
    fire(t, S_CELLS[3][0]); s.wait_for_timeout(400)
    # ---- 6. Finish later
    t.click("[data-a=finish-ask]"); t.click("[data-a=fl-later]"); t.wait_for_timeout(600)
    r1 = [x for x in t.evaluate("__T.RESULTS") if x["gameId"] == "bs1"]
    check(len(r1) == 1 and r1[0].get("partial") and r1[0]["summary"].startswith("Battleships 8×8 (continued, not finished): Lily 4 shots, 2 hits, sank 1 · Teacher 2 shots, 1 hit, sank 0"), "this lesson's part is saved, marked partial: %s" % (r1 and r1[0]["summary"]))
    pz = t.evaluate("__T.STUDENTS['lily'] && __T.STUDENTS['lily'].paused")
    check(pz and pz["battleships"]["hid"]["fleet"] == T_CELLS and pz["battleships"]["st"]["sFleet"] == S_CELLS, "the whole game is kept on the student's record (both fleets, shots, turn)")
    check("peek" not in json.dumps(pz).lower() and "peek" not in json.dumps(r1).lower(), "no outlines flag in the paused game or the result")
    s.wait_for_timeout(500); check("Waiting for your teacher" in s.inner_text("#app"), "the student's screen goes back to waiting")
    saved_st = pz["battleships"]["st"]
    # ---- 7. next lesson: Continue
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300); url2 = link(t, "Lily · LP8")
    check("Battleships in progress (started" in t.inner_text("#app") and t.locator("[data-a=fl-cont][data-t=battleships]").count() == 1, "next lesson: Battleships in progress · Continue · Discard")
    s.close(); s = student(ctx, url2, errs); s.wait_for_timeout(900)
    t.click("[data-a=fl-cont][data-t=battleships]"); s.wait_for_selector(".bs-play", timeout=6000); s.wait_for_timeout(400)
    now = st(t); keep = lambda x: {k: v for k, v in x.items() if k not in ("base", "_rev")}
    check(keep(now) == keep(saved_st) and t.evaluate("JSON.stringify(__T.UI.run.hid.fleet)") == json.dumps(T_CELLS).replace(" ", ""), "Continue restores the game exactly")
    check(st(s)["sShots"] == saved_st["sShots"] and not tfleet_leaks(s, sunk=(3,)), "the student's screen gets only what it may see %s" % tfleet_leaks(s, sunk=(3,)))
    check(t.evaluate("__T.BS_PEEK") is False and t.locator(".bs-shots .bs-c.pk").count() == 0, "outlines off after Continue")
    check("Battleships in progress" not in (t.inner_text("#app")), "no Continue offer on the game screen")
    # ---- 8. win, final result
    for k in range(3):
        for i, c in enumerate(T_CELLS[k]):
            if st(t)["phase"] != "play": break
            if st(t)["turn"] == "t": t.click("[data-a=bs-skip]"); s.wait_for_timeout(250)
            let(t, s); fire(s, c); t.wait_for_timeout(350)
    check(st(t)["winner"] == "s" and "You win!" in s.inner_text("main") and "Lily wins!" in t.inner_text("main"), "the last ship sunk: winner screen on both")
    t.click("main [data-a=finish]"); t.wait_for_timeout(600)
    r2 = [x for x in t.evaluate("__T.RESULTS") if x["packId"] == "lily-lp8" and x["type"] == "battleships"]
    check(len(r2) == 1 and r2[0].get("finished") and not r2[0].get("partial") and "(continued, finished): Lily won" in r2[0]["summary"], "the final lesson's result: finished, with the winner: %s" % (r2 and r2[0]["summary"]))
    check("battleships" not in (t.evaluate("__T.STUDENTS['lily'].paused") or {}), "finished: no longer kept for later")
    check(r2 and r2[0]["items"] == [] and r2[0]["points"] == 0, "no items (missed words ignore it), no lesson points")
    # ---- 9. Discard, and the replace prompt (Typhoon too: Finish later is for any pausable game)
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    for k in range(2):
        t.click("[data-a=play][data-g=%s]" % ("bs1" if k == 0 else "bs1")) if t.locator("[data-a=play][data-g=bs1]").count() else (t.click("[data-a=home]"), go_lesson(t, "Lily · LP7"), t.click("[data-a=play][data-g=bs1]"))
        t.wait_for_timeout(400); t.click("[data-a=finish-ask]"); t.click("[data-a=fl-later]"); t.wait_for_timeout(400)
        if k == 1:
            check("already has a Battleships game kept from" in t.inner_text(".setpop"), "starting another one asks to replace the kept game")
            first = t.evaluate("__T.STUDENTS['lily'].paused.battleships.id"); t.click("[data-a=fl-replace]"); t.wait_for_timeout(400)
            check(t.evaluate("__T.STUDENTS['lily'].paused.battleships.id") != first, "Keep this one replaces it")
        t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    t.click("[data-a=play][data-g=ty1]"); t.wait_for_timeout(300)
    t.click("[data-a=tp-unlock]"); t.wait_for_timeout(200)
    if t.locator("[data-a=tp-pick][data-c=A1]").count(): t.click("[data-a=tp-pick][data-c=A1]")
    else:
        s.wait_for_selector("[data-a=tp-pick]:not([disabled])", timeout=4000); s.click("[data-a=tp-pick][data-c=A1]")
    t.wait_for_timeout(500); t.click("[data-a=tp-score][data-k='0'][data-d='1']"); t.click("[data-a=finish-ask]"); t.click("[data-a=fl-later]"); t.wait_for_timeout(400)
    tz = t.evaluate("__T.STUDENTS['lily'].paused.typhoon")
    check(tz and tz["st"]["open"]["A1"]["t"] == "10" and tz["hid"]["grid"][2]["t"] == "T" and tz["st"]["players"][0]["score"] == 1, "Typhoon: Finish later keeps grid, opened boxes and tally")
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    check(t.locator(".flbar").count() == 2, "both kept games are offered")
    t.click("[data-a=fl-disc][data-t=battleships]"); check(t.locator("[data-a=fl-disc][data-t=battleships]").inner_text().startswith("Tap again"), "Discard asks once more")
    t.click("[data-a=fl-disc][data-t=battleships]"); t.wait_for_timeout(300)
    check("battleships" not in t.evaluate("__T.STUDENTS['lily'].paused") and t.locator(".flbar").count() == 1, "Discard throws it away")
    t.click("[data-a=fl-cont][data-t=typhoon]"); t.wait_for_timeout(500)
    check(st(t)["open"]["A1"]["t"] == "10" and st(t)["players"][0]["score"] == 1 and t.evaluate("__T.UI.run.hid.grid[2].t") == "T", "Typhoon continues where it stopped")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    check(t.locator(".flbar").count() == 1, "Quit without saving a continued game keeps it for later")
    # backup includes the kept games
    check("paused" in json.dumps(t.evaluate("(() => { const s = __T.STUDENTS; return Object.keys(s).map(k => s[k]); })()")), "kept games are in the students records (backup / restore / weekly snapshot)")
    s.close()
    # ---- 10. screen fit: iPad both grids side by side; phone teacher tabs; desktop
    for name, w, h, who in [("ipad", 1180, 820, "s"), ("phone", 390, 844, "t"), ("desktop", 1440, 860, "t"), ("ipad10", 1180, 820, "s10")]:
        c2 = b.new_context(viewport={"width":w, "height":h}, has_touch=(name == "phone")); e2 = []
        g10 = dict(games[0], id="bs10", options={"size":10, "fleet":"5, 4, 3, 3, 2"})
        pk = dict(pack1, games=[games[0], g10]); t2 = teacher(c2, seed_db([pk]), e2); u2 = link(t2, "Lily · LP7")
        s2 = student(c2, u2, e2); s2.wait_for_timeout(800)
        t2.click("[data-a=play][data-g=%s]" % ("bs10" if who == "s10" else "bs1")); s2.wait_for_selector(".bs-setup", timeout=6000)
        t2.click("[data-a=bs-random]"); t2.click("[data-a=bs-ready]"); s2.click("[data-a=bs-random]"); s2.click("[data-a=bs-ready]"); t2.wait_for_timeout(600)
        t2.click("[data-a=bs-let]"); s2.wait_for_selector(".bs-shots [data-a=bs-fire]"); s2.click(".bs-shots [data-a=bs-fire] >> nth=5"); t2.wait_for_timeout(500)
        pg = s2 if who.startswith("s") else t2
        ov = overflow(pg); vis = pg.evaluate("[...document.querySelectorAll('.bs-side')].filter(e => e.offsetParent).length")
        if name == "phone":
            check(not ov and vis == 1 and pg.locator(".bs-tabs").is_visible(), "phone teacher: one grid at a time with tabs %s" % ov)
            pg.click("[data-a=bs-tab][data-v=fleet]"); check(pg.evaluate("[...document.querySelectorAll('.bs-side')].filter(e => e.offsetParent).map(e => e.className).join()") == "bs-side bs-fleet", "phone: the My fleet tab")
            fire_ok = pg.click("[data-a=bs-tab][data-v=shots]") or pg.locator(".bs-shots [data-a=bs-fire]").count() > 0
            check(fire_ok, "phone: the teacher can fire from the tab")
        else:
            check(not ov and vis == 2, "%s: both grids side by side, nothing scrolls %s" % (name, ov))
        pg.screenshot(path=HERE + "/shots/battleships_%s.png" % name)
        check(not e2, "no page errors (%s) %s" % (name, e2[:3])); c2.close()
    check(not errs, "no page errors %s" % errs[:4])
done()
