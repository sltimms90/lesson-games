"""27 Nov: every link in every seeded showcase plan works, the way a guest sees it.
The showcase is seeded by Sam's own Reset showcase (🧪 Test page), then a guest signs in to that database. Each lesson with
a plan is opened in the 📖 plan viewer through its normal path (plan-doc, here served from dev/showcase/plans.json
as the function serves them from the database), and:
  - every heading carries a fixed label: SEGMENT n — …, nA · …, or one of the plan's fixed sections;
  - every segment / step heading opens the run sheet at its block / line, and every run sheet block / line opens the plan;
  - every “Lesson Games” title is a 🎲 chip for one of the lesson's games (none left as plain text), every game in the lesson
    has a chip, and each chip opens that game in its own mode; the "Lesson Games pack <id>:" form works with "~sc-" ids;
  - HW Key: one key jumps to it, several give a menu, none falls back to last lesson's HWnn file;
  - other answer keys and the trap's Right / Also right / Expect lines fold; the outline's entries all exist;
  - 📂 Files: Open plan, Folder, every material and Open all open the placeholder page (never Drive); the run sheet's per-block
    material chips too; the notes doc is left empty.
Coverage: the plan viewer's link types are read from the app's own source (data-a="pl-…"); one this test doesn't know fails it,
like the sandbox's every-game-kind check, so a new link type needs a seed plan that uses it (and a line here)."""
import json, os, re
import lg
from lg import *
lg.APP = lg.APP.replace("window.__T={", "window.__T={get STUDENTS(){return STUDENTS},get PL(){return PL},TYPES:TYPES,rsFindAt:rsFindAt,plFind:plFind,plPrevHw:plPrevHw,plFilesItems:plFilesItems,plOpenAllUrls:plOpenAllUrls,plMaterials:plMaterials,getPack:getPack,", 1)
SC = json.load(open(os.path.join(ROOT, "dev", "showcase", "plans.json"), encoding="utf-8"))   # the text dev/sql/showcase_plans.sql loads
PLACE = "https://sltimms90.github.io/lesson-games/showcase.html#"
SECTIONS = re.compile(r"^(LESSON AT A GLANCE|BEFORE CLASS|BUFFER\b.*|PLANNING RECORD)$")

# ---- the viewer's link types, from the app's source: every data-a="pl-…" it can put on the page ----
SRC = open(os.path.join(ROOT, "app", "index.html"), encoding="utf-8").read()
FOUND = set(re.findall(r'data-a="(pl-[a-z-]+)"', SRC)) | set(re.findall(r'setAttribute\("data-a", "(pl-[a-z-]+)"\)', SRC))
LINKS = {"pl-rs": "segment / step heading → run sheet", "pl-go": "run sheet → plan", "pl-play": "🎲 game chip → the game",
         "pl-hw": "HW Key → the homework key (one, or a menu of several)", "pl-to": "outline → heading",
         "pl-files-x": "📂 Files: Open plan · Folder · materials · notes doc (links)", "pl-openall": "📂 Files: Open all",
         "pl-hw-x": "HW Key menu: last lesson's HW file (link)"}
CHROME = {"pl-open": "📖 nav button", "pl-files": "📂 menu button", "pl-outline": "☰ button", "pl-outline-x": "close", "pl-refresh": "fetch again",
          "pl-edit": "change the plan's link", "pl-edit-x": "cancel", "pl-save": "save a pasted link"}
COVER = {k: set() for k in ["seg→rs", "step→rs", "rs→plan", "chip", "pack-line chips", "hw one", "hw menu", "hw prev file", "outline",
                            "open plan", "folder", "material", "open all", "rs-file chip", "key fold", "answer fold"]}

def seed():
    """Sam resets the showcase; the database it leaves is what the guest signs in to."""
    db = seed_db([{"id":"mia-lp9","student":"Mia","lp":9,"title":"Mia · LP9","date":"2026-11-20","updatedAt":"x","games":[]}], students=[{"id":"mia","name":"Mia","updatedAt":"x"}])
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); ctx = b.new_context(); errs = []
        t = teacher(ctx, db, errs); t.wait_for_selector("#stuSec", timeout=8000)
        t.click("[data-a=tst-open-page]"); t.wait_for_selector("[data-a=tst-sc-reset]", timeout=4000)
        t.click("[data-a=tst-sc-reset]"); t.click("[data-a=tst-sc-go]")
        t.wait_for_function("Object.keys(__MOCK.db.packs).filter(k => k.startsWith('~sc-')).length === 16 && Object.keys(__MOCK.db.sheets).length === 12", timeout=8000)
        out = t.evaluate("JSON.parse(JSON.stringify(__MOCK.db))"); b.close()
        check(not errs, "Sam's reset: no page errors %s" % errs[:2])
        return out

def guest_page(ctx, db, errs, calls):
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("G: " + str(e)))
    pg.on("dialog", lambda d: (errs.append("browser dialog: " + d.message), d.dismiss()))
    pg.add_init_script("window.__MOCK = %s;" % json.dumps({"db":db, "session":{"user":{"email":"friend@example.com"}, "access_token":"GUESTTOK"}, "teacher":False, "guest":True}))
    def h(r):
        u = r.request.url
        if u.endswith("/functions/v1/plan-doc"):
            d = json.loads(r.request.post_data or "{}").get("docId", ""); calls.append(d)
            if not d.startswith("showcase-") or d not in SC: return r.fulfill(status=401, body='{"error":"not_teacher"}', content_type="application/json")
            x = SC[d]; return r.fulfill(body=json.dumps({"html":x["html"], "name":x["name"], "modified":"", "folderId":x["folderId"]}), content_type="application/json")
        if u.endswith("/app/supabase.js"): return r.fulfill(body=lg.MOCK, content_type="application/javascript")
        if "/lesson-games/" in u: return r.fulfill(body=lg.APP, content_type="text/html")
        return r.abort()
    pg.route("**/*", h); pg.goto("https://sltimms90.github.io/lesson-games/app/")
    return pg

def ev(pg, js, arg=None): return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)

db = seed()
unknown = sorted(FOUND - set(LINKS) - set(CHROME))
check(not unknown, "every plan viewer link type is known to this test (a new one needs a seed plan and a check here): %s" % unknown)
check(not (set(LINKS) - FOUND), "the link types this test checks still exist in the app: %s" % sorted(set(LINKS) - FOUND))
plans = sorted([(k, v["data"]) for k, v in db["packs"].items() if v["data"].get("plan")], key=lambda x: x[0])
check(len(plans) == 6 and all(p["plan"]["docId"] in SC for _, p in plans), "six seeded lessons have plans, all in the plan-doc bundle: %s" % [p["plan"]["docId"] for _, p in plans])
check(sorted(SC) == sorted(p["plan"]["docId"] for _, p in plans), "every bundled plan belongs to a seeded lesson")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []; calls = []
    g = guest_page(ctx, db, errs, calls); g.wait_for_selector("#stuSec", timeout=8000)
    check(g.locator(".gst-stripe").count() == 1 and ev(g, "__T.AUTH.email") == "friend@example.com", "signed in as a guest (the stripe shows)")
    for pid, pk in plans:
        title = pk["title"]; who = pk["student"]
        go_lesson(g, title, who); g.wait_for_timeout(300)
        g.click("[data-a=pl-open]"); g.wait_for_selector("#plDoc h2", timeout=5000); g.wait_for_timeout(200)
        tag = "%s (%s)" % (title, pk["plan"]["docId"])
        # -- fixed labels on every heading
        hs = ev(g, "[...document.querySelectorAll('#plDoc h2, #plDoc h3')].map(h => [h.tagName, h.textContent.replace(/\\s+/g, ' ').trim(), h.id, h.dataset.a || '', h.dataset.c || '', h.dataset.s || ''])")
        bad = [t for tg, t, *_ in hs if (tg == "H2" and not re.match(r"^SEGMENT \d+ — ", t) and not SECTIONS.match(t.split(" (")[0])) or (tg == "H3" and not re.match(r"^\d+[A-Z] · \S", t))]
        check(not bad, "%s: every heading has a fixed label: %s" % (tag, bad))
        segs = [(t, i, s) for tg, t, i, a, c, s in hs if i.startswith("pl-seg-")]; steps = [(t, i, c) for tg, t, i, a, c, s in hs if i.startswith("pl-step-")]
        nolink = [t for tg, t, i, a, c, s in hs if (i.startswith("pl-seg-") or i.startswith("pl-step-")) and a != "pl-rs"]
        check(segs and steps and not nolink, "%s: every segment and step heading is a run sheet link (%d + %d): unlinked %s" % (tag, len(segs), len(steps), nolink))
        if segs: COVER["seg→rs"].add(pid)
        if steps: COVER["step→rs"].add(pid)
        # -- 🎲 chips: every quoted title after "Lesson Games" is one; every game has one
        chips = ev(g, "[...document.querySelectorAll('#plDoc .pl-game')].map(b => b.dataset.g)")
        games = {x["id"]: x for x in pk["games"]}
        left = ev(g, r"""[...document.querySelectorAll('#plDoc p, #plDoc li')].map(e => e.textContent).filter(t => /lesson\s+games(\s+pack\s+[\w.~\-]+)?\s*:?\s*[“"]/i.test(t))""")
        check(not left and set(chips) == set(games), "%s: every Lesson Games title is a chip, every game has one (chips %s, games %s, left %s)" % (tag, sorted(set(chips)), sorted(games), left))
        if chips: COVER["chip"].add(pid)
        if ev(g, r"""[...document.querySelectorAll('#plDoc p')].some(e => /Lesson Games pack ~sc-/.test(e.textContent) && e.querySelector('.pl-game'))"""): COVER["pack-line chips"].add(pid)
        # -- folds: keys and the trap's answers
        kb = ev(g, r"""[...document.querySelectorAll('#plDoc p > b:first-child')].filter(b => b.closest('p').textContent.trim() === b.textContent.trim() && /(^key\b|\bkey\s*:?$|^key\s*[—–-])/i.test(b.textContent.trim())).map(b => b.textContent)""")
        check(not kb, "%s: every bold key line is folded: %s" % (tag, kb))
        nk = ev(g, "document.querySelectorAll('#plDoc details.pl-key').length"); na = ev(g, "document.querySelectorAll('#plDoc details.pl-ans').length")
        open_ans = ev(g, r"""[...document.querySelectorAll('#plDoc li, #plDoc p')].filter(e => /^(also right|right|expect(ed)?)\s*:/i.test(e.textContent.trim()) && !e.querySelector('details.pl-ans') && !e.closest('details.pl-ans')).length""")
        check(nk > 0 and open_ans == 0, "%s: %d keys fold, every Right / Also right / Expect line folds (%d open)" % (tag, nk, open_ans))
        if nk: COVER["key fold"].add(pid)
        if na: COVER["answer fold"].add(pid)
        # -- outline
        o = ev(g, "(__T.PL.built.outline || []).map(x => x.id).filter(id => !document.getElementById(id))")
        check(ev(g, "(__T.PL.built.outline || []).length") > 4 and not o, "%s: the outline's entries all exist (%s missing)" % (tag, o))
        COVER["outline"].add(pid)
        # -- HW Key
        hw = ev(g, "__T.PL.built.hw.map(x => x.id)"); hbtn = g.locator(".pl-top [data-a=pl-hw]").count()
        if len(hw) == 1:
            g.click(".pl-top [data-a=pl-hw]"); g.wait_for_timeout(250)
            check(ev(g, "(() => { const e = document.getElementById(%s); return !!e && e.open && e.getBoundingClientRect().top < innerHeight; })()" % json.dumps(hw[0])), "%s: HW Key jumps to the homework key, unfolded" % tag)
            COVER["hw one"].add(pid)
        elif len(hw) > 1:
            g.click(".pl-top [data-a=pl-hw]"); g.wait_for_selector("#plHwMenu", timeout=2000)
            ids = ev(g, "[...document.querySelectorAll('#plHwMenu [data-a=pl-hw][data-id]')].map(b => b.dataset.id)")
            check(sorted(ids) == sorted(hw), "%s: HW Key menu lists every homework key %s" % (tag, ids))
            g.click("#plHwMenu [data-a=pl-hw][data-id='%s']" % hw[1]); g.wait_for_timeout(250)
            check(ev(g, "document.getElementById(%s).open" % json.dumps(hw[1])), "%s: a menu entry opens that key" % tag)
            COVER["hw menu"].add(pid)
        else:
            prev = ev(g, "(() => { const r = __T.plPrevHw(__T.getPack(%s)); return r && { t:r.t, url:r.url, from:r.from.id }; })()" % json.dumps(pid))
            check(hbtn == 1 and prev and prev["url"].startswith(PLACE), "%s: no homework key in the plan → HW Key opens last lesson's homework file %s" % (tag, prev))
            if hbtn: g.click(".pl-top [data-a=pl-hw]"); g.wait_for_selector("#plHwMenu .pl-hwf", timeout=2000)
            check(ev(g, "document.querySelector('#plHwMenu .pl-hwf').href").startswith(PLACE), "%s: the menu's link is the placeholder page" % tag)
            g.click("#plHwMenu [data-a=pl-hw-x].btn"); g.wait_for_timeout(100)
            COVER["hw prev file"].add(pid)
        # -- 📂 Files: every link the placeholder, never Drive; notes doc empty
        items = ev(g, "__T.plFilesItems(__T.getPack(%s)).map(x => [x.t, x.url, !!x.mat, !!x.nd])" % json.dumps(pid))
        drive = [x for x in items if not x[1].startswith(PLACE)]
        check(items and not drive and not any(x[3] for x in items), "%s: 📂 Files has %d links, all the placeholder page, no notes doc: %s" % (tag, len(items), drive))
        if any(x[0] == "Open plan" for x in items): COVER["open plan"].add(pid)
        if any(x[0] == "Folder" for x in items): COVER["folder"].add(pid)
        if any(x[2] for x in items): COVER["material"].add(pid)
        if ev(g, "__T.plOpenAllUrls(__T.getPack(%s)).length" % json.dumps(pid)) > 0: COVER["open all"].add(pid)
        g.click(".pl-top [data-a=pl-files]"); g.wait_for_selector("#plFiles", timeout=2000)
        hrefs = ev(g, "[...document.querySelectorAll('#plFiles a')].map(a => a.href)")
        check(len(hrefs) == len(items) and all(h.startswith(PLACE) for h in hrefs) and g.locator("#plFiles [data-a=pl-openall]").count() == 1, "%s: the Files menu shows them (and Open all)" % tag)
        g.click("#plFiles .row [data-a=pl-files-x]"); g.wait_for_timeout(100)
        # -- run sheet ← plan: every heading's target exists on the run sheet; and back
        targets = [{"c":c, "s":""} for _, _, c in steps] + [{"c":"", "s":s} for _, _, s in segs]
        g.click("#plDoc [data-a=pl-rs][data-c='%s']" % steps[0][2]); g.wait_for_timeout(400)
        check(ev(g, "__T.UI.view") == "sheet", "%s: a step heading opens the run sheet" % tag)
        miss = ev(g, "ts => ts.filter(t => !__T.rsFindAt(t)).map(t => t.c || t.s)", targets)
        check(not miss, "%s: every plan heading has its run sheet line / block: %s" % (tag, miss))
        jumps = ev(g, "[...document.querySelectorAll('.rs .pl-j[data-a=pl-go]')].map(e => ({ bl:e.dataset.bl, c:e.dataset.c }))")
        codes = ev(g, "[...new Set([...document.querySelectorAll('.rs [data-sc]')].map(e => e.dataset.sc))]")
        blocks = ev(g, "[...document.querySelectorAll('.rs .rs-blk[data-seg]')].map(e => e.dataset.seg)")
        rsf = ev(g, "[...document.querySelectorAll('.rs .rs-file')].map(a => a.href)")
        check(rsf and all(h.startswith(PLACE) for h in rsf), "%s: the run sheet's material chips open the placeholder page (%d)" % (tag, len(rsf)))
        if rsf: COVER["rs-file chip"].add(pid)
        g.click("[data-a=pl-open]"); g.wait_for_selector("#plDoc h2", timeout=4000); g.wait_for_timeout(150)
        lost = ev(g, "js => js.filter(j => !__T.plFind(j)).map(j => j.bl + ' ' + j.c)", jumps)
        check(jumps and not lost, "%s: every run sheet block and line opens the plan (%d): %s" % (tag, len(jumps), lost))
        nostep = [c for c in codes if not ev(g, "c => !!document.getElementById('pl-step-' + c)", c)]
        noseg = [s for s in blocks if not ev(g, "s => !!document.getElementById('pl-seg-' + s)", s)]
        check(not nostep and not noseg, "%s: every run sheet step and block has its plan heading: steps %s, blocks %s" % (tag, nostep, noseg))
        COVER["rs→plan"].add(pid)
        # -- each chip opens its game in its own mode, and Back returns to the plan
        for gid in sorted(set(chips)):
            g.click("#plDoc .pl-game[data-g='%s']" % gid); g.wait_for_timeout(350)
            run = ev(g, "__T.UI.run && { v:__T.UI.view, g:__T.UI.run.gameId, t:__T.UI.run.type, mode:__T.UI.run.st.mode || null, fb:__T.UI.run.st.feedback || null }")
            want = games[gid]
            ok = run and run["v"] == "play" and run["g"] == gid and run["t"] == want["type"] and (not want["options"].get("mode") or run["mode"] == want["options"]["mode"]) and (not want["options"].get("feedback") or run["fb"] == want["options"]["feedback"])
            check(ok, "%s: 🎲 %s opens %s%s: %s" % (tag, want["title"], want["type"], (" / " + want["options"]["mode"]) if want["options"].get("mode") else "", run))
            g.click("[data-a=lesson]"); g.wait_for_timeout(300)
            if ev(g, "__T.UI.view") != "plan": g.click("[data-a=pl-open]"); g.wait_for_timeout(300)
        g.click("[data-a=home]"); g.wait_for_timeout(250)
    # ---- coverage across the seed
    empty = sorted(k for k, v in COVER.items() if not v)
    check(not empty, "the seeded plans cover every link type: missing %s" % empty)
    modes = {(x["type"], x["options"].get("mode")) for _, pk in plans for x in pk["games"]}
    need = {"spelling", "hangman", "typeit", "match", "quiz", "bingo", "snakes", "typhoon"}
    check(need <= {t for t, _ in modes} and ("match", "pairs") in modes and ("match", "match") in modes and ("quiz", "winlose") in modes,
          "plan games cover Spelling modes, both Matching modes, Quiz (both modes), Bingo and reward games: %s" % sorted(map(str, modes)))
    check(all(c.startswith("showcase-") for c in calls) and calls, "plan-doc was asked only for showcase plans (%d)" % len(calls))
    for k in sorted(COVER): print("  covered %-16s %s" % (k, ", ".join(sorted(COVER[k]))))
    check(not errs, "no page errors %s" % errs[:3])
done()
