"""Typhoon (25 Nov brief, part 1): a grid of hidden boxes. The teacher's screen keeps the boxes; the student's screen
gets a coordinate grid, picks one box when the teacher unlocks it, and never holds an unrevealed box anywhere
(state, DOM, links, class messages). Tally by hand on the master only. Swap roles. Undo. Screen fit."""
import json
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={unpackData:unpackData,studentLinkData:studentLinkData,get UNDO(){return UNDO},get STUDENTS(){return STUDENTS},handle:handle,", 1)
SECRET = ["Q71", "K82", "Z93", "W64", "V55"]                 # box texts that must never reach the student's board
grid3 = [{"t":t, "m":""} for t in ["Q71", "K82", "T", "x2", "Z93", "SWAP", "", "W64", "V55"]]
grid3[4]["m"] = "Free sweet"
games = [
  {"id":"ty1", "type":"typhoon", "title":"Typhoon", "block":"", "options":{"size":3, "grid":grid3, "mix":"", "codes":"★ = Steal 10"}},
  {"id":"ty2", "type":"typhoon", "title":"Against me", "block":"", "options":{"size":3, "grid":grid3, "mix":"", "codes":"", "vsT":True}},
  {"id":"ty6", "type":"typhoon", "title":"Big typhoon", "block":"", "options":{"size":6, "grid":[], "mix":"10×10, 6×20, 3×50, 2×T, 2×x2, 2×SWAP", "codes":""}},
]
pack = {"id":"cl-lp4", "student":"Cathy & Lily", "lp":4, "title":"Cathy & Lily · LP4", "date":"2026-11-25", "updatedAt":"x", "games":games, "liveRoom":"0123456789abcdef0123456789abcdef"}
solo = {"id":"mia-lp2", "student":"Mia", "lp":2, "title":"Mia · LP2", "date":"2026-11-25", "updatedAt":"x", "games":[], "bank":""}
db = seed_db([pack, solo])
def blob(s):
    """Everything the student's page holds: its saved state, the page, the last live message, undo copies.
    (Both pages share one browser here, so only the student page's own storage key is read.)"""
    return s.evaluate("String(localStorage.getItem('lessonGames.student.v1')) + document.documentElement.outerHTML + JSON.stringify(__T.LIVE.last) + JSON.stringify(__T.UNDO)")
def leaks(s, opened=()):
    b = blob(s); return [x for x in SECRET if x in b and x not in opened]
def st(pg, expr="__T.UI.run.st"): return pg.evaluate("JSON.parse(JSON.stringify(%s))" % expr)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, db, errs)
    # ---- 1. editor: fill randomly, shuffle, clear, preset, save
    go_lesson(t, "Mia · LP2"); t.wait_for_timeout(300)
    picker(t); check(t.locator("[data-a=pick-tile][data-k=typhoon]").count() == 1, "the picker offers Typhoon with no word bank"); t.click("[data-a=pick-close]")
    add_game(t, "typhoon"); t.wait_for_selector("#tyEd .ty-in")
    check(t.locator("#tyEd .ty-in").count() == 25, "editor: 5×5 by default (25 boxes)")
    t.fill("#tyMix", "10×10, 6×20, 3×50, 2×T, 2×x2, 2×SWAP"); t.click("#tyFill")
    vals = t.evaluate("[...document.querySelectorAll('#tyEd .ty-in')].map(i => i.value)")
    check(sorted(vals) == sorted(["10"]*10 + ["20"]*6 + ["50"]*3 + ["T"]*2 + ["x2"]*2 + ["SWAP"]*2), "Fill randomly deals the mix (25 boxes)")
    t.click("#tyShuf"); vals2 = t.evaluate("[...document.querySelectorAll('#tyEd .ty-in')].map(i => i.value)")
    check(sorted(vals2) == sorted(vals), "Shuffle keeps the same boxes")
    t.click("input[name=tySize][value='3']"); t.wait_for_timeout(100)
    check(t.locator("#tyEd .ty-in").count() == 9, "3×3 grid")
    t.fill("#tyMix", "4×10, 2×T"); t.click("#tyFill")
    vals3 = t.evaluate("[...document.querySelectorAll('#tyEd .ty-in')].map(i => i.value)")
    check(sorted(vals3) == sorted(["10"]*4 + ["T"]*2 + [""]*3), "leftover boxes stay blank")
    t.click("#tyClear"); check(t.evaluate("[...document.querySelectorAll('#tyEd .ty-in')].every(i => !i.value)"), "Clear empties every box")
    t.fill("#tyEd .ty-in[data-i='0']", "★"); t.fill("#tyMean", "Steal 10 points"); t.fill("#tyEd .ty-in[data-i='4']", "100")
    t.fill("#tyPName", "My usual 3×3"); t.fill("#tyMix", "5×10, 2×T, 1×x2, 1×SWAP"); t.click("#tyPSave"); t.wait_for_timeout(200)
    pre = t.evaluate("__T.STUDENTS['~teacher'] && __T.STUDENTS['~teacher'].tyPresets")
    check(pre and pre[-1]["name"] == "My usual 3×3" and pre[-1]["size"] == 3, "mix saved as a preset (teacher settings): %s" % pre)
    t.click("[data-a=savegame]"); t.wait_for_timeout(300)
    g = [x for x in t.evaluate("__T.PACKS.find(p => p.id === 'mia-lp2').games") if x["type"] == "typhoon"][0]
    check(g["options"]["size"] == 3 and g["options"]["grid"][0] == {"t":"★", "m":"Steal 10 points"} and g["options"]["grid"][4]["t"] == "100", "typed boxes and a box's own meaning are saved")
    # quick game deals the default preset (the first one: My usual 3×3)
    quick(t, "typhoon"); t.wait_for_timeout(400)
    hid = t.evaluate("__T.UI.run.hid.grid.map(b => b.t)")
    check(t.evaluate("__T.UI.run.st.n") == 3 and sorted(hid) == sorted(["10"]*5 + ["T"]*2 + ["x2", "SWAP"]), "Quick game deals the default preset: %s" % hid)
    check(t.locator(".ty-board").count() == 1 and t.locator(".ty-box.m").count() == 0, "one screen, nobody connected: the board shows, boxes face down")
    gtxt = t.evaluate("document.querySelector('.ty-grid').textContent")
    check(all(x not in gtxt for x in ["SWAP", "x2", "T"]) and "10" not in gtxt.replace("1", ""), "board view: the grid shows coordinates only: %s" % gtxt)
    t.click("[data-a=tp-unlock]"); t.click("[data-a=tp-pick][data-c=B2]"); t.wait_for_timeout(200)
    check(t.evaluate("__T.UI.run.st.open.B2 && !__T.UI.run.st.unlocked"), "same screen: Let them pick → one pick → locked again")
    check(t.locator(".ty-rev .ty-rt").count() == 1, "big reveal on the board")
    t.click("[data-a=settings]"); t.click(".setpop [data-a=tp-view]"); t.click(".setpop [data-a=settings]"); t.wait_for_timeout(200)
    check(t.locator(".ty-master .ty-box.m").count() == 9, "Settings → Teacher view shows the boxes")
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(300)
    # ---- 2. live: class link, phone master + iPad board
    t.click("[data-a=home]"); go_lesson(t, "Cathy & Lily · LP4", "Cathy"); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); url = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    s = student(ctx, url, errs); s.wait_for_timeout(900)
    t.click("[data-a=play][data-g=ty1]"); s.wait_for_selector(".ty-board", timeout=6000); t.wait_for_timeout(400)
    check(t.locator(".ty-master").count() == 1 and s.locator(".ty-board").count() == 1, "teacher gets the master, student the board")
    check(st(t)["players"] == [{"name":"Cathy", "score":0}, {"name":"Lily", "score":0}], "pair lesson: one tally line per child")
    check("Answer the question first!" in s.inner_text("main") and s.locator("[data-a=tp-pick]:not([disabled])").count() == 0, "board locked until the teacher unlocks")
    gd = s.evaluate("JSON.stringify(__T.LIVE.last)")
    check('"grid"' not in gd and '"mix"' not in gd and '"codes"' not in gd, "class message: no grid, mix or codes in the game definition")
    check(not leaks(s), "leak: nothing unrevealed on the student's page %s" % leaks(s))
    # tap while locked: a crafted pick from the student's screen is ignored by the master
    s.evaluate("() => { const r = __T.UI.run; r.st.pick = 'A1'; __T.LIVE.sent = ''; }"); s.evaluate("() => { const L = __T.LIVE, r = __T.UI.run; L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:r.gameId, p:r.packId, gen:r.liveGen, t0:r.liveT0, rev:(r.st._rev||0)+1, st:r.st, from:L.me, r:'s' } }); }")
    t.wait_for_timeout(500)
    check(st(t)["open"] == {} and st(s)["open"] == {} and st(s)["pick"] == "", "tap while locked: ignored, and the student's screen is put back")
    # unlock → one pick → auto-lock
    t.click("[data-a=tp-unlock]"); s.wait_for_timeout(400)
    check(s.locator("[data-a=tp-pick]:not([disabled])").count() == 9 and "Pick a box!" in s.inner_text("main"), "unlocked: the student can pick")
    s.click("[data-a=tp-pick][data-c=A1]"); s.wait_for_timeout(700)
    check(st(t)["open"].get("A1", {}).get("t") == "Q71" and st(s)["open"]["A1"]["t"] == "Q71", "the pick opens A1 on both screens")
    check(not st(t)["unlocked"] and not st(s)["unlocked"], "board locks again after one pick")
    check(s.locator(".ty-rev .ty-rt").inner_text() == "Q71", "big reveal on the student's board")
    check(s.locator("[data-a=tp-pick]:not([disabled])").count() == 0, "a second tap does nothing")
    s.evaluate("() => document.querySelector('[data-a=tp-pick][data-c=A2]').disabled = false"); s.click("[data-a=tp-pick][data-c=A2]", force=True); t.wait_for_timeout(500)
    check("A2" not in st(t)["open"], "a forced second tap is ignored by the master")
    check(not leaks(s, ["Q71"]), "leak: after a reveal, only the revealed box %s" % leaks(s, ["Q71"]))
    # bonus meaning shown on reveal (from the teacher's bonus list) and a box's own meaning
    t.click("[data-a=tp-unlock]"); s.wait_for_timeout(300); s.click("[data-a=tp-pick][data-c=A3]"); s.wait_for_timeout(600)
    check(st(s)["open"]["A3"] == {"t":"T", "m":"Typhoon! Lose all your points"}, "a bonus code shows its meaning: %s" % st(s)["open"].get("A3"))
    t.click("[data-a=tp-unlock]"); s.wait_for_timeout(300); s.click("[data-a=tp-pick][data-c=B2]"); s.wait_for_timeout(600)
    check(st(s)["open"]["B2"]["m"] == "Free sweet", "a box's own meaning line")
    # undo the last reveal
    check(t.locator(".toast.undo").count() == 1, "undo toast after a pick")
    t.click("[data-a=settings]"); t.click("[data-a=undo]"); s.wait_for_timeout(600)
    check("B2" not in st(t)["open"] and "B2" not in st(s)["open"], "Settings → Undo takes the last reveal back on both screens")
    # ---- 3. tally: only the master
    check(s.locator("[data-a=spad-open], [data-a=tp-add], [data-a=spad-neg], .spad").count() == 0, "board: scores are read-only (no pad, no quick buttons)")
    t.click("[data-a=tp-add][data-k='0'][data-v='5']"); t.click("[data-a=tp-add][data-k='0'][data-v='5']"); t.click(".ty-p:nth-child(2) [data-a=spad-neg]"); t.click("[data-a=tp-add][data-k='1'][data-v='-5']")
    s.wait_for_timeout(500)
    check([x["score"] for x in st(s)["players"]] == [10, -5], "quick +5 +5, and − 5, on the master show on the board: %s" % st(s)["players"])
    t.click("[data-a=spad-open][data-k='1']"); t.click(".spad [data-a=spad-key][data-v='8']"); t.click(".spad [data-a=spad-key][data-v='5']"); t.click("[data-a=spad-op][data-v=set]"); t.click(".spad-ok"); s.wait_for_timeout(400)
    check(st(s)["players"][1]["score"] == 85, "tap the score: the pad sets an exact number")
    t.click("[data-a=spad-open][data-k='0']"); t.click("[data-a=spad-op][data-v=zero]"); t.click(".spad-ok"); s.wait_for_timeout(400)
    check(st(s)["players"][0]["score"] == 0, "↺ 0 on the pad (Typhoon)")
    t.click("[data-a=tp-turn][data-k='1']"); s.wait_for_timeout(400)
    check(s.locator(".ty-p.now").inner_text().startswith("Lily"), "whose-turn highlight shows on the board")
    s.evaluate("() => { const L = __T.LIVE, r = __T.UI.run, x = JSON.parse(JSON.stringify(r.st)); x.players[0].score = 999; L.chan.send({ type:'broadcast', event:'m', payload:{ t:'st', g:r.gameId, p:r.packId, gen:r.liveGen, t0:r.liveT0, rev:(r.st._rev||0)+5, st:x, from:L.me, r:'s' } }); }")
    t.wait_for_timeout(500)
    check(st(t)["players"][0]["score"] == 0 and st(s)["players"][0]["score"] == 0, "a score sent from the board is ignored")
    t.click("[data-a=tp-pled]"); t.click("[data-a=tp-padd]"); t.wait_for_timeout(100)
    t.fill(".ty-pname[data-k='2']", "Teacher"); t.press(".ty-pname[data-k='2']", "Tab"); t.click("[data-a=tp-pled]"); s.wait_for_timeout(400)
    check([x["name"] for x in st(s)["players"]] == ["Cathy", "Lily", "Teacher"], "add / rename a player")
    # ---- 4. swap roles
    t.click("[data-a=tp-swap]"); s.wait_for_selector(".ty-master", timeout=4000); t.wait_for_timeout(300)
    check(t.locator(".ty-board").count() == 1 and s.locator(".ty-master .ty-box.m").count() == 9, "swap: the student gets the master, the teacher the board")
    check("Z93" in s.inner_text("main"), "swapped: the student's master shows the boxes")
    s.click("[data-a=tp-unlock]"); t.wait_for_timeout(500)
    check(st(t)["unlocked"], "the student-teacher unlocks the teacher's board")
    t.click("[data-a=tp-pick][data-c=C2]"); s.wait_for_timeout(600)
    check(st(s)["open"]["C2"]["t"] == "W64" and not st(s)["unlocked"], "the teacher picks C2 on the board")
    s.click("[data-a=tp-add][data-k='2'][data-v='5']"); t.wait_for_timeout(500)
    check(st(t)["players"][2]["score"] == 5, "the student-teacher's tally reaches the teacher")
    check(s.locator("[data-a=tp-swap]").count() == 0, "only the teacher can end a swap")
    t.click("[data-a=tp-swap]"); s.wait_for_selector(".ty-board", timeout=4000); s.wait_for_timeout(300)
    check("grid" not in st(s) and not leaks(s, ["Q71", "W64"]), "swap back: the grid is gone from the student's state %s" % leaks(s, ["Q71", "W64"]))
    # ---- 5. saving: Phase B line
    t.click("[data-a=finish-ask]"); check(t.locator("[data-a=fl-later]").count() == 1, "Finish choices include Finish later")
    t.click("[data-a=finish]"); t.wait_for_timeout(500)
    r = [x for x in t.evaluate("__T.RESULTS") if x["gameId"] == "ty1"][0]
    check(r["summary"].startswith("Typhoon 3×3: 3 picks (Cathy 0, Lily 85, Teacher 5)"), "Phase B line: %s" % r["summary"])
    check("Opened: A1 Q71, A3 T, C2 W64" in r["summary"] and r["items"] == [] and r["points"] == 0, "opened boxes in order; no items, no lesson points")
    # ---- 6. per-game link: the student starts; nothing secret in the link
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    menu_click(t, "[data-a=slink][data-g=ty1]"); t.wait_for_selector("#slinkUrl", timeout=5000); surl = t.input_value("#slinkUrl"); t.click("[data-a=slink-close]")
    d = t.evaluate("u => __T.unpackData(u.split('#s=')[1])", surl)
    check(not [x for x in SECRET if x in json.dumps(d)] and "grid" not in d["g"]["options"] and d["g"]["options"]["size"] == 3, "per-game link: size and legend only %s" % d["g"]["options"])
    s.close(); s2 = student(ctx, surl, errs); s2.wait_for_timeout(800); s2.click("[data-a=s-start]")
    try: t.wait_for_function("__T.UI.view === 'play' && !!document.querySelector('.ty-master')", timeout=5000)
    except Exception: pass
    check(t.evaluate("__T.UI.view") == "play" and t.locator(".ty-master").count() == 1, "the teacher's app joins the student's game")
    t.click("[data-a=tp-unlock]"); s2.wait_for_timeout(500); s2.click("[data-a=tp-pick][data-c=C3]"); s2.wait_for_timeout(700)
    check(st(s2)["open"].get("C3", {}).get("t") == "V55", "per-game link: pick works")
    check(not leaks(s2, ["V55", "Q71", "W64"]), "per-game link: nothing unrevealed on the student's page %s" % leaks(s2, ["V55", "Q71", "W64"]))   # Q71, W64: opened in the earlier game (same browser here)
    t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400); s2.close()
    # ---- 6b. against the teacher: on the teacher's turn, a random box or the student picks for the teacher
    menu_click(t, "[data-a=editgame][data-g=ty2]"); t.wait_for_selector("#tyVsT")
    check(t.is_checked("#tyVsT"), "editor: Teacher plays too"); t.click("[data-a=cancelgame]"); t.wait_for_timeout(300)
    s4 = student(ctx, url, errs); s4.wait_for_timeout(800)
    t.click("[data-a=play][data-g=ty2]"); s4.wait_for_selector(".ty-board", timeout=6000); t.wait_for_timeout(300)
    check([x["name"] for x in st(t)["players"]] == ["Cathy", "Lily", "Teacher"], "Teacher plays too: a Teacher line in the tally")
    t.click("[data-a=tp-turn][data-k='1']"); t.click("[data-a=tp-unlock]"); s4.wait_for_timeout(300); s4.click("[data-a=tp-pick][data-c=A1]"); s4.wait_for_timeout(600)
    check(st(t)["turn"] == 2 and st(t)["log"][-1].get("w") == "Lily", "after Lily's pick the turn moves on to Teacher")
    check(t.locator("main [data-a=tp-rand]").count() == 1 and "Let them pick for me" in t.inner_text("main"), "teacher's turn: Random box for me · Let them pick for me")
    s4.wait_for_timeout(300); check("Teacher’s turn" in s4.inner_text("main"), "the board says it's the teacher's turn")
    t.click("main [data-a=tp-rand]"); s4.wait_for_timeout(600)
    lt = st(t)["log"][-1]
    check(len(st(t)["open"]) == 2 and lt.get("w") == "Teacher" and lt["c"] != "A1" and st(s4)["open"].get(lt["c"]), "random box: an unopened box opens for the teacher, on both screens (%s)" % lt)
    check(st(t)["turn"] == 0 and not st(t)["unlocked"], "then it's Cathy's turn, board locked")
    check(("Teacher opened " + lt["c"]) in t.inner_text("main"), "master: who opened what")
    t.click("[data-a=tp-turn][data-k='2']"); t.click("main [data-a=tp-unlock]"); s4.wait_for_timeout(400)
    check("Pick a box for Teacher!" in s4.inner_text("main"), "Let them pick for me: the student picks for the teacher")
    free = [c for c in ["A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"] if c not in st(s4)["open"]][0]
    s4.click("[data-a=tp-pick][data-c=%s]" % free); s4.wait_for_timeout(600)
    check(st(t)["log"][-1] == dict(st(t)["log"][-1], c=free, w="Teacher") and "· Teacher" in s4.locator(".ty-rc").inner_text(), "the student's pick counts as the teacher's box")
    opened = [x["t"] for x in st(t)["log"]]
    check(not leaks(s4, opened + ["Q71", "W64", "V55"]), "leak: still nothing unrevealed on the student's page")
    t.click("[data-a=finish-ask]"); t.click("[data-a=finish]"); t.wait_for_timeout(500)
    r = [x for x in t.evaluate("__T.RESULTS") if x["gameId"] == "ty2"][0]
    check("(Teacher)" in r["summary"] and "A1 Q71 (Lily)" in r["summary"], "Phase B line names whose box it was: %s" % r["summary"])
    t.click("[data-a=backlesson]"); t.wait_for_timeout(300); s4.close()
    # ---- 7. screen fit: iPad board 3×3 and 6×6, phone master
    for gid in ("ty1", "ty6"):
        s3 = student(ctx, url, errs); s3.wait_for_timeout(700)
        t.click("[data-a=play][data-g=%s]" % gid); s3.wait_for_selector(".ty-board", timeout=6000); s3.wait_for_timeout(500)
        for k in range(3): s3.evaluate("() => { const o = document.querySelector('.ty-rev'); if(o) o.click(); }")
        t.click("[data-a=tp-unlock]"); s3.wait_for_timeout(300); s3.click(".ty-box.shut >> nth=0"); s3.wait_for_timeout(3200)
        ov = overflow(s3); check(not ov, "iPad board %s fits without scrolling %s" % (gid, ov)); s3.screenshot(path=HERE + "/shots/typhoon_board_%s.png" % gid)
        t.click("[data-a=finish-ask]"); t.click("[data-a=discard]"); t.wait_for_timeout(400); s3.close()
    ph = b.new_context(viewport={"width":390, "height":844}, has_touch=True); pe = []
    tp = teacher(ph, seed_db([pack]), pe); go_lesson(tp, "Cathy & Lily · LP4", "Cathy"); tp.wait_for_timeout(300)
    tp.click("[data-a=play][data-g=ty6]"); tp.wait_for_timeout(400)
    tp.click("[data-a=settings]"); tp.click(".setpop [data-a=tp-view]"); tp.click(".setpop [data-a=settings]"); tp.wait_for_timeout(400)
    zoom = tp.evaluate("parseFloat(document.querySelector('main.stage').style.zoom || '1')")
    w = tp.evaluate("document.querySelector('.ty-box.m').getBoundingClientRect().width") * zoom
    check(tp.locator(".ty-master").count() == 1 and w >= 40 and not overflow(tp), "phone master 6×6 fits, boxes readable (%dpx, zoom %.2f) %s" % (w, zoom, overflow(tp)))
    ub = tp.locator("[data-a=tp-unlock]").bounding_box(); check(ub and ub["width"] >= 220 and ub["height"] >= 54, "phone: big Let them pick button %s" % ub)
    tp.screenshot(path=HERE + "/shots/typhoon_phone_master.png")
    check(not errs and not pe, "no page errors %s" % (errs + pe)[:4])
done()
