"""27 Nov: a simpler games page. Spelling and Matching tiles with modes over the old kinds (old games open in their own
mode from every route; Hard mode as an option; the mode remembered per student, a saved type always winning; results
still name the mode), one sectioned "Add a game" picker (+ Game) with Words from and a More games drawer, cards with one
main button and a ⋯ menu (Homework link), the score pad (Typhoon tally, Tower Defence coins), home's Resume strip with
Kept games folded, the usual Look on the student's page and a slimmer Advanced. Fit: iPad landscape, phone, desktop."""
import datetime, json
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get STUDENTS(){return STUDENTS},get UNDO(){return UNDO},handle:handle,TYPES:TYPES,GROUPS:GROUPS,pickTiles:pickTiles,modeOf:modeOf,studentLinkData:studentLinkData,unpackData:unpackData,", 1)
TODAY = datetime.date.today().isoformat(); YDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
WC = "kitchen | you cook dinner in this room\nbedroom | you sleep in this room\nbathroom | you take a shower here\ngarden | flowers grow here"
EQ = "you cook dinner in this room = kitchen\nyou sleep in this room = bedroom\nyou take a shower here = bathroom"
MU = "kitchen = you cook here\nbedroom = you sleep here\nbathroom = you shower here"
G = [
  {"id":"g_h", "type":"hangman", "title":"Castle words", "block":WC, "options":{}},
  {"id":"g_a", "type":"anagrams", "title":"Mixed letters", "block":WC, "options":{}},
  {"id":"g_t", "type":"typeit", "title":"Type it", "block":EQ, "options":{}},
  {"id":"g_s", "type":"spelling", "title":"Spell it", "block":"kitchen\nbedroom\ncolour / color", "options":{}},
  {"id":"g_m", "type":"match", "title":"Rooms match", "block":MU, "options":{"mode":"match"}},
  {"id":"g_p", "type":"match", "title":"Rooms memory", "block":MU, "options":{"mode":"pairs"}},
  {"id":"g_c", "type":"cards", "title":"Rooms cards", "block":EQ, "options":{}},
  {"id":"g_b", "type":"bingo", "title":"Room bingo", "block":"a\nb\nc\nd\ne\nf\ng\nh\ni", "options":{"size":3}},
  {"id":"g_ty", "type":"typhoon", "title":"Typhoon", "block":"Pip\nPat", "options":{"size":3, "grid":[], "mix":"10×5, 2×T, 2×x2", "codes":""}},
  {"id":"g_td", "type":"td", "title":"Towers", "block":"", "options":{}},
]
spec = {"student":"Mia", "lp":9, "date":TODAY, "start":"17:00", "length":60, "format":"online",
  "blocks":[{"label":"1 Words", "mins":20, "lines":[{"type":"app", "label":"1A Castle words"}, {"type":"app", "label":"1B Rooms memory"}]}]}
mia9 = {"id":"mia-lp9", "student":"Mia", "lp":9, "title":"Mia · LP9", "date":TODAY, "updatedAt":"x", "games":G, "bank":WC, "liveRoom":"0123456789abcdef0123456789abcdef", "runsheet":spec}
mia8 = {"id":"mia-lp8", "student":"Mia", "lp":8, "title":"Mia · LP8", "date":YDAY, "updatedAt":"x", "games":[dict(G[0])], "bank":WC}
ray3 = {"id":"ray-lp3", "student":"Ray", "lp":3, "title":"Ray · LP3", "date":TODAY, "updatedAt":"x", "games":[], "bank":WC}
res = [{"id":"r1", "packId":"mia-lp8", "gameId":"g_h", "type":"hangman", "title":"Castle words", "summary":"Hangman 2/4", "at":YDAY + "T10:00:00Z", "student":"Mia",
        "items":[{"item":"kitchen", "ok":False}, {"item":"garden", "ok":False}, {"item":"bedroom", "ok":False}, {"item":"bathroom", "ok":True}]},
       {"id":"r2", "packId":"mia-lp9", "gameId":"g_h", "type":"hangman", "title":"Castle words", "summary":"Hangman 3/4", "at":TODAY + "T09:00:00Z", "student":"Mia",
        "items":[{"item":"kitchen", "ok":False}, {"item":"garden", "ok":True}, {"item":"bedroom", "ok":True}, {"item":"bathroom", "ok":True}]}]
kept = {"battleships":{"id":"k1", "type":"battleships", "title":"Ships", "started":YDAY, "at":YDAY + "T10:00:00Z", "fromPack":"ray-lp3", "game":{"type":"battleships", "title":"Ships", "block":"", "options":{}}, "st":{"phase":"play"}, "hid":{}}}
db = seed_db([mia9, mia8, ray3], students=[{"id":"mia", "name":"Mia", "updatedAt":"x"}, {"id":"ray", "name":"Ray", "paused":kept, "updatedAt":"x"}], results=res)
def ev(pg, js, arg=None): return pg.evaluate(js, arg)
def to_lesson(t, pid="mia-lp9"):
    if ev(t, "__T.UI.view") == "play": t.click("[data-a=lesson]"); t.wait_for_timeout(250)
    if ev(t, "__T.UI.view") != "pack" or ev(t, "__T.UI.packId") != pid:
        ev(t, "pid => __T.handle('open', { getAttribute: () => pid })", pid); t.wait_for_timeout(250)
    if ev(t, "__T.UI.view") != "pack": t.click("[data-a=nav-games]"); t.wait_for_timeout(250)
def home(t):
    if ev(t, "__T.UI.view") == "play": t.click("[data-a=lesson]"); t.wait_for_timeout(200)
    t.click("[data-a=home]"); t.wait_for_timeout(200)
def card(t, gid): return t.locator(".game:has([data-g='%s'])" % gid).first
def run(t): return ev(t, "__T.UI.run ? { type: __T.UI.run.type, gid: __T.UI.run.gameId, title: __T.UI.run.title, mode: (__T.UI.run.st.mode || null), ch: !!(__T.UI.run.gflags && __T.UI.run.gflags._challenge) } : null")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, db, errs); t.wait_for_selector("#stuSec", timeout=8000)
    t.on("dialog", lambda d: (errs.append("browser dialog: " + d.message), d.dismiss()))
    to_lesson(t)
    # ---- Part 4: cards. One main button, Retry visible, everything else in ⋯
    labels = {"g_h":"Spelling · Hangman", "g_a":"Spelling · Anagrams", "g_t":"Spelling · Type the answer", "g_s":"Spelling · Spelling test",
              "g_m":"Matching · Match up", "g_p":"Matching · Memory pairs", "g_c":"Matching · Flash cards", "g_b":"Bingo"}
    for gid, lab in labels.items():
        check(lab in card(t, gid).inner_text(), "old %s game shows as %s" % (gid, lab))
    vis = ev(t, "[...document.querySelectorAll('.game')].map(c => [...c.querySelectorAll('button, .gmenu > summary')].filter(b => b.offsetParent && !b.closest('.gm-pop')).map(b => b.dataset.a || 'menu').join(','))")
    check(all(v.split(",")[0] in ("play", "play-resume") and v.split(",")[-1] == "menu" and len([x for x in v.split(",") if x not in ("retry", "menu")]) == 1 for v in vis), "each card shows one main button (+ Retry when there are misses) and ⋯: %s" % vis[:3])
    check(card(t, "g_h").locator("[data-a=retry]").is_visible() and "Retry 1 miss" in card(t, "g_h").inner_text(), "Retry N misses stays visible on the card")
    check(card(t, "g_h").locator("[data-a=editgame]").is_hidden(), "Edit is folded into ⋯ until it's opened")
    card(t, "g_h").locator(".gmenu > summary").click(); t.wait_for_timeout(150)
    m = card(t, "g_h").locator(".gm-pop").inner_text()
    check(all(x in m for x in ["Play in hard mode", "Play as Anagrams", "Play as Type the answer", "Play as Spelling test", "Edit", "Details", "Homework link", "One game on their own device, e.g. homework. In class, use the class link."]), "the ⋯ menu has every old action: %s" % m.replace("\n", " | "))
    t.mouse.click(5, 400); t.wait_for_timeout(150)
    check(card(t, "g_h").locator(".gm-pop").is_hidden(), "tapping outside closes the ⋯ menu")
    card(t, "g_b").locator(".gmenu > summary").click(); mb = card(t, "g_b").locator(".gm-pop").inner_text(); t.mouse.click(5, 400)
    check("Print" in mb and "My card" in mb and "Homework link" in mb, "bingo's ⋯ has Print, My card and Homework link")
    # Homework link: the old Student link
    menu_click(t, "[data-a=slink][data-g=g_h]"); t.wait_for_function("() => document.getElementById('slinkUrl') && document.getElementById('slinkUrl').value.includes('#s=')", timeout=5000)
    check("Homework link · Castle words" in t.inner_text(".overlay h3"), "the link window is called Homework link")
    url = t.input_value("#slinkUrl"); t.click("[data-a=slink-close]")
    sp = student(ctx, url, errs); sp.wait_for_timeout(600); sp.click("[data-a=s-start]"); sp.wait_for_timeout(300)
    check(ev(sp, "__T.UI.run.type") == "hangman" and ev(sp, "__T.UI.run.gameId") == "g_h", "the Homework link opens the same game as the old Student link (Hangman)")
    sp.close()
    # ---- Part 2: old saved types open as themselves, from every route
    for gid, ty, mode in [("g_h", "hangman", None), ("g_a", "anagrams", None), ("g_t", "typeit", None), ("g_s", "spelling", None), ("g_m", "match", "match"), ("g_p", "match", "pairs"), ("g_c", "cards", None)]:
        to_lesson(t); t.click("[data-a=play][data-g=%s], [data-a=play-resume][data-k='mia-lp9|%s']" % (gid, gid)); t.wait_for_timeout(250)
        r = run(t); check(r and r["type"] == ty and r["gid"] == gid and (mode is None or r["mode"] == mode), "lesson page: %s opens as %s%s" % (gid, ty, " (" + mode + ")" if mode else ""))
    to_lesson(t); ev(t, "() => __T.handle('pl-play', { getAttribute: k => k === 'data-g' ? 'g_p' : null })"); t.wait_for_timeout(300)
    r = run(t); check(r and r["type"] == "match" and r["mode"] == "pairs", "plan chip: Memory pairs opens in Memory pairs mode")
    to_lesson(t); t.click("[data-a=rs-open]"); t.wait_for_timeout(300)
    t.locator("[data-a=rs-play][data-g=g_h]").first.click(); t.wait_for_timeout(300)
    r = run(t); check(r and r["type"] == "hangman" and r["gid"] == "g_h", "run sheet Play row: Hangman opens as Hangman")
    home(t)
    t.locator("[data-a=play-resume][data-k='mia-lp9|g_h']").first.click(); t.wait_for_timeout(250)
    r = run(t); check(r and r["type"] == "hangman", "home ▶ Resume carries on the same Hangman")
    # Hard mode: the option on the card and on the start screen behave like the old button
    to_lesson(t); menu_click(t, "[data-a=play-ch][data-g=g_a]"); t.wait_for_timeout(250)
    r1 = run(t); st1 = ev(t, "__T.UI.run.st.ch")
    check(r1["ch"] and r1["title"] == "Mixed letters (hard mode)", "card ⋯ › Play in hard mode = the old Hard mode button: %s" % r1["title"])
    to_lesson(t); picker(t); t.click("[data-a=pick-tile][data-k=spell]"); t.click("[data-a=pick-mode][data-m=hangman]"); t.click("[data-a=pick-hard][data-v='1']"); t.click("[data-a=pick-go]"); t.wait_for_timeout(300)
    r2 = run(t); check(r2["type"] == "hangman" and r2["ch"] and r2["title"].endswith("(hard mode)") and ev(t, "__T.UI.run.st.ch") is True and st1 is True, "start screen Hard mode plays as the old Hard mode: %s %s %s" % (r2, st1, ev(t, "__T.UI.run.st.ch")))
    # Play as: the same words in another mode; the saved game isn't changed
    to_lesson(t); n0 = ev(t, "__T.PACKS.find(p => p.id === 'mia-lp9').games.length")
    menu_click(t, "[data-a=playas][data-g=g_h][data-m=anagrams]"); t.wait_for_timeout(300)
    r = run(t); g_h = ev(t, "__T.PACKS.find(p => p.id === 'mia-lp9').games.find(g => g.id === 'g_h')")
    check(r["type"] == "anagrams" and r["title"] == "Castle words · Anagrams" and g_h["type"] == "hangman" and g_h["block"] == WC, "Play as Anagrams keeps the words, makes a copy; the saved Hangman is unchanged")
    check(ev(t, "__T.PACKS.find(p => p.id === 'mia-lp9').games.length") == n0 + 1, "Play as adds one game to the lesson")
    # ---- Part 2/3/6: mode remembered per student; picker start screen; results name the mode
    to_lesson(t); picker(t); t.click("[data-a=pick-tile][data-k=spell]")
    check(ev(t, "document.querySelector('[data-a=pick-mode][aria-checked=true]').dataset.m") == "anagrams", "the Spelling tile opens in the mode last used with Mia (Anagrams, from Play as)")
    t.click("[data-a=pick-mode][data-m=typeit]")
    check(t.locator("[data-a=pick-hard]").count() == 0, "Type the answer has no Hard mode option")
    t.click("[data-a=pick-go]"); t.wait_for_timeout(300)
    check(run(t)["type"] == "typeit" and ev(t, "__T.STUDENTS.mia.modes.spell") == "typeit", "Start plays Type the answer and remembers it for Mia")
    to_lesson(t, "ray-lp3"); picker(t); t.click("[data-a=pick-tile][data-k=spell]")
    check(ev(t, "document.querySelector('[data-a=pick-mode][aria-checked=true]').dataset.m") == "hangman", "another student starts in the first mode (Hangman)")
    t.click("[data-a=pick-mode][data-m=anagrams]"); t.click("[data-a=pick-go]"); t.wait_for_timeout(300)
    check(run(t)["type"] == "anagrams", "quick Anagrams starts")
    ev(t, "() => { const s = __T.UI.run.st; }"); t.click("[data-a=finish-ask]"); t.click("[data-a=finish]"); t.wait_for_timeout(400)
    last = ev(t, "__T.RESULTS.filter(r => r.packId === 'ray-lp3').map(r => r.summary + ' | ' + r.type)")
    check(last and last[0].startswith("Anagrams") and last[0].endswith("| anagrams"), "results still name the mode: %s" % last)
    # a plan-saved type always wins over the remembered mode
    to_lesson(t); t.click("[data-a=play][data-g=g_c], [data-a=play-resume][data-k='mia-lp9|g_c']"); t.wait_for_timeout(250)
    check(run(t)["type"] == "cards", "a saved Flash Cards game plays as Flash Cards, whatever mode Mia used last")
    # ---- Part 3: the picker
    to_lesson(t); picker(t)
    secs = ev(t, "[...document.querySelectorAll('.pk-sec h4')].map(h => h.textContent)")
    check(secs == ["Practice", "Break & reward", "Class tools", "More games"], "picker sections: %s" % secs)
    tiles = ev(t, "[...document.querySelectorAll('.picker [data-a=pick-tile]')].map(b => b.dataset.k)")
    kinds = ev(t, "Object.keys(__T.TYPES)")
    reach = set(tiles); [reach.update(m["t"] for m in ev(t, "__T.GROUPS[%s].modes" % json.dumps(k))) for k in tiles if k in ("spell", "matching")]
    check(sorted(reach & set(kinds)) == sorted(kinds) and len(tiles) == len(set(tiles)), "every kind is in the one picker, once (Memory pairs through Matching): missing %s" % sorted(set(kinds) - reach))
    check(ev(t, "[...document.querySelectorAll('[data-sec=break] [data-a=pick-tile]')].map(b => b.dataset.k).join(',')") == "typhoon,snakes,hilo,td,battleships", "Break & reward: Typhoon, Snakes & Ladders, Higher or Lower, Tower Defence, Battleships")
    check(ev(t, "[...document.querySelectorAll('[data-sec=tools] [data-a=pick-tile]')].map(b => b.dataset.k).join(',')") == "bingo,wheel,taboo,slot,dice", "Class tools: Bingo, Random wheel, Taboo, Slot machine, Story Dice")
    check(t.locator("#pickMore [data-a=pick-tile][data-k=cross]").count() == 1 and not ev(t, "document.getElementById('pickMore').open"), "Crossword starts in the folded More games drawer")
    check(t.locator(".picker .pk-sec:not(#pickMore) [data-a=pick-tile] .muted, .picker small").count() == 0, "tiles: an icon and a short name, no descriptions")
    # iPad landscape: sections 1-3 without scrolling
    bot = ev(t, "Math.max(...[...document.querySelectorAll('[data-sec=tools] [data-a=pick-tile]')].map(b => b.getBoundingClientRect().bottom))")
    check(bot <= 820, "iPad landscape: Practice, Break & reward and Class tools fit without scrolling (bottom %d)" % bot)
    # the More games setting
    t.click("[data-a=pick-arr]"); t.click("[data-a=pick-tile][data-k=quiz]"); t.wait_for_timeout(150)
    check(ev(t, "__T.STUDENTS['~teacher'].pickMore.includes('quiz')") and t.locator("#pickMore [data-a=pick-tile][data-k=quiz]").count() == 1, "the More games setting moves Quiz into the drawer (saved as a teacher setting)")
    t.click("#pickMore [data-a=pick-tile][data-k=cross]"); t.click("[data-a=pick-arr]"); t.wait_for_timeout(150)
    check(t.locator("[data-sec=practice] [data-a=pick-tile][data-k=cross]").count() == 1 and ev(t, "__T.PACKS.length") == 3, "…and Crossword out of it; nothing deleted")
    # Words from: a source button changes the word line and the game built
    scope(t, "missed"); line = t.inner_text(".pk-line")
    check(line.startswith("Warm-up") and "kitchen" in line and "garden" in line, "Words from: Missed lately lists the missed words: %s" % line)
    t.click("[data-a=pick-tile][data-k=matching]"); t.click("[data-a=pick-mode][data-m=pairs]"); t.click("[data-a=pick-go]"); t.wait_for_timeout(300)
    r = run(t); check(r["type"] == "match" and r["mode"] == "pairs" and "missed words" in r["title"], "Memory pairs from missed words: %s" % r["title"])
    scope(t, "today") if ev(t, "__T.UI.view") == "pack" else None
    to_lesson(t); scope(t, "today"); t.click("[data-a=pick-close]")
    # a kind that needs its own content opens the editor; Type your own does too, with only that mode's fields
    tile(t, "quiz"); t.wait_for_timeout(200)
    check(ev(t, "__T.UI.view") == "gameEdit" and ev(t, "__T.UI.draftGame.type") == "quiz", "Quiz tile opens the editor")
    t.click("[data-a=cancelgame]"); t.wait_for_timeout(200)
    tile(t, "spell"); t.click("[data-a=pick-mode][data-m=spelling]"); t.click("[data-a=pick-own]"); t.wait_for_timeout(200)
    check(ev(t, "__T.UI.draftGame.type") == "spelling" and "clue" not in t.inner_text("label[for=gBlock]").lower(), "Type your own: the Spelling test editor (no clue fields)")
    t.click("[data-a=cancelgame]"); t.wait_for_timeout(200)
    tile(t, "typhoon"); t.wait_for_timeout(200)
    check(t.locator(".pk-opt").count() == 0 and t.locator("[data-a=pick-own]").inner_text() == "Set it up first", "Typhoon's start screen: no modes or words, ▶ Start or Set it up first")
    t.click("[data-a=pick-go]"); t.wait_for_timeout(300)
    check(run(t)["type"] == "typhoon", "▶ Start: Typhoon on the spot")
    # ---- Part 5: score pad
    if t.locator("[data-a=tp-view][data-v=master]").count(): t.click("[data-a=tp-view][data-v=master]"); t.wait_for_timeout(200)
    sc = lambda: ev(t, "__T.UI.run.st.players.map(p => p.score)")
    check(t.locator("[data-a=tp-step]").count() == 0 and t.locator("[data-a=tp-score]").count() == 0, "the ±1/±5/±10 step picker and single +/− are gone")
    t.click("[data-a=tp-add][data-k='0'][data-v='50']"); t.click("[data-a=tp-add][data-k='0'][data-v='25']")
    t.click(".ty-p:nth-child(1) [data-a=spad-neg]"); t.click("[data-a=tp-add][data-k='0'][data-v='-10']"); t.wait_for_timeout(100)
    check(sc()[0] == 65 and ev(t, "document.querySelector('[data-a=spad-neg]').getAttribute('aria-pressed')") == "false", "quick buttons +50 +25, then − and 10 takes 10 away (65); − goes back off")
    t.click("[data-a=spad-open][data-k='0']")
    for d in "120": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
    t.click("[data-a=spad-op][data-v=add]"); a1 = sc()[0]
    for d in "20": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
    t.click("[data-a=spad-op][data-v=sub]"); a2 = sc()[0]
    for d in "300": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
    t.click("[data-a=spad-op][data-v=set]"); a3 = sc()[0]
    t.click("[data-a=spad-op][data-v=zero]"); a4 = sc()[0]
    check([a1, a2, a3, a4] == [185, 165, 300, 0], "pad: 65 + 120, − 20, = 300, ↺ 0 → %s" % [a1, a2, a3, a4])
    for d in "99999": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
    check(t.inner_text(".spad-num") == "9999", "typed numbers stop at 9999: %s" % t.inner_text(".spad-num"))
    t.click(".spad [data-a=spad-key][data-v=bk]"); check(t.inner_text(".spad-num") == "999", "⌫ takes a digit off")
    t.click(".spad-ok"); t.wait_for_timeout(100); check(t.locator(".spad").count() == 0, "✓ closes the pad")
    t.click("[data-a=spad-open][data-k='0']"); t.mouse.click(20, 300); t.wait_for_timeout(100)
    check(t.locator(".spad").count() == 0, "a tap outside closes the pad")
    t.click("[data-a=settings]"); t.wait_for_timeout(100); t.click("[data-a=undo]"); t.wait_for_timeout(100)
    check(sc()[0] == 300, "Settings → Undo takes back the last score change (↺ 0): %s" % sc())
    # read-only board (the student's screen): no pad
    t.click("[data-a=lesson]"); t.wait_for_timeout(200)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); curl = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    s = student(ctx, curl, errs); s.wait_for_timeout(800)
    t.locator("[data-a=play-resume]").first.click() if t.locator("[data-a=play-resume][data-k^='mia-lp9|q']").count() else None
    t.wait_for_timeout(1200)
    if ev(s, "__T.UI.run && __T.UI.run.type") == "typhoon":
        check(s.locator("[data-a=spad-open], [data-a=tp-add], .spad").count() == 0 and s.locator(".ty-tally .sc").count() >= 1, "the board (student's screen) shows the scores read-only, no pad")
        ev(s, "() => __T.handle('spad-open', { getAttribute: () => '0' })"); s.wait_for_timeout(100)
        check(s.locator(".spad").count() == 0, "the board can't open the pad even by a crafted tap")
    else: check(False, "Typhoon reached the student's board (%s)" % ev(s, "__T.UI.view"))
    s.close()
    # Tower Defence coins (teacher alone: applied at once)
    to_lesson(t); t.click("[data-a=play][data-g=g_td]"); t.wait_for_timeout(300)
    if t.locator("[data-a=td-go]").count(): t.click("[data-a=td-go]"); t.wait_for_timeout(300)
    t.click("[data-a=settings]"); t.wait_for_timeout(150)
    c0 = ev(t, "__T.UI.run.st.coins")
    if t.locator("[data-a=td-coins][data-v='25']").count():
        t.click("[data-a=td-coins][data-v='25']"); t.wait_for_timeout(100)
        c1 = ev(t, "__T.UI.run.st.coins")
        if not t.locator("[data-a=spad-open]").is_visible(): t.click("[data-a=settings]"); t.wait_for_timeout(100)
        t.click("[data-a=spad-open]");
        for d in "500": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
        t.click("[data-a=spad-op][data-v=set]"); c2 = ev(t, "__T.UI.run.st.coins")
        for d in "9999": t.click(".spad [data-a=spad-key][data-v='%s']" % d)
        t.click("[data-a=spad-op][data-v=sub]"); c3 = ev(t, "__T.UI.run.st.coins")
        check([c1 - c0, c2, c3] == [25, 500, 0], "TD coins: +25 quick, = 500, − 9999 stops at 0 → %s" % [c1 - c0, c2, c3])
        t.click(".spad-ok")
        if ev(t, "__T.UI.settingsOpen"): ev(t, "() => __T.handle('settings', null)"); t.wait_for_timeout(100)
    else: check(False, "TD shows coin quick buttons on the teacher's screen")
    # ---- Part 7: home
    to_lesson(t); t.click("[data-a=play][data-g=g_m], [data-a=play-resume][data-k='mia-lp9|g_m']"); t.wait_for_timeout(200); t.click("[data-a=lesson]")   # today's, left part-way
    ev(t, "() => { const r = Object.values(__T.UI.parked || {})[0]; }")
    to_lesson(t, "mia-lp8"); t.click("[data-a=play][data-g=g_h], [data-a=play-resume][data-k='mia-lp8|g_h']"); t.wait_for_timeout(200); t.click("[data-a=lesson]")   # yesterday's
    home(t)
    full = ev(t, "[...document.querySelectorAll('.wrap > p.row [data-a=play-resume]')].map(b => b.dataset.k)")
    check(full and all(k.startswith("mia-lp9|") or k.startswith("ray-lp3|") for k in full) and "mia-lp8|g_h" not in full, "only games from today's lessons show in full: %s" % full)
    check(len(full) <= 3, "at most three in full (newest first); the rest fold away (%d)" % len(full))
    ksum = t.inner_text("#keptSec > summary")
    check(t.locator("#keptSec").count() == 1 and not ev(t, "document.getElementById('keptSec').open") and "Kept games (" in ksum, "the rest fold under one line: %s" % ksum)
    t.click("#keptSec > summary"); kt = t.inner_text("#keptSec")
    check("Castle words" in kt and "Mia" in kt and "LP8" in kt and "Ships" in kt and "Ray" in kt and "Finish later" in kt, "each kept game shows the student, the lesson and the date: %s" % kt.replace("\n", " | "))
    t.click("#keptSec [data-a=kg-ask][data-k='mia-lp8|g_h']"); t.wait_for_timeout(100)
    check(t.locator(".kg-ask").count() == 1 and ev(t, "((__T.UI.run && __T.UI.run.packId === 'mia-lp8') || !!(__T.UI.parked || {})['mia-lp8|g_h'])"), "✕ asks inline first (nothing discarded yet)")
    t.click("[data-a=kg-no]"); t.click("#keptSec [data-a=kg-ask][data-k='mia-lp8|g_h']"); t.click("[data-a=kg-go]"); t.wait_for_timeout(200)
    check(not ev(t, "((__T.UI.run && __T.UI.run.packId === 'mia-lp8') || !!(__T.UI.parked || {})['mia-lp8|g_h'])") and t.locator("[data-k='mia-lp8|g_h']").count() == 0, "Discard removes the kept game")
    t.click("#keptSec > summary") if t.locator("#keptSec").count() and not ev(t, "document.getElementById('keptSec').open") else None
    t.click("[data-a=kg-ask][data-k='fl|ray|battleships']"); t.click("[data-a=kg-go]"); t.wait_for_timeout(200)
    check(not ev(t, "Object.keys(__T.STUDENTS.ray.paused || {}).length"), "a Finish later game can be discarded from Kept games too")
    # ---- Part 8: Look and Advanced
    to_lesson(t); t.click("#advSec > summary"); t.wait_for_timeout(150)
    adv = t.inner_text("#advSec")
    check(t.locator("#lkStu").count() == 0 and t.locator("#lkPack").count() == 1, "the lesson's Advanced has this lesson's look only")
    check(all(x in adv for x in ["Add a student’s result", "Copy lesson results", "Edit lesson details", "Delete lesson"]) and "Online students" not in adv, "Advanced keeps the rare admin; Online students has moved")
    check(ev(t, "(() => { const b = document.getElementById('clsBar'), h = b && b.nextElementSibling; return !!(h && h.matches('details.help')); })()"), "the class link's How it works sits right under the class link bar")
    ev(t, "() => __T.handle('student', { getAttribute: () => 'Mia' })"); t.wait_for_timeout(200)
    check(t.locator("#lkStu").count() == 1, "the student's usual look is on the 👤 page")
    t.select_option("#lkStu", "dark") if ev(t, "[...document.querySelectorAll('#lkStu option')].some(o => o.value === 'dark')") else t.select_option("#lkStu", index=1)
    t.wait_for_timeout(150); check(ev(t, "!!__T.STUDENTS.mia.look"), "changing it saves the student's look")
    # ---- fit: picker, cards (menu open), pad, home, test page
    for nm, vw in [("ipad", {"width":1180, "height":820}), ("phone", {"width":390, "height":844}), ("desktop", {"width":1440, "height":900})]:
        t.set_viewport_size(vw); W = vw["width"]
        def wide():
            return ev(t, "W => { const out = []; if (document.documentElement.scrollWidth > W + 1) out.push('page wide ' + document.documentElement.scrollWidth); document.querySelectorAll('#app *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && r.height && (r.right > W + 2 || r.left < -2) && !e.closest('.gmenu:not([open])')) out.push((e.className || e.tagName) + ' ' + Math.round(r.left) + '-' + Math.round(r.right)); }); return out.slice(0, 4); }", W)
        to_lesson(t); t.wait_for_timeout(150)
        card(t, "g_b").locator(".gmenu > summary").click(); t.wait_for_timeout(100)
        check(not wide(), "%s: cards and an open ⋯ menu fit the width %s" % (nm, wide())); t.screenshot(path=HERE + "/shots/games_cards_%s.png" % nm); t.mouse.click(3, 300)
        picker(t); check(not wide(), "%s: the picker fits the width %s" % (nm, wide())); t.screenshot(path=HERE + "/shots/games_picker_%s.png" % nm)
        t.click("[data-a=pick-tile][data-k=spell]"); check(not wide() and t.locator("[data-a=pick-go]").is_visible(), "%s: the start screen fits %s" % (nm, wide())); t.screenshot(path=HERE + "/shots/games_start_%s.png" % nm)
        gb = ev(t, "(() => { const r = document.querySelector('[data-a=pick-go]').getBoundingClientRect(); return r.bottom; })()")
        check(gb <= vw["height"], "%s: ▶ Start is on screen without scrolling (%d)" % (nm, gb))
        t.click("[data-a=pick-close]")
        t.click("[data-a=play-resume][data-k^='mia-lp9|q'], [data-a=play][data-g=g_ty]"); t.wait_for_timeout(200)
        if ev(t, "__T.UI.run.type") == "typhoon":
            if t.locator("[data-a=tp-view][data-v=master]").count(): t.click("[data-a=tp-view][data-v=master]")
            t.click("[data-a=spad-open][data-k='0']"); t.wait_for_timeout(100)
            pr = ev(t, "(() => { const r = document.querySelector('.spad').getBoundingClientRect(); const k = [...document.querySelectorAll('.spad-keys button')].map(b => b.getBoundingClientRect()); return [r.left, r.right, r.top, r.bottom, Math.min(...k.map(x => x.height)), Math.min(...k.map(x => x.width))]; })()")
            check(pr[0] >= 0 and pr[1] <= W and pr[2] >= 0 and pr[3] <= vw["height"] + 1 and pr[4] >= 48 and pr[5] >= 48, "%s: the pad fits, keys at least 48px: %s" % (nm, [round(x) for x in pr]))
            if nm == "phone": check(pr[3] >= vw["height"] - 2 and pr[2] > vw["height"] / 3, "phone: the pad sits at the bottom, in thumb reach (top %d)" % pr[2])
            t.screenshot(path=HERE + "/shots/games_pad_%s.png" % nm); t.click(".spad-ok"); t.click("[data-a=lesson]")
        t.click("[data-a=home]"); t.wait_for_timeout(150); check(not wide(), "%s: home fits the width %s" % (nm, wide())); t.screenshot(path=HERE + "/shots/games_home_%s.png" % nm)
        t.click("[data-a=tst-open-page]"); t.wait_for_timeout(250); check(not wide(), "%s: the test page fits the width %s" % (nm, wide()))
        t.click("[data-a=home]"); t.wait_for_timeout(150)
    check(not errs, "no page errors or browser dialogs %s" % errs[:3])
done()
