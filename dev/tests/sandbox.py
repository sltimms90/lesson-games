"""27 Nov: the test sandbox (Part 9) and the class link following every game (Part 1).
Test students (students.data.test) stay out of the day list, Students, Phase B owed, missed words, Keeps coming up and
progress; backups keep them. 🧪 Test → Reset sandbox wipes only test students' lessons / results / sheets / kept games and
seeds one "Every game" lesson each, with a game of every kind in TYPES (a new kind without a seed entry fails here).
Then, with one class link, every kind opened on the teacher's side appears on the student's page. A student page from an
older build reloads itself once to fetch the new one; if it can't, the teacher is told."""
import json
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get STUDENTS(){return STUDENTS},get SHEETS(){return SHEETS},get PHASEB(){return PHASEB},SBX_SEED:SBX_SEED,TYPES:TYPES,missedWords:missedWords,stuckWords:stuckWords,progressData:progressData,pbAll:pbAll,backupData:backupData,isTestPack:isTestPack,lessonResultsText:lessonResultsText,", 1)
TODAY = __import__("datetime").date.today().isoformat()
YDAY = (__import__("datetime").date.today() - __import__("datetime").timedelta(days=1)).isoformat()
H = {"id":"g1","type":"hangman","title":"Words","block":"cat | a pet\ndog | it barks\nfish | it swims","options":{}}
miss = [{"item":"cat","ok":False,"note":""},{"item":"dog","ok":False,"note":""},{"item":"fish","ok":True,"note":""}]
demo_old = {"id":"demo-lp5","student":"Demo","lp":5,"title":"Demo · LP5","date":YDAY,"updatedAt":"x","games":[H]}
demo_new = {"id":"demo-lp6","student":"Demo","lp":6,"title":"Demo · LP6","date":TODAY,"updatedAt":"x","games":[H],"bank":"cat | a pet\nbird | it flies"}
mia_old = {"id":"mia-lp8","student":"Mia","lp":8,"title":"Mia · LP8","date":YDAY,"updatedAt":"x","games":[H]}
mia_new = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":TODAY,"updatedAt":"x","games":[H],"bank":"cat | a pet\nbird | it flies"}
demox = {"id":"demox-lp1","student":"Demox","lp":1,"title":"Demox · LP1","date":TODAY,"updatedAt":"x","games":[H]}   # a real student whose name looks like a test one
res = lambda i, pid, at: {"id":i,"packId":pid,"gameId":"g1","type":"hangman","title":"Words","summary":"Hangman 1/3","at":at,"items":miss,"student":pid.split("-")[0].title()}
results = [res("r1","demo-lp5","2026-11-20T10:00:00Z"), res("r2","mia-lp8","2026-11-20T10:00:00Z"), res("r3","demox-lp1","2026-11-20T10:00:00Z"), res("r4","demo-lp6",TODAY+"T09:00:00Z"), res("r5","mia-lp9",TODAY+"T09:00:00Z")]
kept = {"td":{"id":"k1","type":"td","title":"Towers","started":YDAY,"st":{"wave":2},"hid":{}}}
db = seed_db([demo_old, demo_new, mia_old, mia_new, demox],
  students=[{"id":"demo","name":"Demo","updatedAt":"x"}, {"id":"mia","name":"Mia","paused":kept,"updatedAt":"x"}, {"id":"demox","name":"Demox","paused":kept,"updatedAt":"x"}],
  results=results)
for pid in ["demo-lp6", "mia-lp9", "demox-lp1"]: db["sheets"][pid] = {"id":pid, "data":{"id":pid, "packId":pid, "marks":{"x":{"done":True}}}}
def ev(pg, js): return pg.evaluate(js)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, db, errs); t.wait_for_selector("#stuSec", timeout=8000)
    # ---- before the flag: Demo is an ordinary student (nothing hidden until the sandbox is set up)
    check("Demo · LP6" in t.inner_text("#app"), "before setting up, Demo is on the day list like any student")
    check(t.locator("[data-a=tst-open-page]").count() == 1, "home has a 🧪 Test button")
    check(t.evaluate("document.querySelector('[data-a=tst-open-page]').compareDocumentPosition(document.querySelector('[data-a=backup]')) & Node.DOCUMENT_POSITION_PRECEDING") > 0, "🧪 Test sits at the bottom, after Your data")
    # ---- the test page turns Demo into a test student and adds Demo Pair
    t.click("[data-a=tst-open-page]"); t.wait_for_selector(".sbx-stu", timeout=4000); t.wait_for_timeout(400)
    st = ev(t, "JSON.parse(JSON.stringify(__T.STUDENTS))")
    check(st["demo"].get("test") is True and st["demo-pair"].get("test") is True and st["demo-pair"].get("players") == ["Pip", "Pat"], "Demo flagged as a test student; Demo Pair (Pip, Pat) added")
    check(not st["mia"].get("test") and not st["demox"].get("test"), "real students untouched by the set-up")
    check(t.locator(".sbx-stripe").count() == 1, "the test page shows the 🧪 stripe")
    check("Demo · LP6" in t.inner_text("#app") and "Demo Pair" in t.inner_text("#app"), "test page lists the test students and their lessons")
    # ---- kept apart
    t.click("[data-a=home]"); t.wait_for_timeout(300); home = t.inner_text("#app")
    check("Demo · LP6" not in home and "Mia · LP9" in home and "Demox · LP1" in home, "test lessons are off home's day list; real ones stay")
    t.click("#stuSec > summary"); t.wait_for_timeout(150)
    check(t.locator("#stuSec [data-a=student][data-s=Demo]").count() == 0 and t.locator("#stuSec [data-a=student][data-s=Mia]").count() == 1, "test students are off home's Students list")
    pb = ev(t, "__T.pbAll().owed.concat(__T.pbAll().look).map(o => o.p.id)")
    check("demo-lp6" not in pb and "demo-lp5" not in pb and "mia-lp9" in pb, "Phase B owed / needs a look skip test lessons: %s" % pb)
    check(ev(t, "__T.missedWords(__T.PACKS.find(p => p.id === 'demo-lp6')).length") == 0 and ev(t, "__T.missedWords(__T.PACKS.find(p => p.id === 'mia-lp9')).length") == 2, "missed words: none for a test lesson, as before for a real one")
    check(ev(t, "__T.progressData('Demo').lessons.length") == 0 and ev(t, "__T.progressData('Mia').lessons.length") == 2, "progress patterns leave test students out")
    check(ev(t, "__T.stuckWords(__T.PACKS.find(p => p.id === 'demo-lp6')).length") == 0, "Keeps coming up leaves test students out")
    check(ev(t, "__T.lessonResultsText(__T.PACKS.find(p => p.id === 'demo-lp6'))").startswith("🧪 TEST LESSON"), "Copy lesson results marks a test lesson as a test")
    bk = ev(t, "JSON.stringify(__T.backupData().collections)")
    check('"demo-lp6"' in bk and '"test":true' in bk, "backups still include test students and their lessons")
    t.click("[data-a=newpack]"); t.wait_for_timeout(200)
    check(ev(t, "[...document.querySelectorAll('#stuList option')].map(o => o.value).join(',')") == "Demox,Mia", "New lesson's student list has only real students")
    t.click("[data-a=cancelpack]"); t.wait_for_timeout(200)
    # ---- reset
    t.click("[data-a=tst-open-page]"); t.wait_for_selector("[data-a=tst-reset]")
    t.click("[data-a=tst-reset]"); t.wait_for_timeout(150)
    check(t.locator("[data-a=tst-reset-go]").count() == 1 and t.locator(".sbx-ask").count() == 1, "Reset asks inline first")
    t.click("[data-a=tst-reset-no]"); t.wait_for_timeout(150)
    check(ev(t, "__T.PACKS.some(p => p.id === 'demo-lp6')"), "Cancel leaves the sandbox as it was")
    t.on("dialog", lambda d: (errs.append("browser dialog: " + d.message), d.dismiss()))
    t.click("[data-a=tst-reset]"); t.click("[data-a=tst-reset-go]"); t.wait_for_timeout(1500)
    ids = sorted(ev(t, "__T.PACKS.map(p => p.id)"))
    check(ids == ["demo-every", "demo-pair-every", "demox-lp1", "mia-lp8", "mia-lp9"], "reset: test lessons replaced by one Every game each: %s" % ids)
    check(sorted(ev(t, "__T.RESULTS.map(r => r.id)")) == ["r2", "r3", "r5"], "reset deletes test results only")
    check(sorted(ev(t, "Object.keys(__T.SHEETS)")) == ["demox-lp1", "mia-lp9"], "reset clears test run sheet marks only")
    st = ev(t, "JSON.parse(JSON.stringify(__T.STUDENTS))")
    check(st["mia"].get("paused") == kept and st["demox"].get("paused") == kept and not st["demo"].get("paused"), "kept games: real students keep theirs")
    mk = json.loads(ev(t, "JSON.stringify(window.__MOCKDB || null)") or "null")
    kinds = ev(t, "Object.keys(__T.TYPES)")
    missing = ev(t, "Object.keys(__T.TYPES).filter(k => !__T.SBX_SEED[k])")
    check(not missing, "the seed has every game kind (add new kinds to SBX_SEED): missing %s" % missing)
    ev_every = ev(t, "(() => { const p = __T.PACKS.find(p => p.id === 'demo-every'); return { kinds: p.games.map(g => g.type), bad: p.games.map(g => { const T = __T.TYPES[g.type]; const e = T.validate(g.block, Object.assign({}, T.defaults(p), g.options || {})); return e ? g.type + ': ' + e : ''; }).filter(Boolean), bank: !!p.bank, rs: !!(p.runsheet && p.runsheet.blocks.length), mats: (p.materials || []).length }; })()")
    check(sorted(ev_every["kinds"]) == sorted(kinds), "Every game holds one saved game of each kind (%d)" % len(kinds))
    check(not ev_every["bad"], "every seeded game is valid: %s" % ev_every["bad"])
    check(ev_every["bank"] and ev_every["rs"] and ev_every["mats"] == 1, "seed has a word bank, a run sheet and a materials entry")
    pair = ev(t, "__T.PACKS.find(p => p.id === 'demo-pair-every').games.filter(g => ['bingo', 'typhoon'].includes(g.type)).map(g => g.type + ':' + (g.options.cards || g.block))")
    check("bingo:Pip, Pat" in pair and "typhoon:Pip\nPat" in pair, "Demo Pair's seed gives Pip and Pat a bingo card and a Typhoon line each: %s" % pair)
    # ---- the stripe and the class link, every kind
    t.click(".sbx-stu [data-a=open][data-id=demo-every]"); t.wait_for_timeout(500)
    if t.locator("[data-a=nav-games]").count() and ev(t, "__T.UI.view") != "pack": t.click("[data-a=nav-games]"); t.wait_for_timeout(300)
    check(t.locator(".sbx-stripe").count() == 1, "the 🧪 stripe shows on a test lesson (teacher side)")
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl"); url = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    s = student(ctx, url, errs); s.wait_for_timeout(1000)
    games = ev(t, "__T.PACKS.find(p => p.id === 'demo-every').games.map(g => [g.id, g.type])")
    ok = []; bad = []
    for gid, ty in games:
        if ev(t, "__T.UI.view") == "play": t.click("[data-a=lesson]"); t.wait_for_timeout(300)
        t.evaluate("id => { const b = document.querySelector('[data-a=play][data-g=\"' + id + '\"]') || document.querySelector('[data-a=play-resume][data-k$=\"|' + id + '\"]'); b.click(); }", gid)
        try:
            s.wait_for_function("id => window.__T && __T.UI.view === 'play' && __T.UI.run && __T.UI.run.gameId === id && document.querySelector('#app main.stage') && document.querySelector('#app main.stage').children.length > 0", arg=gid, timeout=5000)
            ok.append(ty)
        except Exception:
            bad.append("%s (student on %s)" % (ty, ev(s, "__T.UI.run ? __T.UI.run.type : __T.UI.view")))
        if s.locator(".sbx-stripe").count(): bad.append(ty + ": stripe on the student's page")
    check(not bad and sorted(ok) == sorted(kinds), "every kind follows the one class link onto the student's page (%d): failed %s" % (len(ok), bad))
    tx = s.evaluate("document.documentElement.outerHTML")
    check("Q71" not in tx, "")
    s.close()
    # ---- a student page from an older build: reloads once, then follows; if still old, the teacher is told
    OLD = lg.APP.replace('var APP_B = "', 'var APP_B = "0', 1).replace("window.__T={", "delete TYPES.td; LIVE_TYPES.pop(); window.__T={", 1)
    for always_old in (False, True):
        loads = []
        s = ctx.new_page(); s.on("pageerror", lambda e: errs.append("S: " + str(e)))
        def mk(loads, always_old):
          def h(r):
            u = r.request.url
            if u.endswith("/app/supabase.js"): return r.fulfill(body=lg.MOCK, content_type="application/javascript")
            if "/lesson-games/" in u: loads.append(1); return r.fulfill(body=OLD if (always_old or len(loads) == 1) else lg.APP, content_type="text/html")
            return r.abort()
          return h
        s.route("**/*", mk(loads, always_old)); s.goto(url); s.wait_for_timeout(1500)
        if ev(t, "__T.UI.view") == "play": t.click("[data-a=lesson]"); t.wait_for_timeout(300)
        t.wait_for_timeout(300)
        bar = t.inner_text("#clsBar")
        td = [g for g, ty in games if ty == "td"][0]
        t.evaluate("id => { const b = document.querySelector('[data-a=play][data-g=\"' + id + '\"]') || document.querySelector('[data-a=play-resume][data-k$=\"|' + id + '\"]'); b.click(); }", td); t.wait_for_timeout(2500)
        on = ev(s, "__T.UI.run ? __T.UI.run.type : __T.UI.view")
        if not always_old:
            check(len(loads) == 2 and on == "td" and "different versions" not in bar, "an older student page reloads itself once and then follows Tower Defence (loads %d, on %s)" % (len(loads), on))
        else:
            t.wait_for_timeout(5000)
            check(len(loads) == 2, "a page that stays old reloads only once (%d loads)" % len(loads))
            check("different versions" in bar, "the class bar tells the teacher the student's page is a different version: %s" % bar)
            check("hasn’t opened this game" in t.inner_text("#livePill"), "the pill says the student's screen hasn't opened the game: %s" % t.inner_text("#livePill"))
        s.close()
    # ---- a test lesson's play screen: stripe on the teacher's, not the student's (above); fit
    for vw in [{"width":1180,"height":820}, {"width":390,"height":844}, {"width":1440,"height":900}]:
        t.set_viewport_size(vw)
        if ev(t, "__T.UI.view") == "play": t.click("[data-a=lesson]"); t.wait_for_timeout(200)
        t.click("[data-a=home]"); t.wait_for_timeout(200); t.click("[data-a=tst-open-page]"); t.wait_for_timeout(300)
        o = t.evaluate("() => { const W = innerWidth, out = []; if (document.documentElement.scrollWidth > W + 1) out.push('page wide'); document.querySelectorAll('#app *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.right > W + 2 || r.left < -2)) out.push(e.className + ' ' + Math.round(r.left) + '-' + Math.round(r.right)); }); return out.slice(0, 5); }")
        check(not o, "test page fits the width at %dx%d: %s" % (vw["width"], vw["height"], o))
        t.screenshot(path=HERE + "/shots/sandbox_%d.png" % vw["width"])
    check(not errs, "no page errors %s" % errs[:3])
done()
