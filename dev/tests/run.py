import json, sys, time
from playwright.sync_api import sync_playwright
ROOT = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "../.."))
MOCK = open("/home/claude/work/test/mock-supabase.js").read()
APP = open(ROOT + "/app/index.html", encoding="utf-8").read()
HOOK = "window.__T={get STORE(){return STORE},get STUDENT_PAGE(){return STUDENT_PAGE},get SB_MODE(){return SB_MODE},packData:packData,studentLinkData:studentLinkData};\n"
assert APP.count("if(STUDENT_PAGE) startStudent();") == 1
APP = APP.replace("if(STUDENT_PAGE) startStudent();", HOOK + "if(STUDENT_PAGE) startStudent();")
STU = open(ROOT + "/index.html", encoding="utf-8").read()
fails = []
def check(c, msg):
    print(("PASS " if c else "FAIL ") + msg); 
    if not c: fails.append(msg)

def route(page, student_html=APP):
    def h(r):
        u = r.request.url
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/app/" in u: return r.fulfill(body=APP, content_type="text/html")
        if "/lesson-games/" in u: return r.fulfill(body=student_html, content_type="text/html")
        return r.abort()
    page.route("**/*", h)

seed = {"packs":{}, "results":{}, "students":{}, "boards":{}, "sheets":{}}
for i in range(3):
    pid = "p%d" % i
    seed["packs"][pid] = {"id":pid, "data":{"id":pid, "title":"Seed lesson %d" % i, "date":"2026-11-1%d" % i, "games":[], "updatedAt":"2026-11-1%dT00:00:00Z" % i}}
seed["students"]["mia"] = {"id":"mia", "data":{"id":"mia", "name":"mia"}}
seed["results"]["r1"] = {"id":"r1", "data":{"id":"r1", "packId":"p1", "student":"mia", "at":"2026-11-12T01:00:00Z"}}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}, accept_downloads=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed}))
    route(pg)
    pg.goto("https://sltimms90.github.io/lesson-games/app/")
    pg.wait_for_selector("#sbEmail", timeout=8000)
    check("Sign in" in pg.inner_text("#app"), "signed-out visitor sees the sign-in screen")
    check("Seed lesson" not in pg.content(), "no lesson data on the sign-in screen")
    pg.fill("#sbEmail", "teacher@example.com"); pg.click("[data-a=sb-send]")
    pg.wait_for_selector("#sbCode")
    otp = pg.evaluate("__MOCK.otp")
    check(otp["options"]["emailRedirectTo"] == "https://sltimms90.github.io/lesson-games/app/", "magic link returns to /app/")
    pg.fill("#sbCode", "000000"); pg.click("[data-a=sb-code]"); pg.wait_for_timeout(300)
    check("didn’t work" in pg.inner_text("#app"), "wrong code shows an error")
    pg.fill("#sbCode", "123456"); pg.click("[data-a=sb-code]")
    pg.wait_for_selector("text=Seed lesson 2", timeout=8000)
    check(pg.locator(".list li").count() == 3, "three seeded lessons listed")
    check("Saved online" in pg.inner_text("#status"), "status pill says Saved online")
    check(pg.evaluate("__MOCK.created.opts.auth.persistSession") is True, "session persists")
    # realtime from another device
    pg.evaluate("""__MOCK.remote('packs','INSERT',{id:'p9',data:{id:'p9',title:'From the planning chat',date:'2026-11-14',games:[],updatedAt:'2026-11-14T00:00:00Z'}})""")
    pg.wait_for_selector("text=From the planning chat", timeout=3000); check(True, "Realtime insert appears without reload")
    pg.evaluate("__MOCK.remote('packs','DELETE',{id:'p0'})"); pg.wait_for_timeout(200)
    check("Seed lesson 0" not in pg.inner_text("#app"), "Realtime delete removes the lesson")
    # writes through the adapter, per-document queue order
    pg.evaluate("""(async function(){ var p = {id:'q1',title:'A',games:[],date:'2026-11-14',updatedAt:new Date().toISOString()};
      __T.STORE.savePack(p); p = Object.assign({}, p, {title:'B'}); await __T.STORE.savePack(p); })()""")
    check(pg.evaluate("__MOCK.db.packs.q1.data.title") == "B", "queued writes land in order (last write wins)")
    pg.evaluate("__T.STORE.deletePack('q1')"); pg.wait_for_timeout(100)
    check(pg.evaluate("!__MOCK.db.packs.q1"), "deletePack removes the row")
    pg.evaluate("__MOCK.failNext = true"); 
    r = pg.evaluate("__T.STORE.saveResult({id:'r2',packId:'p1',at:'x'}).then(()=>'ok',e=>'err:'+e.message)")
    check(r == "err:network down", "write errors reach the caller")
    # backup
    with pg.expect_download() as d: pg.click("[data-a=backup]")
    data = json.load(open(d.value.path()))
    check(data["format"] == "lesson-games-backup" and len(data["collections"]["packs"]) == 3 and len(data["collections"]["students"]) == 1, "backup file has the live data")
    # restore (into an emptied db)
    pg.evaluate("for (const t in __MOCK.db) __MOCK.db[t] = {}")
    big = {"format":"lesson-games-backup","v":1,"collections":{"packs":[{"id":"k%d"%i,"title":"K%d"%i,"games":[],"updatedAt":"2026-01-01"} for i in range(22)],
           "results":[{"id":"x%d"%i,"packId":"k1","at":"2026"} for i in range(66)],"students":[{"id":s} for s in "abcdefghi"],"boards":[{"id":"b1"}],"sheets":[{"id":"s%d"%i,"packId":"k1"} for i in range(3)]}}
    open("/tmp/bk.json","w").write(json.dumps(big))
    pg.once("dialog", lambda dl: dl.accept())
    pg.set_input_files("#restoreFile", "/tmp/bk.json"); pg.wait_for_timeout(800)
    counts = pg.evaluate("Object.fromEntries(Object.entries(__MOCK.db).map(([k,v])=>[k,Object.keys(v).length]))")
    check(counts == {"packs":22,"results":66,"students":9,"boards":1,"sheets":3}, "restore writes 22/66/9/1/3: %s" % counts)
    # landscape iPad: home has no horizontal overflow
    check(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), "no sideways scrolling at iPad landscape")
    # sign out
    pg.click("[data-a=sb-signout]"); pg.wait_for_selector("#sbEmail", timeout=3000)
    check("K1" not in pg.inner_text("#app"), "sign out returns to sign-in screen")
    check(not errs, "no page errors: %s" % errs)
    pg.close()

    # a signed-in stranger
    pg = ctx.new_page(); errs2 = []; pg.on("pageerror", lambda e: errs2.append(str(e)))
    pg.add_init_script("window.__MOCK = {db:%s, session:{user:{email:'someone@else.com'}}, teacher:false};" % json.dumps(seed))
    route(pg); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    pg.wait_for_selector("text=can’t open the lessons", timeout=5000)
    check("Seed lesson" not in pg.content(), "stranger sees no lessons")
    pg.close()

    # student page at the root and student links into /app/
    for url in ["https://sltimms90.github.io/lesson-games/", "https://sltimms90.github.io/lesson-games/app/#s=abc"]:
        pg = ctx.new_page(); e3 = []; pg.on("pageerror", lambda e: e3.append(str(e)))
        reqs = []; pg.on("request", lambda r: reqs.append(r.url))
        route(pg); pg.goto(url); pg.wait_for_timeout(1200)
        mode = pg.evaluate("[__T.STUDENT_PAGE, __T.SB_MODE]")
        check(mode[0] is True, url + " runs as the student page")
        check(not any(u.endswith("supabase.js") for u in reqs), url + " never loads Supabase")
        check("Sign in" not in pg.inner_text("body") and "Lessons" not in pg.inner_text("body"), url + " shows no teacher screens")
        check(not e3, url + " no page errors %s" % e3)
        pg.screenshot(path="/home/claude/work/test/student_%d.png" % (1 if url.endswith("/") else 2))
        pg.close()
    # end-to-end: link made by the teacher build, played on the student page at iPad landscape
    pg = ctx.new_page(); e4 = []; pg.on("pageerror", lambda e: e4.append(str(e)))
    route(pg); pg.goto("https://sltimms90.github.io/lesson-games/"); pg.wait_for_timeout(500)
    url = pg.evaluate("""(async function(){ var p = {id:'pk1', title:'Castles', student:'mia', games:[{id:'g1', type:'hangman', block:'castle | a king lives here\\nbridge'}]};
        var c = await __T.packData(__T.studentLinkData(p, p.games[0])); return 'https://sltimms90.github.io/lesson-games/#s=' + c; })()""")
    reqs = []; pg.on("request", lambda r: reqs.append(r.url))
    pg.goto(url); pg.reload(); pg.wait_for_selector("[data-a=s-start]", timeout=5000)
    check("Hangman" in pg.inner_text("#app"), "student link opens the game")
    pg.click("[data-a=s-start]"); pg.wait_for_timeout(600)
    pg.screenshot(path="/home/claude/work/test/student_play.png")
    check(pg.evaluate("document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth"), "game fits iPad landscape without scrolling")
    check(not any("supabase" in u for u in reqs), "student game makes no Supabase requests")
    check(not e4, "student game no page errors %s" % e4)
    pg.close()
    b.close()
print("\n%d failures" % len(fails)); sys.exit(1 if fails else 0)
