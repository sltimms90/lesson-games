"""Homework links (Nov 2026): a Student link's result saves itself through submit_homework, whenever it's played.
The mock's submit_homework makes the same checks as dev/sql/submit_homework.sql; the real function was tested
against the database itself (anon role: wrong token, wrong game, oversized, bad id, no table access)."""
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={slinkData:slinkData,unpackData:unpackData,lessonResultsText:lessonResultsText,go:go,", 1)
games = [
  {"id":"g1","type":"hangman","title":"Castle words","block":"cat | a pet that says meow\ndog | a pet that barks","options":{}},
  {"id":"g2","type":"quiz","title":"Quiz","block":"Which is a verb?\nhappy\n*climb\ntable","options":{"timer":20,"bonus":0}},
]
pack = {"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-18","updatedAt":"x","games":games}
db = seed_db([pack])

def server(t):
    """The teacher's database as it is now: what the student's page talks to."""
    return t.evaluate("JSON.parse(JSON.stringify(__MOCK.db))")
def open_student(ctx, url, dbnow, errs, extra=""):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("S: " + str(e)))
    pg.add_init_script("window.__MOCK = %s;%s" % (json.dumps({"db":dbnow}), extra))
    route(pg); pg.goto(url); pg.wait_for_selector("[data-a=s-start]", timeout=6000)
    return pg
def play_hangman(s):
    s.click("[data-a=s-start]"); s.wait_for_selector(".keys", timeout=5000)
    s.click("[data-a=hm-key][data-c=a]"); s.wait_for_timeout(100)
    for i in range(2):
        s.click("[data-a=hm-show]"); s.wait_for_timeout(150); s.click("[data-a=hm-next]"); s.wait_for_timeout(300)
    s.wait_for_selector(".results", timeout=5000); s.wait_for_timeout(400)
def link_for(t, gid):
    t.click("[data-a=slink][data-g=%s]" % gid); t.wait_for_selector("#slinkUrl", timeout=5000)
    u = t.input_value("#slinkUrl"); return u
def link_data(t, u):
    return t.evaluate("u => __T.unpackData(u.split('#s=')[1])", u)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    home = b.new_context(viewport={"width":390, "height":844}, device_scale_factor=2)   # the student at home: no live channel to the teacher
    t = teacher(ctx, db, errs); go_lesson(t, "Mia · LP9"); t.wait_for_timeout(300)
    url = link_for(t, "g1")
    tok = t.evaluate("__T.PACKS[0].hw && __T.PACKS[0].hw.g1")
    check(isinstance(tok, str) and len(tok) == 32, "the game got a homework token: %s" % tok)
    check(server(t)["packs"]["mia-lp9"]["data"].get("hw", {}).get("g1") == tok, "token saved on the lesson in the database")
    d = link_data(t, url)
    check(d.get("h") == tok and d["g"]["id"] == "g1" and d["p"] == "mia-lp9", "the link carries lesson, game and token")
    check("saves itself" in t.inner_text(".pop"), "link box says homework results save themselves")
    t.click("[data-a=slink-close]")
    url2 = link_for(t, "g1"); t.click("[data-a=slink-close]")
    check(link_data(t, url2).get("h") == tok, "opening the link again keeps the same token")
    check(t.evaluate("__T.PACKS[0].hw.g2") is None, "only the game whose link was made gets a token")

    # 1. Homework at home: the student plays alone, nobody on the other end
    dbnow = server(t)
    s = open_student(home, url, dbnow, errs); play_hangman(s)
    hw = s.evaluate("__MOCK.homework || []")
    check(len(hw) == 1, "one result sent to the database: %d" % len(hw))
    r = hw[0]["data"] if hw else {}
    check(r.get("packId") == "mia-lp9" and r.get("gameId") == "g1" and r.get("homework") is True and r.get("title") == "Castle words (homework)", "it's for this lesson + game, marked homework: %s" % r.get("title"))
    check("(homework, played" in r.get("summary", "") and len(r.get("items", [])) == 2, "summary says homework + when; items kept: %s" % r.get("summary", "")[:80])
    rp = s.evaluate("__MOCK.rpcs[0]")
    check(set(rp.keys()) == {"p_pack", "p_game", "p_token", "p_result"} and "detail" not in rp["p_result"] and "student" not in rp["p_result"], "the page sends only the result fields")
    check("Your teacher has your score already" in s.inner_text("#app") and s.locator("details #res").count() == 1, "student told it's sent; the code folded away")
    sid1 = rp["p_result"]["sid"]; s.screenshot(path=HERE + "/shots/hw_saved.png")
    s.reload(); s.wait_for_timeout(800)
    check(s.evaluate("__MOCK.rpcs.length") == 0 and "Your teacher has your score already" in s.inner_text("#app"), "a reload doesn't send it again")
    # Play again: a new result (new play id)
    s.click("[data-a=s-start]"); s.wait_for_selector(".keys", timeout=5000)
    for i in range(2):
        s.click("[data-a=hm-show]"); s.wait_for_timeout(150); s.click("[data-a=hm-next]"); s.wait_for_timeout(300)
    s.wait_for_selector(".results", timeout=5000); s.wait_for_timeout(400)
    sid2 = s.evaluate("__MOCK.rpcs[0].p_result.sid")
    check(sid2 and sid2 != sid1, "a replay is a new result (sid %s vs %s)" % (sid1, sid2))
    s.close()

    # 2. The same play sent twice (dropped answer, resend) stays one result
    s = open_student(home, url, dbnow, errs)
    s.evaluate("""() => __T.SB ? 0 : 0""")
    out = s.evaluate("""async (a) => { const c = window.supabase.createClient('u','k');
        const one = await c.rpc('submit_homework', a); const two = await c.rpc('submit_homework', a);
        return [one.data, two.data, Object.keys(__MOCK.db.results).length]; }""",
        {"p_pack":"mia-lp9", "p_game":"g1", "p_token":tok, "p_result":{"sid":"mabcdef12", "summary":"x — y"}})
    check(out[0]["new"] is True and out[1]["new"] is False and out[2] == 1, "the same play twice is one row: %s" % out)
    # 3. Wrong / edited token, wrong game, oversized, bad id: all refused
    bad = s.evaluate("""async (a) => { const c = window.supabase.createClient('u','k'), out = [];
        for (const x of a) { const r = await c.rpc('submit_homework', x); out.push(r.error ? r.error.message : 'saved'); } return out; }""", [
        {"p_pack":"mia-lp9", "p_game":"g1", "p_token":tok[:-1] + ("0" if tok[-1] != "0" else "1"), "p_result":{"sid":"mabcdef13"}},
        {"p_pack":"mia-lp9", "p_game":"g2", "p_token":tok, "p_result":{"sid":"mabcdef14"}},
        {"p_pack":"mia-lp9", "p_game":"g1", "p_token":tok, "p_result":{"sid":"mabcdef15", "summary":"x" * 70000}},
        {"p_pack":"mia-lp9", "p_game":"g1", "p_token":tok, "p_result":{"sid":"../x"}},
    ])
    check(bad == ["bad_link", "bad_link", "too_big", "bad_result"], "edited token, other game, oversized and bad id refused: %s" % bad)
    s.close()

    # 4. Edited token in the link itself: the student sees why, and still gets the result code
    d2 = dict(d); d2["h"] = "f" * 32
    bad_url = url.split("#s=")[0] + "#s=" + t.evaluate("x => __T.packData(x)", d2)
    s = open_student(home, bad_url, dbnow, errs); play_hangman(s)
    s.wait_for_timeout(300); txt = s.inner_text("#app")
    check("replaced" in txt and "Send this to your teacher" in txt and "LGR1." in s.input_value("#res"), "edited link: told it couldn't send, code shown")
    check(not s.evaluate("__MOCK.homework"), "nothing saved")
    s.close()

    # 5. No connection: code shown, Try again sends it
    s = open_student(home, url, dbnow, errs, "window.__MOCK.hwDown = true;"); play_hangman(s)
    check("no connection" in s.inner_text("#app") and s.locator("[data-a=hw-retry]").count() == 1 and "LGR1." in s.input_value("#res"), "offline: Try again + result code"); s.screenshot(path=HERE + "/shots/hw_offline.png")
    s.evaluate("__MOCK.hwDown = false"); s.click("[data-a=hw-retry]"); s.wait_for_timeout(400)
    check(len(s.evaluate("__MOCK.homework || []")) == 1 and "Your teacher has your score already" in s.inner_text("#app"), "Try again sends it")
    s.close()

    # 6. New link: old links stop saving
    link_for(t, "g1"); t.click("[data-a=slink-new]")
    check("old links stop saving" in t.inner_text(".pop"), "New link asks for a second tap")
    t.click("[data-a=slink-new]"); t.wait_for_function("document.querySelector('#slinkUrl') && document.querySelector('#slinkUrl').value.length > 0", timeout=5000)
    url3 = t.input_value("#slinkUrl"); tok3 = link_data(t, url3).get("h")
    check(tok3 and tok3 != tok and t.evaluate("__T.PACKS[0].hw.g1") == tok3, "new token made and saved")
    t.click("[data-a=slink-close]")
    dbnew = server(t)
    s = open_student(home, url, dbnew, errs); play_hangman(s)
    check("replaced" in s.inner_text("#app") and not s.evaluate("__MOCK.homework"), "the old link no longer saves")
    s.close()
    s = open_student(home, url3, dbnew, errs); play_hangman(s)
    hwrow = s.evaluate("__MOCK.homework || []")
    check(len(hwrow) == 1, "the new link saves")
    s.close()

    # 7. Teacher's app: the homework result arrives like any result, tagged, and goes into the lesson results text
    t.evaluate("r => __MOCK.remote('results', 'INSERT', r)", hwrow[0]); t.wait_for_timeout(400)
    row = t.inner_text(".game:has([data-g=g1])")
    check("Homework" in row and "(homework, played" in row and "played 1 time" in row, "lesson page shows it as homework: %s" % row.replace("\n", " / ")[:160])
    check(t.locator(".game:has([data-g=g1]) .hwtag").count() == 1, "homework tag")
    check("homework" in t.evaluate("__T.lessonResultsText(__T.PACKS[0])"), "lesson results text (Phase B) includes it")

    # 8. Live at the same time (teacher on the lesson page): the student's send uses the live game number, so it's one result
    url4 = link_for(t, "g1"); t.click("[data-a=slink-close]")
    s = open_student(ctx, url4, server(t), errs); play_hangman(s)
    s.wait_for_timeout(500)
    sid = s.evaluate("__MOCK.rpcs[0].p_result.sid")
    tr = t.evaluate("__T.RESULTS.filter(r => r.gameId === 'g1' && r.liveGen).map(r => r.id)")
    check(sid.startswith("L") and any(x.endswith("_" + sid) for x in tr), "teacher's live save and the homework send share one id: %s / %s" % (sid, tr))
    s.close()

    # 9. Class link pages never send homework
    if t.locator("[data-a=backlesson]").count(): t.click("[data-a=backlesson]"); t.wait_for_timeout(300)
    t.click("#clsBar [data-a=clink]"); t.wait_for_selector("#slinkUrl", timeout=5000); curl = t.input_value("#slinkUrl"); t.click("[data-a=clink-close]")
    check("h" not in t.evaluate("u => __T.unpackData(u.split('#c=')[1])", curl), "class link has no homework token")
    check(not errs, "no page errors: %s" % errs)
    b.close()
done()
