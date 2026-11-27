"""27 Nov: guest accounts and the showcase school.
Sam's 🧪 Test page: Reset showcase seeds four made-up students (showcase:true) with ~3 past lessons and one today each; Reset
sandbox and Reset showcase never touch each other's rows or a real student's. On Sam's side the showcase stays out of the day
list, Students, Phase B, missed words, Keeps coming up, progress and Kept games (backups keep it). Preview as guest shows the app
as a guest sees it. A guest (an email on the guest list; mock-supabase.js copies dev/sql/guests.sql's rules) sees only the
showcase, as ordinary students: the day list, Phase B owed, missed words, progress, run sheets; a thin "Guest preview" stripe
with Reset demo (asked inline), no Your data, no 🧪 Test, no teacher settings saved to Sam's row, no Sam's email. The class
link works for a showcase lesson. A signed-in stranger sees nothing. The real database's rules are tested by
dev/sql/guests_test.sql (run it with the Supabase SQL editor or MCP: it rolls itself back)."""
import json, datetime
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get STUDENTS(){return STUDENTS},get SHEETS(){return SHEETS},get PHASEB(){return PHASEB},get BOARDS(){return BOARDS},get GUEST(){return GUEST},missedWords:missedWords,stuckWords:stuckWords,progressData:progressData,pbAll:pbAll,backupData:backupData,keptList:keptList,students:students,tset:tset,tsetSave:tsetSave,getPack:getPack,", 1)
TODAY = datetime.date.today().isoformat(); YDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
SC_NAMES = ["Leo", "Mina", "Ken & Ivy", "Grace"]
H = {"id":"g1","type":"hangman","title":"Words","block":"cat | a pet\ndog | it barks\nfish | it swims","options":{}}
miss = [{"item":"cat","ok":False,"note":""},{"item":"dog","ok":True,"note":""}]
real = [{"id":"mia-lp8","student":"Mia","lp":8,"title":"Mia · LP8","date":YDAY,"updatedAt":"x","games":[H],"notes":"REAL-SECRET-NOTE"},
        {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":TODAY,"updatedAt":"x","games":[H]},
        {"id":"demo-lp1","student":"Demo","lp":1,"title":"Demo · LP1","date":TODAY,"updatedAt":"x","games":[H]}]
results = [{"id":"r-mia","packId":"mia-lp8","gameId":"g1","type":"hangman","title":"Words","summary":"REAL-SECRET-RESULT","at":YDAY + "T10:00:00Z","items":miss,"student":"Mia"},
           {"id":"r-demo","packId":"demo-lp1","gameId":"g1","type":"hangman","title":"Words","summary":"Hangman","at":TODAY + "T09:00:00Z","items":miss,"student":"Demo"}]
db0 = seed_db(real, students=[{"id":"mia","name":"Mia","notes_doc":"1RealNotesDocId_abcdefgh","paused":{"td":{"id":"k1","type":"td","title":"Towers","started":YDAY,"st":{"wave":2},"hid":{}}},"updatedAt":"x"},
                              {"id":"demo","name":"Demo","updatedAt":"x"},
                              {"id":"~teacher","name":"","tyBonus":"SAM-OWN-SETTING","updatedAt":"x"}], results=results)
db0["sheets"]["mia-lp8"] = {"id":"mia-lp8","data":{"id":"mia-lp8","packId":"mia-lp8","marks":{"x":"y"},"summary":"REAL-SECRET-SHEET"}}
db0["phaseb"] = {}
def ev(pg, js, arg=None): return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
def sc_rows(pg): return ev(pg, "(() => { const d = __MOCK.db, o = {}; for (const t in d) for (const k in d[t]) { const r = d[t][k], id = r.id || r.pack_id, data = r.data || r; if (String(id).startsWith('~sc-') || (t === 'students' && data.showcase)) o[t + '/' + id] = JSON.stringify(r); } return o; })()")
def other_rows(pg): return ev(pg, "(() => { const d = __MOCK.db, o = {}; for (const t in d) for (const k in d[t]) { const r = d[t][k], id = r.id || r.pack_id, data = r.data || r; if (!(String(id).startsWith('~sc-') || (t === 'students' && data.showcase) || (t === 'boards' && data.showcase))) o[t + '/' + id] = JSON.stringify(r); } return o; })()")
def wide(pg): return ev(pg, "(() => { const W = innerWidth, out = []; if (document.documentElement.scrollWidth > W + 1) out.push('page wide'); document.querySelectorAll('#app *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.right > W + 2 || r.left < -2) && !e.closest('.overlay')) out.push(e.className + ' ' + Math.round(r.left) + '-' + Math.round(r.right)); }); return out.slice(0, 5); })()")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    t = teacher(ctx, db0, errs); t.on("dialog", lambda d: (errs.append("browser dialog: " + d.message), d.dismiss()))
    acct = []
    t.route("**/functions/v1/guest-account", lambda r: (acct.append(json.loads(r.request.post_data or "{}")), r.fulfill(body='{"ok":true,"created":true}', content_type="application/json")))
    t.wait_for_selector("#stuSec", timeout=8000)
    # ---- Sam: the Test page, both resets
    t.click("[data-a=tst-open-page]"); t.wait_for_selector("[data-a=tst-sc-reset]", timeout=4000)
    check(t.locator(".sc-sec [data-a=tst-preview]").count() == 1 and t.locator(".sc-sec #gstEmail").count() == 1, "the Test page has Preview as guest, Reset showcase and the Guests list")
    t.click("[data-a=tst-reset]"); t.click("[data-a=tst-reset-go]"); t.wait_for_timeout(1200)
    before = other_rows(t)
    t.click("[data-a=tst-sc-reset]"); t.wait_for_timeout(100)
    check(t.locator(".sc-ask [data-a=tst-sc-go]").count() == 1, "Reset showcase asks inline first")
    t.click("[data-a=tst-sc-no]"); t.wait_for_timeout(100)
    check(not sc_rows(t), "Cancel: nothing seeded")
    t.click("[data-a=tst-sc-reset]"); t.click("[data-a=tst-sc-go]")
    t.wait_for_function("Object.keys(__MOCK.db.packs).filter(k => k.startsWith('~sc-')).length === 16 && Object.keys(__MOCK.db.sheets).filter(k => k.startsWith('~sc-')).length === 12 && Object.keys(__MOCK.db.phaseb).length === 10", timeout=8000)
    t.wait_for_timeout(300)
    check(other_rows(t) == before, "Reset showcase: every real and sandbox row is exactly as it was")
    st = ev(t, "JSON.parse(JSON.stringify(__MOCK.db.students))")
    check(all(st[i]["data"].get("showcase") is True and not st[i]["data"].get("test") for i in ["leo", "mina", "ken-ivy", "grace"]), "four showcase students, none of them test")
    check(not st["mia"]["data"].get("showcase") and not st["demo"]["data"].get("showcase"), "real and test students aren't showcase")
    packs = ev(t, "Object.values(__MOCK.db.packs).map(r => r.data).filter(p => p.id.startsWith('~sc-'))")
    by = {}
    for pk in packs: by.setdefault(pk["student"], []).append(pk)
    check(sorted(by) == sorted(SC_NAMES) and all(len(v) == 4 and sum(1 for x in v if x["date"] == TODAY) == 1 and sum(1 for x in v if x["date"] < TODAY) == 3 for v in by.values()), "each showcase student: three past lessons and one today (dates from today)")
    check(all(x["id"].startswith("~sc-") and x.get("runsheet") for x in packs), "showcase lesson ids start ~sc-; every lesson has a run sheet")
    mats = [m for x in packs for m in x.get("materials", [])]
    check(mats and all(m["id"].startswith("showcase-") for m in mats) and not any(x.get("plan") and not x["plan"]["docId"].startswith("showcase-") for x in packs), "materials and plans are showcase ids (placeholder page), never Drive files")
    check(not any("notes_doc" in st[i]["data"] for i in ["leo", "mina", "ken-ivy", "grace"]), "notes doc links left empty")
    bd = ev(t, "__MOCK.db.boards['~sc-board'] && __MOCK.db.boards['~sc-board'].data")
    check(bd and bd["showcase"] is True and bd["img"].startswith("https://prglfopvovvxhzrejhzc.supabase.co/storage/v1/object/public/game-pictures/"), "the showcase board's picture is its public address (no upload needed by a guest)")
    sh = ev(t, "Object.values(__MOCK.db.sheets).map(r => r.data).filter(s => s.id.startsWith('~sc-'))")
    check(len(sh) == 12 and all(s["finished"] and not s["gaps"] and s["marks"].get("end.fin") for s in sh), "past run sheets: finished, every line marked")
    typed = [s for s in sh if any(k.startswith("end.") and k not in ("end.fin", "end.spine", "end.plan") and not k.startswith("end.energy") and v for k, v in s["marks"].items()) or any(k.endswith(".m") for k in s["marks"])]
    check(len(typed) == 12, "every past run sheet has typed feedback lines (%d)" % len(typed))
    check(not any(s["id"] for s in sh if any(x["id"] == s["id"] and x["date"] == TODAY for x in packs)), "today's run sheets are unmarked")
    # sandbox reset never touches the showcase
    scb = sc_rows(t)
    t.click("[data-a=tst-reset]"); t.click("[data-a=tst-reset-go]"); t.wait_for_timeout(1200)
    check(sc_rows(t) == scb, "Reset sandbox leaves every showcase row as it was")
    check(ev(t, "!!__MOCK.db.packs['demo-every'] && !!__MOCK.db.packs['mia-lp9']"), "…and still resets the sandbox")
    # ---- Sam's side: the showcase is kept out
    t.click("[data-a=home]"); t.wait_for_timeout(300); home = t.inner_text("#app")
    check("Mia · LP9" in home and not any(n + " · LP" in home for n in SC_NAMES), "Sam's day list: real lessons, no showcase")
    t.click("#stuSec > summary"); t.wait_for_timeout(150)
    check(not any(t.locator("#stuSec [data-a=student][data-s='%s']" % n).count() for n in SC_NAMES), "Sam's Students list has no showcase student")
    A = ev(t, "(() => { const A = __T.pbAll(); return { owed: A.owed.map(o => o.p.id), look: A.look.map(o => o.p.id), done: A.done.map(x => x.row.pack_id) }; })()")
    check(not any(i.startswith("~sc-") for i in A["owed"] + A["look"] + A["done"]), "Sam's Phase B (owed, needs a look, done lately) has no showcase lesson: %s" % A)
    check(ev(t, "__T.PACKS.filter(p => p.id.startsWith('~sc-')).every(p => __T.missedWords(p).length === 0 && __T.stuckWords(p).length === 0)"), "missed words / Keeps coming up: nothing for showcase lessons on Sam's side")
    check(ev(t, "['Leo','Mina','Ken & Ivy','Grace'].every(n => __T.progressData(n).lessons.length === 0)"), "progress patterns leave the showcase out")
    check(ev(t, "__T.missedWords(__T.getPack('mia-lp9')).length") == 1, "…while a real student's are as before")
    check(not any(n in ev(t, "__T.students()") for n in SC_NAMES), "New lesson's student list has no showcase student")
    bk = ev(t, "JSON.stringify(__T.backupData().collections)")
    check('"~sc-leo-lp23"' in bk and '"showcase":true' in bk, "backups include the showcase")
    check(ev(t, "__T.BOARDS['~sc-board']") is None, "the showcase board isn't in Sam's own board list")
    # ---- Guests list
    t.click("[data-a=tst-open-page]"); t.wait_for_selector("#gstEmail", timeout=3000)
    t.fill("#gstEmail", "Friend@Example.com"); t.click("[data-a=tst-g-add]"); t.wait_for_timeout(500)
    check(ev(t, "__MOCK.guests") == ["friend@example.com"] and acct == [{"email":"friend@example.com"}], "Add guest: on the list, and their sign-in is made (guest-account)")
    check("friend@example.com" in t.inner_text(".sc-sec"), "the list shows the guest")
    t.fill("#gstEmail", "not-an-email"); t.click("[data-a=tst-g-add]"); t.wait_for_timeout(200)
    check("full email" in t.inner_text(".sc-sec") and ev(t, "__MOCK.guests.length") == 1, "a bad email is refused")
    for vw in [{"width":1180,"height":820}, {"width":390,"height":844}, {"width":1440,"height":900}]:
        t.set_viewport_size(vw); t.wait_for_timeout(150)
        check(not wide(t), "Guests list fits at %dx%d: %s" % (vw["width"], vw["height"], wide(t)))
        t.locator(".sc-sec").screenshot(path=HERE + "/shots/showcase_guests_%d.png" % vw["width"])
    t.set_viewport_size({"width":1180, "height":820})
    t.click(".gl-row [data-a=tst-g-ask]"); t.wait_for_timeout(100)
    check(t.locator(".gl-ask [data-a=tst-g-del]").count() == 1, "Remove asks inline")
    t.click(".gl-ask [data-a=tst-g-no]"); t.wait_for_timeout(100)
    # ---- Preview as guest
    t.click("[data-a=tst-preview]"); t.wait_for_timeout(500); home = t.inner_text("#app")
    check(t.locator(".gst-stripe [data-a=gst-exit]").count() == 1 and t.locator("[data-a=tst-open-page]").count() == 0 and t.locator("[data-a=backup]").count() == 0, "preview: the guest stripe (with Exit preview), no 🧪 Test, no Your data")
    check(all(n + " · LP" in home for n in SC_NAMES) and "Mia" not in home and "Demo" not in home, "preview: today's four showcase lessons, nothing real or sandbox")
    check(ev(t, "__T.PACKS.every(p => p.id.startsWith('~sc-')) && Object.keys(__T.STUDENTS).sort().join() === 'grace,ken-ivy,leo,mina'"), "preview: only showcase data in the app")
    check(ev(t, "__T.tset().tyBonus") is None, "preview: Sam's teacher settings aren't there")
    ev(t, "__T.tsetSave({ tyBonus:'PREVIEW-CHANGE' })"); t.wait_for_timeout(200)
    check(ev(t, "__MOCK.db.students['~teacher'].data.tyBonus") == "SAM-OWN-SETTING", "preview: changing a teacher setting never touches Sam's own")
    t.click("[data-a=gst-exit]"); t.wait_for_timeout(300)
    check(ev(t, "__T.UI.view") == "test" and ev(t, "__T.tset().tyBonus") == "SAM-OWN-SETTING" and ev(t, "!!__T.getPack('mia-lp9')"), "Exit preview: back to the Test page and Sam's own data")
    dbS = ev(t, "JSON.parse(JSON.stringify(__MOCK.db))"); t.close()

    # ---- a guest signs in to that database
    g = ctx.new_page(); g.on("pageerror", lambda e: errs.append("G: " + str(e))); g.on("dialog", lambda d: (errs.append("browser dialog: " + d.message), d.dismiss()))
    g.add_init_script("window.__MOCK = %s;" % json.dumps({"db":dbS, "session":{"user":{"email":"friend@example.com"}}, "teacher":False, "guest":True}))
    route(g); g.goto("https://sltimms90.github.io/lesson-games/app/"); g.wait_for_selector("#stuSec", timeout=8000); g.wait_for_timeout(400)
    html = g.inner_html("#app") + g.inner_text("body"); home = g.inner_text("#app")   # what's rendered (the page's script holds the sandbox seed's names)
    check(ev(g, "__T.GUEST") is True and g.locator(".gst-stripe [data-a=gst-reset]").count() == 1 and g.locator("[data-a=gst-exit]").count() == 0, "guest: signed in, the Guest preview stripe with Reset demo")
    check(all(n + " · LP" in home for n in SC_NAMES), "guest: today's four lessons on the day list")
    found = [x for x in ["REAL-SECRET", "Mia", "Demo", "1RealNotesDocId", "SAM-OWN-SETTING", "t@x"] if x in html]
    check(not found, "guest: nothing real, sandbox or Sam's anywhere on the page: %s" % [(x, html[max(0, html.find(x) - 80):html.find(x) + 40]) for x in found])
    check(ev(g, "__T.PACKS.length === 16 && __T.RESULTS.every(r => r.packId.startsWith('~sc-')) && Object.keys(__T.SHEETS).every(k => k.startsWith('~sc-')) && Object.keys(__T.BOARDS).join() === '~sc-board'"), "guest: the app holds only showcase lessons, results, run sheets and the showcase board")
    check(g.locator("[data-a=tst-open-page]").count() == 0 and g.locator("[data-a=backup]").count() == 0 and g.locator("[data-a=restore]").count() == 0 and g.locator("[data-a=sb-signout]").count() == 1, "guest: no 🧪 Test, no backups or restore; Sign out only")
    check(g.locator(".pb-badge").inner_text() == "2" and ev(g, "__T.pbAll().owed.length") == 2, "guest: Phase B owes two lessons (the 📝 badge)")
    g.click("[data-a=pb-open]"); g.wait_for_timeout(300)
    check(g.locator("#pbOwed .pb-row").count() == 2 and ev(g, "__T.pbAll().done.length") >= 5, "guest: the Phase B screen lists two owed and the ones done in the last 14 days")
    g.click("[data-a=home]"); g.wait_for_timeout(200); g.click("#stuSec > summary"); g.wait_for_timeout(150)
    check(sorted(ev(g, "[...document.querySelectorAll('#stuSec [data-a=student]')].map(b => b.dataset.s)")) == sorted(SC_NAMES), "guest: the four showcase students on the Students list")
    g.click("#stuSec [data-a=student][data-s='Leo']"); g.wait_for_timeout(300)
    pg_txt = g.inner_text("#app")
    check("Keeps coming up" in pg_txt and "night" in pg_txt and "dream" in pg_txt, "guest: Leo's progress shows Keeps coming up (night, dream)")
    check(all(len(ev(g, "__T.progressData(%s).stuck" % json.dumps(n))) > 0 and len(ev(g, "__T.progressData(%s).lessons" % json.dumps(n))) == 3 for n in SC_NAMES), "guest: every showcase student has progress and words that keep coming up")
    check(ev(g, "__T.PACKS.filter(p => p.date === %s).every(p => __T.missedWords(p).length >= 2)" % json.dumps(TODAY)), "guest: each of today's lessons has missed words for a warm-up")
    check(ev(g, "__T.tset().tyBonus") != "SAM-OWN-SETTING", "guest: no teacher settings of Sam's")
    # writes the database must refuse (mock-supabase.js's copy of the rules)
    bad = ev(g, """async () => { const S = __T.SB, out = {};
      out.realPack = (await S.from('packs').upsert({ id:'mia-lp9', data:{ id:'mia-lp9', student:'Leo' } })).error ? 'refused' : 'WROTE';
      out.newStudent = (await S.from('students').upsert({ id:'mia', data:{ id:'mia', name:'Mia', showcase:true } })).error ? 'refused' : 'WROTE';
      out.testFlag = (await S.from('students').upsert({ id:'leo', data:{ id:'leo', name:'Leo', showcase:true, test:true } })).error ? 'refused' : 'WROTE';
      out.unflag = (await S.from('students').upsert({ id:'leo', data:{ id:'leo', name:'Leo' } })).error ? 'refused' : 'WROTE';
      out.moveLesson = (await S.from('packs').upsert({ id:'~sc-leo-lp23', data:{ id:'~sc-leo-lp23', student:'Mia' } })).error ? 'refused' : 'WROTE';
      const r = __MOCK.db.results[Object.keys(__MOCK.db.results).find(k => k.startsWith('~sc-'))];
      out.moveResult = (await S.from('results').upsert({ id:r.id, data:Object.assign({}, r.data, { packId:'mia-lp8' }) })).error ? 'refused' : 'WROTE';
      await S.from('packs').delete().eq('id', 'mia-lp9'); out.delReal = __MOCK.db.packs['mia-lp9'] ? 'kept' : 'DELETED';
      out.readReal = (await S.from('results').select('id,data')).data.filter(x => !x.id.startsWith('~sc-')).length;
      return out; }""")
    check(bad == {"realPack":"refused", "newStudent":"refused", "testFlag":"refused", "unflag":"refused", "moveLesson":"refused", "moveResult":"refused", "delReal":"kept", "readReal":0}, "guest: writes to real rows, flag changes and moves are refused: %s" % bad)
    # new lesson: only for a showcase student, with a ~sc- id
    g.click("[data-a=home]"); g.wait_for_timeout(200); g.click("[data-a=newpack]"); g.wait_for_timeout(200)
    g.fill("#pStudent", "Mia"); g.fill("#pLp", "10"); g.click("[data-a=savepack]"); g.wait_for_timeout(200)
    check("In the demo" in g.inner_text("#err") and not ev(g, "Object.keys(__MOCK.db.packs).some(k => k.includes('mia-lp10'))"), "guest: New lesson for a non-showcase name is refused")
    g.fill("#pStudent", "Leo"); g.fill("#pLp", "24"); g.click("[data-a=savepack]"); g.wait_for_timeout(500)
    check(ev(g, "!!__MOCK.db.packs['~sc-leo-lp24']"), "guest: New lesson for Leo is saved as a showcase lesson (~sc-leo-lp24)")
    # class link: the friend plays the student's side in another tab
    g.click("[data-a=home]"); g.wait_for_timeout(200); g.click("text=Leo · LP23"); g.wait_for_timeout(400)
    g.click("#clsBar [data-a=clink]"); g.wait_for_selector("#slinkUrl", timeout=4000); url = g.input_value("#slinkUrl"); g.click("[data-a=clink-close]")
    s = student(ctx, url, errs); s.wait_for_timeout(1000)
    g.click("[data-a=nav-games]"); g.wait_for_timeout(300)
    g.click("[data-a=play][data-g=g1]");
    try:
        s.wait_for_function("window.__T && __T.UI.view === 'play' && __T.UI.run && __T.UI.run.gameId === 'g1'", timeout=6000); on = True
    except Exception: on = False
    check(on, "guest: the class link puts the showcase game on the student's screen")
    check(not s.locator(".gst-stripe").count() and "Guest preview" not in s.inner_text("body"), "the student's screen has no guest stripe")
    s.close()
    if ev(g, "__T.UI.view") == "play": g.click("[data-a=lesson]"); g.wait_for_timeout(300)
    # a run sheet tick (a write the guest may make)
    g.click("[data-a=rs-open]"); g.wait_for_timeout(300); g.click(".rs [data-a=rs-tick] >> nth=0"); g.wait_for_timeout(1200)
    check(ev(g, "!!__MOCK.db.sheets['~sc-leo-lp23']"), "guest: a run sheet tick on today's lesson saves")
    # fit: the stripe on home, run sheet, plan header and a play screen
    for vw in [{"width":1180,"height":820}, {"width":390,"height":844}, {"width":1440,"height":900}]:
        g.set_viewport_size(vw)
        if g.locator("[data-a=home]").count(): g.click("[data-a=home]"); g.wait_for_timeout(200)
        h = ev(g, "document.querySelector('.gst-stripe').getBoundingClientRect().height")
        check(not wide(g) and h <= (60 if vw["width"] < 500 else 34), "guest home fits at %dx%d, stripe %dpx: %s" % (vw["width"], vw["height"], h, wide(g)))
        g.screenshot(path=HERE + "/shots/showcase_guest_%d.png" % vw["width"])
        g.click("[data-a=gst-reset]"); g.wait_for_timeout(100)
        check(not wide(g) and g.locator(".gst-ask [data-a=gst-reset-go]").count() == 1, "Reset demo's inline question fits at %dx%d" % (vw["width"], vw["height"]))
        g.click("[data-a=gst-reset-no]"); g.wait_for_timeout(100)
    g.set_viewport_size({"width":1180, "height":820})
    # Reset demo: asks inline, then wipes and re-seeds the showcase only
    oth = other_rows(g)
    g.click("[data-a=gst-reset]"); g.wait_for_timeout(100); g.click("[data-a=gst-reset-go]")
    g.wait_for_function("!__MOCK.db.packs['~sc-leo-lp24'] && !__MOCK.db.sheets['~sc-leo-lp23'] && Object.keys(__MOCK.db.packs).filter(k => k.startsWith('~sc-')).length === 16 && Object.keys(__MOCK.db.phaseb).length === 10", timeout=8000)
    g.wait_for_timeout(400)
    check(other_rows(g) == oth, "guest Reset demo: every real and sandbox row untouched")
    check(ev(g, "Object.keys(__MOCK.db.results).filter(k => k.startsWith('~sc-')).length") == ev(g, "Object.keys(__MOCK.db.results).filter(k => k.startsWith('~sc-')).length") and ev(g, "__T.pbAll().owed.length") == 2, "guest Reset demo: re-seeded (Phase B owes two again)")
    g.close()

    # ---- a signed-in stranger (not on the guest list) sees nothing
    x = ctx.new_page(); x.add_init_script("window.__MOCK = %s;" % json.dumps({"db":dbS, "session":{"user":{"email":"someone@else.com"}}, "teacher":False, "guest":False}))
    route(x); x.goto("https://sltimms90.github.io/lesson-games/app/"); x.wait_for_selector("text=can’t open the lessons", timeout=5000)
    check(not any(n + " · LP" in x.content() for n in SC_NAMES) and "Mia" not in x.inner_text("#app"), "a stranger: no lessons, showcase or real")
    x.close()
    check(not errs, "no page errors %s" % errs[:3])
done()
