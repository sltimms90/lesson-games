import json, sys, base64
from playwright.sync_api import sync_playwright
from lg import menu_click, quick, add_game, scope, picker, tile
ROOT = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "../.."))
MOCK = open("mock-supabase.js").read()
APP = open(ROOT + "/app/index.html", encoding="utf-8").read()
APP = __import__("re").sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>', "", APP)  # the test hook changes the script, so its hash no longer matches
HOOK = "window.__T={setHomeDay:function(d){HOMEDAY=d;render()},get STORE(){return STORE},slinkData:slinkData,packData:packData,get SLINK_TYPES(){return SLINK_TYPES}};\n"
APP = APP.replace("if(STUDENT_PAGE) startStudent();", HOOK + "if(STUDENT_PAGE) startStudent();")
BOARD = open("board.b64").read(); TOK = open("tok.b64").read(); JPG = open("board.jpg","rb").read()
fails = []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: fails.append(m)
def go_lesson(pg, title, who=None, timeout=8000):
    """Home lists only today's lessons; anything else is reached through the Students list (folded)."""
    pg.wait_for_selector("#stuSec, .head h2", timeout=timeout)
    if pg.locator(".head h2", has_text=title).count(): return   # the app reopened on this lesson
    if not pg.locator("#stuSec").count():
        if not pg.locator("[data-a=home]").count(): pg.click("[data-a=student]"); pg.wait_for_timeout(200)
        pg.click("[data-a=home]"); pg.wait_for_selector("#stuSec", timeout=timeout)
    if not pg.locator(".daybar ~ .list >> text=" + title).count():
        if not pg.evaluate("document.getElementById('stuSec').open"): pg.click("#stuSec > summary")
        pg.click("#stuSec [data-a=student]:has-text('%s')" % (who or title.split(" · ")[0])); pg.wait_for_timeout(250)
    pg.click("text=" + title)
def route(page, imgs):
    def h(r):
        u = r.request.url
        if "/storage/v1/object/public/" in u: imgs.append(u); return r.fulfill(body=JPG, content_type="image/jpeg")
        if u.endswith("/app/supabase.js"): return r.fulfill(body=MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=APP, content_type="text/html")
        return r.abort()
    page.route("**/*", h)
seed = {"packs":{}, "results":{}, "students":{}, "boards":{}, "sheets":{}}
pack = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","updatedAt":"2026-11-14T00:00:00Z","games":[
  {"id":"g1","type":"snakes","title":"Castle race","block":"Mia\nTeacher","options":{"boardId":"b_snakes_blue","auto":True}},
  {"id":"g2","type":"bingo","title":"Town bingo","block":"\n".join(["castle","tower","bridge","market","river","church","school","park","bank","shop","house","road","hill","farm","lake","zoo","cafe"]),
   "options":{"size":4,"call":"word","claim":True,"cards":"Mia","code":"MI9","show":"all","self":False,"lines":1}},{"id":"g3","type":"hilo","title":"Card reward","block":"Mia\nTeacher","options":{}}]}
seed["packs"]["mia-lp9"] = {"id":"mia-lp9","data":pack}
seed["boards"]["b_snakes_blue"] = {"id":"b_snakes_blue","data":{"id":"b_snakes_blue","name":"Blue","img":BOARD,"w":600,"h":600,"rows":10,"cols":10,"l":0,"r":0,"t":0,"b":0,"zig":True,"start":"bl","jumps":"3-22\n17-4","updatedAt":"x"}}
seed["students"]["mia"] = {"id":"mia","data":{"id":"mia","name":"Mia","token":TOK}}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180,"height":820})
    pg = ctx.new_page(); errs=[]; pg.on("pageerror", lambda e: errs.append(str(e))); imgs=[]
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}}))
    route(pg, imgs); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    pg.wait_for_selector("#stuSec", timeout=8000)
    check("snakes" in pg.evaluate("__T.SLINK_TYPES") and "bingo" in pg.evaluate("__T.SLINK_TYPES"), "both types offer a student link")
    go_lesson(pg, "Mia · LP9"); pg.wait_for_timeout(400)
    check(pg.locator("[data-a=slink][data-g=g1]").count() == 1 and pg.locator("[data-a=slink][data-g=g2]").count() == 1, "Student link buttons shown on the lesson page")
    menu_click(pg, "[data-a=slink][data-g=g1]"); pg.wait_for_selector("#slinkUrl", timeout=5000)
    snurl = pg.input_value("#slinkUrl")
    ups = pg.evaluate("__MOCK.uploads")
    check(len(ups) == 2 and ups[0]["bk"] == "game-pictures" and ups[0]["type"] == "image/jpeg" and ups[1]["type"] == "image/png", "board + Mia's token uploaded: %s" % [(u["path"],u["type"]) for u in ups])
    check(len(snurl) < 3000, "snakes link stays short: %d chars" % len(snurl))
    pg.click("[data-a=slink-close]"); menu_click(pg, "[data-a=slink][data-g=g1]"); pg.wait_for_selector("#slinkUrl")
    check(len(pg.evaluate("__MOCK.uploads")) == 2, "second link reuses the uploaded pictures")
    pg.click("[data-a=slink-close]"); menu_click(pg, "[data-a=slink][data-g=g2]"); pg.wait_for_selector("#slinkUrl")
    bgurl = pg.input_value("#slinkUrl"); check(len(bgurl) < 3000, "bingo link %d chars" % len(bgurl))
    check(not errs, "teacher errors %s" % errs)
    pg.close()
    # student: snakes
    pg = ctx.new_page(); route(pg, []); pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":seed, "session":{"user":{"email":"t@x"}}})); pg.goto("https://sltimms90.github.io/lesson-games/app/"); go_lesson(pg, "Mia · LP9"); pg.wait_for_timeout(300)
    menu_click(pg, "[data-a=slink][data-g=g3]"); pg.wait_for_selector("#slinkUrl"); hlurl = pg.input_value("#slinkUrl"); pg.close()
    for name, url in [("snakes", snurl), ("bingo", bgurl), ("hilo", hlurl)]:
        pg = ctx.new_page(); e=[]; pg.on("pageerror", lambda x: e.append(str(x))); imgs=[]; reqs=[]
        pg.on("request", lambda r: reqs.append(r.url))
        route(pg, imgs); pg.goto("https://sltimms90.github.io/lesson-games/"); pg.goto(url); pg.reload()
        pg.wait_for_selector("[data-a=s-start]", timeout=6000); pg.click("[data-a=s-start]"); pg.wait_for_timeout(800)
        pg.screenshot(path="stu_%s_1.png" % name)
        if name == "snakes":
            check(pg.locator("#snBoardEl > img").count() == 1 and "game-pictures" in pg.get_attribute("#snBoardEl > img", "src"), "student sees your board picture")
            check(any("game-pictures" in u for u in imgs), "board fetched from the picture folder")
            btns = pg.eval_on_selector_all("[data-a]", "els => els.map(e => e.getAttribute('data-a'))")
            print("  buttons:", sorted(set(btns)))
        else:
            btns = pg.eval_on_selector_all("[data-a]", "els => els.map(e => e.getAttribute('data-a'))")
            print("  buttons:", sorted(set(btns)))
        check(not any(x in u for u in reqs for x in ["/rest/v1/", "/auth/v1/"]), name + ": no database or sign-in requests")
        check(pg.evaluate("document.documentElement.scrollHeight <= innerHeight + 1 && document.documentElement.scrollWidth <= innerWidth"), name + ": fits iPad landscape")
        check(not e, name + " errors %s" % e)
        pg.close()
    b.close()
print("%d failures" % len(fails))
