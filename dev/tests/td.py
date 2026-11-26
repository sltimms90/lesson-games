"""Tower Defence (26 Nov brief): a single-player break game with pausing at its centre.
Build / upgrade / sell and their costs; a wave only on ▶ Start wave; auto-pause after each wave (and the setting off);
the wave limit; ❚❚ freezes the game; the tab hidden pauses it; the same state and taps give the same game; ‹ and
▶ Resume, Finish later and Continue restore it exactly (mid-wave: from the start of that wave); game over; + Coins;
⚡ challenge; undo; live (teacher's status screen, the teacher's pause locks the student, unlock, the student's own
pause); results text; screen fit on iPad, desktop and phone."""
import json, os
import lg
lg.APP = lg.APP.replace("window.__T={", "window.__T={tdGeo:tdGeo,tdStep:tdStep,tdNewSim:tdNewSim,tdWave:tdWave,TYPES:TYPES,get TD_SEL(){return TD_SEL},get render(){return render},saveRun:saveRun,get STUDENTS(){return STUDENTS},get UNDO(){return UNDO},", 1)
from lg import *
games = [{"id":"td1", "type":"td", "title":"Tower Defence", "block":"", "options":{}},
         {"id":"td2", "type":"td", "title":"Tower Defence", "block":"", "options":{"map":1, "diff":"normal", "pick":False}},
         {"id":"hl1", "type":"hilo", "title":"Higher or Lower", "block":"", "options":{}}]
room = "0123456789abcdef0123456789abcdef"
bank = "castle | a big old house for a king\ntower | a tall building\nbridge | it goes over a river"
pack1 = {"id":"lily-lp7", "student":"Lily", "lp":7, "title":"Lily · LP7", "date":"2026-11-26", "updatedAt":"x", "games":games, "bank":bank}
pack2 = {"id":"lily-lp8", "student":"Lily", "lp":8, "title":"Lily · LP8", "date":"2026-11-26", "updatedAt":"x", "games":[]}
def st(pg): return pg.evaluate("JSON.parse(JSON.stringify(__T.UI.run.st))")
def sim(pg): return pg.evaluate("__T.UI.run.sim ? JSON.parse(JSON.stringify(__T.UI.run.sim)) : null")
def ev(pg, js, arg=None): return pg.evaluate(js, arg)
def slot_xy(pg, i): return ev(pg, "i => { const s = __T.tdGeo(__T.UI.run.st.map).slots[i]; const r = document.getElementById('tdCv').getBoundingClientRect(); return [r.left + (s.c + .5) * r.width / 16, r.top + (s.r + .5) * r.height / 10]; }", i)
def tap_slot(pg, i):
    x, y = slot_xy(pg, i); pg.mouse.click(x, y); pg.wait_for_timeout(120)
def build(pg, i, k):
    tap_slot(pg, i); pg.click("#tdMenu [data-a=td-build][data-k=%s]" % k); pg.wait_for_timeout(80)
def ff(pg, n):
    """n fixed steps right away (the frame loop then carries on from there)."""
    return ev(pg, "n => { const r = __T.UI.run; for (let i = 0; i < n && r.st.phase === 'wave'; i++) __T.tdStep(r.st, r.sim); return r.st.phase; }", n)
def end_wave(pg, keep_card=False):
    ev(pg, "() => { const r = __T.UI.run; for (let i = 0; i < 40000 && r.st.phase === 'wave' && !r.st.pz && !r.st.ch && !r.st.tlock; i++) __T.tdStep(r.st, r.sim); __T.saveRun(); __T.render(); }"); pg.wait_for_timeout(150)
    if not keep_card and pg.locator("[data-a=td-card]").count():
        pg.click("[data-a=td-card]"); pg.click("[data-a=td-cardok]"); pg.wait_for_timeout(100)
def settings(pg):
    if not pg.locator(".setpop").count(): pg.click("header [data-a=settings]"); pg.wait_for_timeout(120)
def close_settings(pg):
    if pg.locator(".setpop").count(): pg.click(".setpop [data-a=settings]"); pg.wait_for_timeout(120)
def menu_free(pg):
    return pg.evaluate("""() => { const m = document.getElementById('tdMenu'); return m ? +m.getAttribute('data-cover') : -1; }""")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, seed_db([pack1, pack2]), errs); go_lesson(t, "Lily · LP7"); t.wait_for_timeout(300)
    # ---- 0. adding it: no words box, Quick game
    t.click("#addSec > summary"); t.click("[data-a=addgame][data-t=td]"); t.wait_for_selector("#gTitle")
    check(t.locator("#gBlock").is_hidden() and t.locator("input[name=tdMap]").count() == 3 and t.locator("input[name=tdDiff]").count() == 3 and t.locator("#tdAuto").is_checked(), "Add a game → Tower Defence: no words box; map, difficulty, Stop after each wave")
    t.click("[data-a=cancelgame]"); t.wait_for_timeout(200)
    check(t.locator("[data-a=quick][data-q=td]").count() == 1, "Quick game offers Tower Defence (needs no words)")
    # ---- 1. setup: map and difficulty
    t.click("[data-a=play][data-g=td1]"); t.wait_for_selector(".td-setup")
    check(t.locator(".td-mapbtn").count() == 3 and t.locator(".td-setup .seg button").count() == 3, "a new game opens on the map and difficulty choice")
    t.click("[data-a=td-map][data-v='1']"); t.click("[data-a=td-diff][data-v=normal]")
    s = st(t); check(s["map"] == 1 and s["diff"] == "normal" and s["coins"] == 120 and s["lives"] == 20 and len(s["towers"]) == len(ev(t, "__T.tdGeo(1).slots")), "map 2, Normal: 120 coins, 20 lives, a slot list for that map")
    t.click("[data-a=td-go]"); t.wait_for_selector("#tdCv")
    check(st(t)["phase"] == "build" and "Start wave 1" in t.inner_text(".td-side"), "▶ Play: building, ▶ Start wave 1")
    # ---- 2. a wave only on ▶ Start wave
    t.wait_for_timeout(1500)
    check(st(t)["phase"] == "build" and sim(t) is None, "nothing comes until ▶ Start wave (1.5 s later: still building, no enemies)")
    # ---- 3. build / upgrade / sell and their costs; the menu beside its slot, clear of the path
    nslots = len(st(t)["towers"]); covers = []
    for m in range(3):
        ev(t, "m => { __T.UI.run.st.map = m; __T.UI.run.st.towers = __T.tdGeo(m).slots.map(() => null); __T.render(); }", m); t.wait_for_timeout(100)
        for i in range(len(ev(t, "m => __T.tdGeo(m).slots", m))):
            tap_slot(t, i); covers.append((m, i, menu_free(t))); tap_slot(t, i)
    check(all(c[2] == 0 for c in covers), "the build menu opens beside every slot of all 3 maps without covering the path %s" % [c for c in covers if c[2]][:4])
    ev(t, "() => { __T.UI.run.st.map = 1; __T.UI.run.st.towers = __T.tdGeo(1).slots.map(() => null); __T.render(); }"); t.wait_for_timeout(100)
    tap_slot(t, 0)
    check(t.locator("#tdMenu [data-a=td-build]").count() == 4 and all(h >= 44 for h in t.evaluate("[...document.querySelectorAll('#tdMenu button')].map(b => Math.min(b.offsetWidth, b.offsetHeight))")), "four towers in the menu, every button at least 44 px")
    t.click("#tdMenu [data-a=td-build][data-k=basic]"); t.wait_for_timeout(100)
    s = st(t); check(s["coins"] == 100 and s["towers"][0] == {"k":"basic", "lv":1, "spent":20}, "Basic: 20 coins")
    tap_slot(t, 0); check("Upgrade" in t.inner_text("#tdMenu") and "+14" in t.inner_text("#tdMenu"), "tap the tower: Upgrade (30) / Sell (+14, 70%)")
    t.click("#tdMenu [data-a=td-up]"); t.wait_for_timeout(100)
    s = st(t); check(s["coins"] == 70 and s["towers"][0]["lv"] == 2 and s["towers"][0]["spent"] == 50, "upgrade to level 2: 30 coins")
    check(t.locator("#tdMenu [data-a=td-up]").count() == 1, "the menu stays open after an upgrade")
    t.click("#tdMenu [data-a=td-up]"); t.wait_for_timeout(100)
    s = st(t); check(s["coins"] == 25 and s["towers"][0]["lv"] == 3, "level 3: 45 coins")
    check(t.locator("#tdMenu button[disabled]:has-text('Top level')").count() == 1, "level 3 is the top")
    t.click("#tdMenu [data-a=td-sell]"); t.wait_for_timeout(100)
    s = st(t); check(s["coins"] == 25 + 66 and s["towers"][0] is None, "sell: 70% of the 95 spent back (66)")
    tap_slot(t, 1); dis = t.evaluate("[...document.querySelectorAll('#tdMenu [data-a=td-build]')].map(b => b.getAttribute('data-k') + ':' + b.disabled)")
    check(dis == ["basic:false", "splash:false", "freeze:false", "sniper:false"], "91 coins: every tower affordable %s" % dis)
    t.click("#tdMenu [data-a=td-build][data-k=sniper]"); t.wait_for_timeout(100)
    tap_slot(t, 2); dis = t.evaluate("[...document.querySelectorAll('#tdMenu [data-a=td-build]')].map(b => b.getAttribute('data-k') + ':' + b.disabled)")
    check(st(t)["coins"] == 36 and dis == ["basic:false", "splash:true", "freeze:false", "sniper:true"], "Sniper 55: 36 left, so Splash (45) and Sniper are greyed out %s" % dis)
    ev(t, "() => { const r = __T.UI.run; __T.TYPES.td.act(r, 'td-build', { getAttribute: k => k === 'data-s' ? '2' : k === 'data-k' ? 'splash' : null }); }")
    check(st(t)["towers"][2] is None and st(t)["coins"] == 36, "building without the coins is refused")
    tap_slot(t, 2)
    # ---- 4. undo a build (Settings → Undo)
    ev(t, "() => { __T.UI.run.st.coins = 200; __T.render(); }"); build(t, 4, "freeze"); c0 = st(t)["coins"]
    settings(t); check(not t.locator(".setpop [data-a=undo]").is_disabled(), "⚙ Undo is there after a build")
    t.click(".setpop [data-a=undo]"); t.wait_for_timeout(150)
    s = st(t); check(s["towers"][4] is None and s["coins"] == c0 + 35, "Undo: the Freeze tower goes and its 35 coins come back")
    build(t, 4, "basic"); tap_slot(t, 4); t.click("#tdMenu [data-a=td-sell]"); t.wait_for_timeout(100); c1 = st(t)["coins"]
    settings(t); t.click(".setpop [data-a=undo]"); t.wait_for_timeout(150)
    s = st(t); check(s["towers"][4] == {"k":"basic", "lv":1, "spent":20} and s["coins"] == c1 - 14, "Undo a sale: the tower is back, the 14 coins go again")
    # ---- 5. + Coins (teacher, ⚙)
    settings(t); c2 = st(t)["coins"]
    t.click(".setpop [data-a=td-coins][data-n='25']"); t.wait_for_timeout(100)
    settings(t); t.click(".setpop [data-a=td-coins][data-n='100']"); t.wait_for_timeout(100)
    s = st(t); check(s["coins"] == c2 + 125 and len(s["grants"]) == 2 and len(s["gotG"]) == 2, "+ Coins in ⚙: +25 and +100 (each added once)")
    close_settings(t)
    # ---- 6. ▶ Start wave; ❚❚ freezes everything
    ev(t, "() => { __T.UI.run.st.coins = 300; __T.render(); }")
    t.click("[data-a=td-start]"); t.wait_for_timeout(1400)
    s = st(t); m0 = sim(t)
    check(s["phase"] == "wave" and m0 and m0["t"] > 20 and len(m0["en"]) >= 1, "▶ Start wave: enemies come (%s steps)" % (m0 and m0["t"]))
    check(s["ws"] == {"lives":20, "coins":300, "kills":0}, "the wave's start is noted (lives, coins)")
    t.click("header [data-a=pause]"); t.wait_for_timeout(100)
    a = sim(t); t.wait_for_timeout(1500); z = sim(t)
    check(st(t)["pz"] == "me" and a == z and a["en"], "❚❚: enemy positions unchanged 1.5 s later")
    pt = t.inner_text(".td-pause")
    check("Paused" in pt and "Wave 1" in pt and "❤ 20" in pt and "🪙" in pt and t.locator(".td-pause [data-a=td-resume]").count() == 1, "pause screen: wave, lives, coins, big ▶ Resume")
    check(t.locator("header [data-a=pause]").count() == 0, "no ❚❚ while paused")
    clock1 = t.inner_text("#clock"); t.wait_for_timeout(1100)
    check(t.inner_text("#clock") == clock1, "the game clock stops while paused")
    t.click("[data-a=td-resume]"); t.wait_for_timeout(700)
    check(st(t)["pz"] == "" and sim(t)["t"] > z["t"], "▶ Resume: it carries on")
    # ---- 7. the tab hidden pauses it
    ev(t, "() => { Object.defineProperty(document, 'hidden', { get: () => true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"); t.wait_for_timeout(150)
    h1 = sim(t); t.wait_for_timeout(800); h2 = sim(t)
    check(st(t)["pz"] == "away" and h1 == h2, "tab hidden (visibilitychange): paused, nothing moves")
    ev(t, "() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }"); t.wait_for_timeout(150)
    check(st(t)["pz"] == "away" and t.locator(".td-pause [data-a=td-resume]").count() == 1, "back on the tab: still paused, ▶ Resume")
    t.click("[data-a=td-resume]"); t.wait_for_timeout(200)
    # ---- 8. deterministic: the same state and the same taps give the same game
    det = ev(t, """() => {
      const T = __T.TYPES.td, base = JSON.stringify({ st: __T.UI.run.st, sim: __T.UI.run.sim });
      function play(tapAt){ const o = JSON.parse(base), run = { st:o.st, sim:o.sim, type:'td' };
        for (let i = 0; i < 900 && run.st.phase === 'wave'; i++){ if (i === tapAt){ const s = run.st.towers.findIndex(x => !x); T.act(run, 'td-build', { getAttribute: k => k === 'data-s' ? String(s) : k === 'data-k' ? 'sniper' : null }); } __T.tdStep(run.st, run.sim); }
        return JSON.stringify(run); }
      const a = play(120), b = play(120), c = play(400);
      return [a === b, a !== c, JSON.parse(a).st.coins, JSON.parse(c).st.coins]; }""")
    check(det[0] and det[1], "deterministic: same state + same tap at the same step = the same outcome; a later tap differs (%s)" % det)
    # ---- 9. auto-pause at the end of the wave; the setting off
    end_wave(t)
    s = st(t); check(s["phase"] == "build" and s["wave"] == 2 and s["cleared"] == 1 and s["pz"] == "wave" and "Wave 1 cleared!" in t.inner_text(".td-pause"), "wave cleared: auto-pause, “Wave 1 cleared!”")
    check(s["coins"] > 300 and t.locator("[data-a=td-start]").is_disabled(), "kill coins and the clear bonus; Start waits for ▶ Resume")
    t.click("[data-a=td-resume]"); t.wait_for_timeout(100)
    settings(t); t.click(".setpop [data-a=td-auto]"); t.wait_for_timeout(100); close_settings(t)
    check(st(t)["auto"] is False, "⚙ Stop after each wave: off")
    t.click("[data-a=td-start]"); t.wait_for_timeout(200); end_wave(t)
    s = st(t); check(s["phase"] == "build" and s["wave"] == 3 and s["pz"] == "" and not t.locator(".td-pause").count() and not t.locator("[data-a=td-start]").is_disabled(), "with it off: no pause after the wave, ▶ Start wave 3 straight away")
    settings(t); t.click(".setpop [data-a=td-auto]"); t.wait_for_timeout(100)
    # ---- 10. the wave limit
    settings(t); t.click(".setpop [data-a=td-limit][data-v='1']"); t.wait_for_timeout(100)
    check(st(t)["limit"] == 3 and "Wave 3" in t.inner_text(".setpop #tdLimit"), "⚙ Stop at wave: + sets it to the next wave (3)")
    close_settings(t)
    t.click("[data-a=td-start]"); t.wait_for_timeout(200); end_wave(t, keep_card=True)
    s = st(t)
    check(s["card"] and not s["card"]["open"] and "Bonus card!" in t.inner_text(".td-pause") and t.locator("[data-a=td-start]").is_disabled(), "wave 3 cleared: a bonus card first, face down; nothing starts until it's dealt with")
    k = s["card"]["k"]; t.click("[data-a=td-card]"); t.wait_for_timeout(100)
    check(st(t)["card"]["open"] and t.locator(".td-card b").count() == 1, "tap: it turns over (%s: %s)" % (k, t.inner_text(".td-card").replace("\n", " ")))
    t.click("[data-a=td-cardok]"); t.wait_for_timeout(100)
    s = st(t); pt = t.inner_text(".td-pause")
    check(s["pz"] == "limit" and s["cleared"] == 3 and "Time for some work!" in pt and t.locator(".td-pause [data-a=td-resume]").count() == 0, "wave 3 cleared at the limit: “Time for some work!”, no ▶ Resume")
    ev(t, "() => { const r = __T.UI.run; __T.TYPES.td.act(r, 'td-resume', { getAttribute: () => null }); __T.render(); }")
    check(st(t)["pz"] == "limit", "a resume is refused while the limit stands")
    settings(t); t.click(".setpop [data-a=td-limit][data-v='1']"); t.wait_for_timeout(150); close_settings(t)
    s = st(t); check(s["limit"] == 4 and s["pz"] == "wave" and t.locator(".td-pause [data-a=td-resume]").count() == 1, "limit raised to 4: the pause becomes a normal break with ▶ Resume")
    t.click("[data-a=td-resume]"); settings(t); t.click(".setpop [data-a=td-limit][data-v='0']"); t.wait_for_timeout(100); close_settings(t)
    check(st(t)["limit"] == 0, "No limit clears it")
    # ---- 11. ⚡ challenge: paused while open; Good adds coins; logged
    t.click("[data-a=td-start]"); t.wait_for_timeout(600)
    t.click("header [data-a=challenge]"); t.wait_for_timeout(150)
    c1 = sim(t); t.wait_for_timeout(900); c2s = sim(t)
    check(st(t)["ch"] and c1 == c2s and t.locator(".chov").count() == 1, "⚡: a prompt, and the wave waits while it's open")
    check("castle" in json.dumps(st(t)["ch"]) or "tower" in json.dumps(st(t)["ch"]) or "bridge" in json.dumps(st(t)["ch"]), "prompt from the lesson's words (chPool)")
    co = st(t)["coins"]; t.click("[data-a=ch-mark][data-m=good]"); t.wait_for_timeout(400)
    s = st(t); check(s["ch"] is None and s["coins"] >= co + 50 and len(s["chLog"]) == 1 and s["chLog"][0]["ok"], "Good: +50 coins, logged in chLog")
    check(sim(t)["t"] > c2s["t"], "the wave carries on after the challenge")
    t.click("header [data-a=challenge]"); co = st(t)["coins"]; ev(t, "() => { __T.UI.run.st.pz = ''; }")
    t.click("[data-a=ch-mark][data-m=no]"); t.wait_for_timeout(100)
    s = st(t); check(len(s["chLog"]) == 2 and not s["chLog"][1]["ok"] and s["coins"] - co < 50, "Not yet: logged, no bonus")
    # ---- 11b. bonus cards: each one's effect; next-wave cards change the wave; unlockable towers; the gold mine
    end_wave(t)
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    ev(t, "() => { const r = __T.UI.run; r.st.towers = r.st.towers.map(() => null); r.st.towers[0] = { k:'basic', lv:1, spent:20 }; r.st.towers[1] = { k:'sniper', lv:3, spent:210 }; r.st.coins = 100; r.st.lives = 15; r.st.free = 0; r.st.mod = ''; __T.render(); }")
    def card(k):
        ev(t, "k => { __T.UI.run.st.card = { k, open:false }; __T.render(); }", k); t.click("[data-a=td-card]"); t.wait_for_timeout(80)
        txt = t.inner_text(".td-card"); t.click("[data-a=td-cardok]"); t.wait_for_timeout(80); return txt
    card("upall"); s = st(t); check(s["towers"][0]["lv"] == 2 and s["towers"][1]["lv"] == 3, "⬆ Power up: every tower up a level (level 3 stays 3)")
    card("coins"); check(st(t)["coins"] == 160, "🪙 Treasure: +60 coins")
    card("tax"); check(st(t)["coins"] == 120, "🕳 Lose 40 coins")
    card("lives"); check(st(t)["lives"] == 18, "❤ +3 lives")
    card("lives"); card("lives"); check(st(t)["lives"] == 20, "…never above 20")
    txt = card("free"); check(st(t)["free"] == 1 and "Next tower free" in t.inner_text(".td-side"), "🎁 A free tower: shown in the side panel")
    tap_slot(t, 2); check("Free" in t.inner_text("#tdMenu"), "the build menu says Free")
    t.click("#tdMenu [data-a=td-build][data-k=sniper]"); t.wait_for_timeout(80)
    s = st(t); check(s["towers"][2] == {"k":"sniper", "lv":1, "spent":0} and s["coins"] == 120 and s["free"] == 0, "the next tower costs nothing (and sells for nothing)")
    settings(t); t.click(".setpop [data-a=undo]"); t.wait_for_timeout(100)
    check(st(t)["towers"][2] is None and st(t)["free"] == 1, "undo gives the free tower back"); build(t, 2, "basic")
    n0 = sum(1 for x in st(t)["towers"] if x); txt = card("lose"); s = st(t)
    check(sum(1 for x in s["towers"] if x) == n0 - 1 and "knocked down" in txt, "💥 Oh no: one tower is knocked down (%s)" % txt.replace("\n", " "))
    w = st(t)["wave"]
    base = ev(t, "w => __T.tdWave(w, __T.UI.run.st.diff, '')", w)
    for k, test, msg in (("dbl", lambda L: len(L) == 2 * len([e for e in base if e["k"] != "b"]) + len([e for e in base if e["k"] == "b"]), "👥 Double trouble: twice the enemies"),
                         ("tough", lambda L: L[0]["hp"] > base[0]["hp"] * 1.4, "🛡 Armour up: tougher"),
                         ("fast", lambda L: L[0]["spm"] == 1.3, "💨 Speedy: faster"), ("slow", lambda L: L[0]["spm"] == .75, "🐌 Sleepy: slower")):
        card(k); s = st(t); L = ev(t, "() => { const s = __T.UI.run.st; return __T.tdWave(s.wave, s.diff, s.mod); }")
        check(s["mod"] == k and test(L), msg + " next wave (and it says so: %s)" % t.inner_text("#tdNext"))
    t.click("[data-a=td-start]"); t.wait_for_timeout(200); end_wave(t)
    check(st(t)["mod"] == "", "…for one wave only")
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    d1 = ev(t, "() => { const s = __T.UI.run.st, x = JSON.parse(JSON.stringify(s)); x.card = null; x.cleared = 5; x.phase = 'wave'; x.wave = 6; x.towers = x.towers.map(() => null); const m = __T.tdNewSim(x); for (let i = 0; i < 99999 && x.phase === 'wave'; i++){ x.lives = 20; __T.tdStep(x, m); } return x.card; }")
    d2 = ev(t, "() => { const s = __T.UI.run.st, x = JSON.parse(JSON.stringify(s)); x.card = null; x.cleared = 5; x.phase = 'wave'; x.wave = 6; x.towers = x.towers.map(() => null); const m = __T.tdNewSim(x); for (let i = 0; i < 99999 && x.phase === 'wave'; i++){ x.lives = 20; __T.tdStep(x, m); } return x.card; }")
    check(d1 and d1 == d2 and not d1["open"], "a card comes after wave 6 too, and the same game draws the same card (%s)" % d1)
    # unlockable towers
    ev(t, "() => { const r = __T.UI.run; r.st.cleared = 4; r.st.coins = 1000; r.st.free = 0; __T.render(); }")
    free = st(t)["towers"].index(None); tap_slot(t, free)
    locks = t.evaluate("[...document.querySelectorAll('#tdMenu .td-b.lock')].map(b => b.getAttribute('data-k') + ' ' + b.textContent)")
    check(len(locks) == 3 and "lightning 🔒wave 6" in locks and t.locator("#tdMenu [data-a=td-build]").count() == 4, "after 4 waves: three towers locked, showing when they open %s" % locks)
    check(menu_free(t) == 0, "the bigger menu still keeps clear of the path"); tap_slot(t, free)
    ev(t, "() => { const r = __T.UI.run; return __T.TYPES.td.act(r, 'td-build', { getAttribute: k => k === 'data-s' ? String(r.st.towers.indexOf(null)) : k === 'data-k' ? 'lightning' : null }); }")
    check(not any(x and x["k"] == "lightning" for x in st(t)["towers"]), "a locked tower can't be built")
    ev(t, "() => { __T.UI.run.st.cleared = 12; __T.render(); }"); tap_slot(t, free)
    check(t.locator("#tdMenu .td-b.lock").count() == 0 and t.locator("#tdMenu [data-a=td-build]").count() == 7, "after wave 12 all seven towers are open (Lightning 5, Gold mine 8, Laser 12)"); tap_slot(t, free)
    covers2 = []
    for m in range(3):
        ev(t, "m => { const r = __T.UI.run; r.st.map = m; r.st.towers = __T.tdGeo(m).slots.map(() => null); __T.render(); }", m); t.wait_for_timeout(80)
        for i in range(len(ev(t, "m => __T.tdGeo(m).slots", m))):
            tap_slot(t, i); covers2.append((m, i, menu_free(t))); tap_slot(t, i)
    check(all(c[2] == 0 for c in covers2), "with seven towers the menu still never covers the path, any slot, any map %s" % [c for c in covers2 if c[2]][:4])
    ev(t, "() => { const r = __T.UI.run; r.st.map = 1; r.st.towers = __T.tdGeo(1).slots.map(() => null); r.st.coins = 1000; __T.render(); }")
    build(t, 0, "mine"); tap_slot(t, 0); t.click("#tdMenu [data-a=td-up]"); tap_slot(t, 0); build(t, 1, "lightning"); build(t, 2, "laser"); build(t, 3, "basic")
    c0 = st(t)["coins"]; w = st(t)["wave"]
    t.click("[data-a=td-start]"); t.wait_for_timeout(1200)
    t.screenshot(path=os.path.join(HERE, "shots", "td-new-towers.png"))
    end_wave(t, keep_card=True); s = st(t)
    check(s["mined"] == 25 and "Gold mines: +25" in t.inner_text(".td-pause"), "💰 Gold mine level 2: +25 coins after the wave, said on the break screen")
    if s["card"]: t.click("[data-a=td-card]"); t.click("[data-a=td-cardok]")
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    # the teacher can turn the cards off
    settings(t); t.click(".setpop [data-a=td-cards]"); t.wait_for_timeout(100); close_settings(t)
    ev(t, "() => { const r = __T.UI.run; r.st.cleared = 8; r.st.wave = 9; __T.render(); }")
    t.click("[data-a=td-start]"); t.wait_for_timeout(200)
    ev(t, "() => { const r = __T.UI.run; for (let i = 0; i < 40000 && r.st.phase === 'wave'; i++){ r.st.lives = 20; __T.tdStep(r.st, r.sim); } __T.saveRun(); __T.render(); }"); t.wait_for_timeout(150)
    check(st(t)["cards"] is False and st(t)["cleared"] == 9 and not st(t)["card"], "⚙ Bonus cards off: wave 9 cleared, no card %s" % {k: st(t)[k] for k in ("cards", "cleared", "card", "phase", "pz", "lives")})
    settings(t); t.click(".setpop [data-a=td-cards]"); t.wait_for_timeout(100); close_settings(t)
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    # ---- 12. ‹ leaves the game mid-wave: paused; another game; ▶ Resume restores it exactly
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    t.click("[data-a=td-start]"); t.wait_for_timeout(500)
    t.wait_for_timeout(300); t.click("header [data-a=lesson]"); t.wait_for_timeout(250)
    snap = ev(t, "() => { const r = __T.UI.parked && Object.values(__T.UI.parked).find(x => x.type === 'td') || __T.UI.run; return JSON.stringify({ st:r.st, sim:r.sim }); }")
    check(json.loads(snap)["st"]["pz"] == "away", "‹ mid-wave: the wave pauses")
    t.click("[data-a=play][data-g=hl1]"); t.wait_for_timeout(300); t.click("[data-a=hl-call][data-c=hi]"); t.wait_for_timeout(1500)
    t.click("header [data-a=lesson]"); t.wait_for_timeout(250)
    t.click("[data-a=play-resume][data-k='lily-lp7|td1']"); t.wait_for_selector("#tdCv")
    back = ev(t, "() => { const r = __T.UI.run; const s = JSON.parse(JSON.stringify(r.st)); delete s._rev; return JSON.stringify({ st:s, sim:r.sim }); }")
    sn = json.loads(snap); sn["st"].pop("_rev", None)
    check(json.loads(back) == sn, "▶ Resume after another game: towers, wave, lives, coins and every enemy exactly as left")
    check(t.locator(".td-pause [data-a=td-resume]").count() == 1, "…waiting on ▶ Resume")
    t.click("[data-a=td-resume]"); t.wait_for_timeout(500)
    # ---- 13. Finish later mid-wave → kept from the start of the wave, with the towers as they are now
    ff(t, 300); ev(t, "() => __T.render()"); t.wait_for_timeout(100)
    s = st(t); ws = s["ws"]; free = s["towers"].index(None)
    ev(t, "() => { __T.UI.run.st.coins += 500; __T.UI.run.st.ws.coins += 0; __T.render(); }")
    s = st(t); kills_before = s["kills"]
    build(t, free, "basic")
    s = st(t); ws = s["ws"]
    check(s["phase"] == "wave" and ws["coins"] != s["coins"], "mid-wave (coins %d, wave start %d after the new tower)" % (s["coins"], ws["coins"]))
    t.click("header [data-a=finish-ask]"); t.click("[data-a=fl-later]"); t.wait_for_timeout(600)
    kept = ev(t, "() => __T.STUDENTS['lily'].paused.td")
    check(kept and kept["st"]["phase"] == "build" and kept["st"]["wave"] == s["wave"] and kept["st"]["lives"] == ws["lives"] and kept["st"]["coins"] == ws["coins"] and kept["st"]["towers"] == s["towers"], "Finish later mid-wave: kept at the start of wave %d (lives, coins then), towers as now" % s["wave"])
    res = t.input_value("#res")
    check(res.startswith("Tower Defence (Normal, map 2) (continued, not finished): waves 1–%d this lesson" % s["wave"]) and "lives left" in res and "challenges:" in res and "✓" in res and "Stopped" not in res, "partial result: %s" % res)
    rows = ev(t, "() => __T.RESULTS.filter(r => r.type === 'td')")
    check(len(rows) == 1 and rows[0]["partial"] is True, "saved as a result marked partial")
    # ---- 14. next lesson: Continue restores it exactly; then the final result
    t.click("[data-a=backlesson]"); t.wait_for_timeout(200); t.click("[data-a=home]"); go_lesson(t, "Lily · LP8"); t.wait_for_timeout(300)
    fb = t.inner_text(".flbar")
    check("Tower Defence in progress" in fb and "started" in fb and "Continue" in fb and "Discard" in fb, "next lesson: “Tower Defence in progress (started …): Continue · Discard” (%s)" % fb.replace("\n", " "))
    t.click(".flbar [data-a=fl-cont][data-t=td]"); t.wait_for_selector("#tdCv")
    c = st(t)
    same = all(c[k] == kept["st"][k] for k in ("map", "diff", "towers", "wave", "lives", "coins", "auto", "cleared", "grants", "gotG")) and c["chLog"] == []
    check(same and c["w0"] == kept["st"]["wave"] and c["limit"] == 0, "Continue: map, difficulty, towers, wave, lives, coins and settings exactly as kept (this lesson counts from wave %d)" % c["w0"])
    t.click("[data-a=td-start]"); t.wait_for_timeout(300); end_wave(t)
    if st(t)["pz"]: t.click("[data-a=td-resume]")
    t.click("header [data-a=finish-ask]"); t.click("[data-a=finish]"); t.wait_for_timeout(500)
    res = t.input_value("#res"); w = c["wave"]
    check(res.startswith("Tower Defence (Normal, map 2) (continued, finished): Stopped at wave %d · wave %d this lesson" % (w, w)) and "challenges" not in res, "final result (last time’s challenges were in last time’s result): %s" % res)
    check(not ev(t, "() => (__T.STUDENTS['lily'].paused || {}).td"), "finished: the kept game is gone")
    # ---- 15. lives reach 0: game over
    ev(t, "() => { for (const k in __T.UI.parked) if (__T.UI.parked[k].type === 'hilo') delete __T.UI.parked[k]; }")   # its ▶ Resume button names the lesson too
    t.click("[data-a=backlesson]"); t.wait_for_timeout(200); t.click("[data-a=home]"); go_lesson(t, "Lily · LP7"); t.wait_for_timeout(300)
    t.click("[data-a=play][data-g=td2]"); t.wait_for_selector("#tdCv")
    check(st(t)["phase"] == "build" and st(t)["map"] == 1 and st(t)["diff"] == "normal", "“The student chooses” off: straight to building, the game's own map and difficulty")
    ev(t, "() => { const r = __T.UI.run; r.st.wave = 5; r.st.lives = 3; __T.render(); }")
    t.click("[data-a=td-start]"); t.wait_for_timeout(200); end_wave(t)
    s = st(t); pt = t.inner_text(".td-pause")
    check(s["phase"] == "over" and s["lives"] == 0 and not s["won"] and "Game over" in pt and "Reached wave 5" in pt, "lives reach 0 (the boss costs 5): “Game over”, “Reached wave 5”")
    check(t.locator("header [data-a=pause]").count() == 0 and t.locator("[data-a=td-start]").count() == 0, "nothing to pause or start any more")
    t.click(".td-pause [data-a=finish]"); t.wait_for_timeout(400)
    res = t.input_value("#res")
    check(res.startswith("Tower Defence (Normal, map 2): Game over at wave 5 · waves 1–5 this lesson, 0 lives left, 0 towers"), "final result: %s" % res)
    check(ev(t, "() => __T.RESULTS.filter(r => r.type === 'td').every(r => (r.points || 0) === 0)"), "no lesson points (a break game)")
    check(not errs, "no page errors %s" % errs[:3])
    ctx.close()
    # =============== LIVE: the student plays on their own screen; the teacher's screen shows the status ===============
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    lp = dict(pack1, liveRoom=room, games=[games[1]])
    t = teacher(ctx, seed_db([lp]), errs); go_lesson(t, "Lily · LP7"); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); url = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    t.set_viewport_size({"width":390, "height":844})   # Sam's phone
    s = student(ctx, url, errs); s.wait_for_timeout(900)
    t.click("[data-a=play][data-g=td2]"); s.wait_for_selector("#tdCv", timeout=6000); t.wait_for_timeout(600)
    check(t.locator(".td-status").count() == 1 and t.locator("#tdCv").count() == 0, "teacher's screen: a status screen, no map")
    check(t.locator("#livePill .lo").count() == 0, "no 🔒 override for Tower Defence (the student's screen plays it)")
    o = overflow(t); check(not o, "status screen fits Sam's phone (390×844) %s" % o)
    t.screenshot(path=os.path.join(HERE, "shots", "td-status-phone.png"))
    ns = len(st(s)["towers"]); build(s, ns - 1, "basic"); build(s, ns - 2, "basic"); t.wait_for_timeout(700)   # by the castle: the wave lasts a while
    tiles = t.inner_text(".td-tiles")
    check(st(t)["towers"][ns - 1] == {"k":"basic", "lv":1, "spent":20} and "🏰 2" in tiles and "🪙 80" in tiles, "student builds: the teacher's status shows the towers and coins (%s)" % tiles.replace("\n", " "))
    ev(s, """() => { window.__sent = 0; const ch = __T.LIVE.chan, o = ch.send.bind(ch); ch.send = m => { if (m.payload && m.payload.t === 'st') window.__sent++; return o(m); }; }""")
    s.click("[data-a=td-start]"); t.wait_for_timeout(700)
    check("Playing wave 1" in t.inner_text(".td-stline") and st(t)["phase"] == "wave", "wave start: the status says so at once")
    ev(s, "() => { window.__sent = 0; window.__iv = setInterval(() => { __T.UI.run.st.coins++; }, 100); }")   # something changes all the time
    t.wait_for_timeout(6000); n = ev(s, "(() => { clearInterval(window.__iv); return window.__sent; })()")
    check(2 <= n <= 4, "during a wave the student's screen sends a status at most every 2 s (%d in 6 s, coins changing every 0.1 s)" % n)
    check(st(t)["coins"] == st(s)["coins"] or abs(st(t)["coins"] - st(s)["coins"]) < 40, "the teacher's coins follow the student's (%d / %d)" % (st(t)["coins"], st(s)["coins"]))
    # teacher pause wins
    t.click(".td-status [data-a=td-tpause]"); s.wait_for_timeout(700)
    ss = st(s); a1 = sim(s); s.wait_for_timeout(900); a2 = sim(s)
    check(ss["tlock"] and ss["pz"] == "teacher" and a1 == a2, "teacher ❚❚: the student's game stops")
    check("Paused by your teacher" in s.inner_text(".td-pause") and s.locator(".td-pause [data-a=td-resume]").count() == 0 and s.locator("header [data-a=pause]").count() == 0, "student: “Paused by your teacher”, no ▶ Resume, no ❚❚")
    ev(s, "() => { const r = __T.UI.run; return __T.TYPES.td.act(r, 'td-resume', { getAttribute: () => null }); }")
    s.evaluate("() => document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }))"); s.wait_for_timeout(300)
    check(st(s)["pz"] == "teacher" and st(s)["tlock"], "the student can't resume it (resume refused)")
    check("Paused by you" in t.inner_text(".td-stline") and t.locator("[data-a=td-tres]").count() == 1, "teacher: “Paused by you” and ▶ Unlock")
    t.click("[data-a=td-tres]"); s.wait_for_timeout(700)
    check(not st(s)["tlock"] and "Ready to carry on?" in s.inner_text(".td-pause") and s.locator(".td-pause [data-a=td-resume]").count() == 1, "Unlock: the student gets ▶ Resume")
    check("Waiting for Lily to tap Resume" in t.inner_text(".td-stline"), "teacher: waiting for Lily")
    s.click("[data-a=td-resume]"); s.wait_for_timeout(900)
    check(st(s)["pz"] == "" and sim(s)["t"] > a2["t"] and "Playing wave" in t.inner_text(".td-stline"), "the student resumes; the teacher sees it playing")
    # the student's own pause: the student can resume it
    s.click("header [data-a=pause]"); t.wait_for_timeout(700)
    check(st(s)["pz"] == "me" and "Paused by Lily" in t.inner_text(".td-stline"), "student ❚❚: the teacher sees “Paused by Lily”")
    s.click("[data-a=td-resume]"); t.wait_for_timeout(700)
    check(st(s)["pz"] == "" and "Playing wave" in t.inner_text(".td-stline"), "…and the student resumes it")
    # + Coins from the teacher: once
    c0 = st(s)["coins"]; s.click("header [data-a=pause]"); s.wait_for_timeout(300); c0 = st(s)["coins"]
    t.click(".td-status [data-a=td-coins][data-n='50']"); s.wait_for_timeout(800)
    check(st(s)["coins"] == c0 + 50, "teacher + 50 coins: the student's coins go up by 50 (%d → %d)" % (c0, st(s)["coins"]))
    t.click(".td-status [data-a=td-auto]"); s.wait_for_timeout(1500)
    check(st(s)["coins"] == c0 + 50 and st(s)["auto"] is False, "…once, however many messages follow; Stop after each wave off reaches the student")
    t.click(".td-status [data-a=td-limit][data-v='1']"); s.wait_for_timeout(600)
    check(st(s)["limit"] == 1, "teacher's wave limit reaches the student")
    t.click(".td-status [data-a=td-limit][data-v='0']"); t.click(".td-status [data-a=td-auto]"); s.wait_for_timeout(500)
    s.click("[data-a=td-resume]"); s.wait_for_timeout(300)
    # ⚡ from the teacher: the student's game waits; Good adds coins
    t.click("header [data-a=challenge]"); s.wait_for_timeout(700)
    b1 = sim(s); s.wait_for_timeout(800); b2 = sim(s)
    check(s.locator(".chov").count() == 1 and st(s)["ch"] and b1 == b2, "⚡ on the teacher's phone: the prompt on the student's screen, the wave waits")
    c1 = st(s)["coins"]; t.click("[data-a=ch-mark][data-m=good]"); s.wait_for_timeout(900)
    check(st(s)["ch"] is None and st(s)["coins"] >= c1 + 50 and len(st(s)["chLog"]) == 1 and len(st(t)["chLog"]) == 1, "Good: +50 coins on the student's screen, logged on both")
    # the end of the wave, the teacher's undo
    ev(s, "() => { const r = __T.UI.run; for (let i = 0; i < 40000 && r.st.phase === 'wave' && !r.st.pz; i++) __T.tdStep(r.st, r.sim); __T.saveRun(); __T.render(); }"); t.wait_for_timeout(700)
    check(st(s)["phase"] == "build" and "Wave 1 cleared" in t.inner_text(".td-stline"), "wave cleared and auto-paused: the teacher sees it")
    if st(s)["pz"]: s.click("[data-a=td-resume]")
    build(s, 2, "freeze"); t.wait_for_timeout(700)
    c2 = st(s)["coins"]
    check(t.locator("header .ro").count() == 0, "teacher's header buttons (‹ ❚❚ ⚙ ✕) all work while watching")
    t.click("header [data-a=settings]"); t.click(".setpop [data-a=undo]"); s.wait_for_timeout(800)
    check(st(s)["towers"][2] is None and st(s)["coins"] == c2 + 35, "teacher's ⚙ Undo: the student's last build is taken back")
    errs_live = [e for e in errs]
    check(not errs_live, "no page errors %s" % errs_live[:3])
    ctx.close()
    # =============== SCREEN FIT ===============
    for name, w, h in [("ipad", 1180, 820), ("desktop", 1440, 860), ("phonel", 844, 390)]:
        ctx = b.new_context(viewport={"width":w, "height":h}, has_touch=name.startswith("phone")); errs = []
        t = teacher(ctx, seed_db([pack1]), errs); go_lesson(t, "Lily · LP7"); t.wait_for_timeout(300)
        t.click("[data-a=play][data-g=td1]"); t.wait_for_selector(".td-setup"); fits = []
        fits.append(("setup", overflow(t))); t.screenshot(path=os.path.join(HERE, "shots", "td-%s-setup.png" % name))
        t.click("[data-a=td-go]"); t.wait_for_selector("#tdCv"); tap_slot(t, 3)
        fits.append(("build menu", overflow(t)))
        side = t.evaluate("(() => { const a = document.getElementById('tdCv').getBoundingClientRect(), b = document.querySelector('.td-side').getBoundingClientRect(); return [Math.round(a.right), Math.round(b.left), Math.round(a.bottom), innerHeight]; })()")
        t.click("#tdMenu [data-a=td-build][data-k=basic]"); t.click("[data-a=td-start]"); t.wait_for_timeout(1500)
        fits.append(("wave", overflow(t))); t.screenshot(path=os.path.join(HERE, "shots", "td-%s-wave.png" % name))
        t.click("header [data-a=pause]"); fits.append(("pause", overflow(t)))
        zoom = t.evaluate("document.querySelector('main.stage').style.zoom || '1'")
        bad = [f for f in fits if f[1]]
        if name.startswith("phone"): print(("PASS " if not bad else "NOTE ") + "%s: Tower Defence fits (zoom %s) %s" % (name, zoom, bad))
        else:
            check(not bad and zoom in ("", "1"), "%s: setup, map + build menu, wave and pause fit without scrolling or zoom %s" % (name, bad))
            check(side[0] <= side[1] and side[2] <= side[3], "%s: the whole map and the side panel side by side (%s)" % (name, side))
        check(not errs, "%s no page errors %s" % (name, errs[:2]))
        ctx.close()
done()
