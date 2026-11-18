"""Bingo feedback (18 Nov 2026): a card each for "Cathy & Lily", either side of the caller; called words in one line
that never shrinks the cards; print two cards a page plus the teacher's; "My card" for the phone. Run sheet: a step
cue and its app game ("2A …") are one row."""
from lg import *
import lg
lg.APP = lg.APP.replace(HOOK, HOOK + "window.__B={splitNames:splitNames,rsBuildDoc:rsBuildDoc,rsDoc:rsDoc,getPack:getPack};")
words = ["castle","tower","bridge","market","river","forest","garden","palace","village","harbour","museum","station","library","school","hospital","bakery"]
bg = {"id":"g3","type":"bingo","title":"Bingo","block":"\n".join(words),"options":{"size":3,"call":"word","claim":True,"cards":"Cathy & Lily","code":"PAB5","show":"student","self":True,"lines":3}}
blocks = [{"mins":14,"label":"2 GAME Evidence Auction","material":"WS27","lines":[{"text":"8 lots · E4 red pen","type":"cue","label":"2A The auction"},{"game":"g1","type":"app","label":"2A Evidence Auction"},{"n":5,"type":"score","label":"2A fakes passed + fixed"},{"text":"7 sentences · fixes typed","type":"cue","label":"2B Case Closed"},{"game":"g2","type":"app","label":"2B Case Closed"},{"text":"3 slips","type":"cue","label":"2C Fix-it"}]}]
pack = {"id":"jl","student":"Cathy & Lily","lp":27,"title":"JL","date":"2026-11-18","updatedAt":"x",
 "games":[{"id":"g1","type":"auction","title":"Evidence Auction","block":"1. He goes home. [CORRECT]\n2. He go home. [WRONG — goes]"},{"id":"g2","type":"spot","title":"Case Closed","block":"She don't like it. = She doesn't like it."}, bg],
 "runsheet":{"student":"Cathy & Lily","lp":27,"start":"19:00","length":60,"format":"in person","blocks":blocks}}
res = [{"id":"r1","packId":"jl","gameId":"g1","type":"auction","summary":"x","score":{"text":"9,650 money · fixed 5/5"},"at":"2026-11-18T11:00:00Z"}]
def lesson(pg):
    pg.wait_for_selector("text=JL", timeout=8000); pg.click("text=JL"); pg.wait_for_timeout(300)
    if pg.evaluate("__T.UI.view") == "sheet": pg.locator("button", has_text="Games").first.click(); pg.wait_for_timeout(300)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":1180, "height":820}); errs = []
    pg = teacher(ctx, seed_db([pack], results=res), errs); lesson(pg)
    check(pg.evaluate("__B.splitNames('Cathy & Lily').join('|') + ';' + __B.splitNames('Matthew and Emma').join('|') + ';' + __B.splitNames('Alexander').join('|')") == "Cathy|Lily;Matthew|Emma;Alexander", "names split on & and 'and', not inside a name")
    pg.click("[data-a=play][data-g=g3]"); pg.wait_for_timeout(400)
    heads = pg.locator(".card-head span:first-child").all_text_contents()
    check(heads == ["Cathy", "Lily"], "two student cards, Cathy and Lily: %s" % heads)
    check(pg.locator(".play3.duo").count() == 1, "duo layout: a card each side of the caller")
    xs = pg.evaluate("[...document.querySelectorAll('.bgwrap > .play3 > *')].map(e => e.className.split(' ')[0])")
    check(xs == ["cards", "center", "cards"], "card · caller · card: %s" % xs)
    h0 = pg.evaluate("document.querySelector('.card').getBoundingClientRect().height")
    for i in range(14):
        if pg.locator("[data-a=bg-next]:not([disabled])").count(): pg.click("[data-a=bg-next]"); pg.wait_for_timeout(60)
    pg.wait_for_timeout(300)
    h1 = pg.evaluate("document.querySelector('.card').getBoundingClientRect().height")
    check(abs(h1 - h0) < 2 and pg.evaluate("getComputedStyle(document.querySelector('main.stage')).zoom") == "1", "cards keep their size after 14 calls (%d → %d)" % (h0, h1))
    check(pg.evaluate("document.querySelector('.calledbar .chips').getBoundingClientRect().height") < 60, "called words stay on one line")
    check(overflow(pg) == [], "nothing spills: %s" % overflow(pg))
    tk = pg.evaluate("__T.UI.run.st.cards[__T.UI.run.st.tk].map(i => i < 0 ? '*' : __T.UI.run.st.items[i].w).join(',')")
    pg.click("[data-a=lesson]"); pg.wait_for_timeout(300)
    if pg.evaluate("__T.UI.view") == "sheet": pg.locator("button", has_text="Games").first.click(); pg.wait_for_timeout(300)
    pg.evaluate("window.print = () => {}"); pg.click("[data-a=print][data-g=g3]"); pg.wait_for_timeout(200)
    names = pg.locator("#print .pcard .ph span:last-child").all_text_contents()
    check(names == ["Cathy", "Lily", "Teacher"], "prints Cathy, Lily and Teacher: %s" % names)
    check(pg.locator("#print .ppage").count() == 2 and pg.locator("#print .ppage").first.locator(".pcard").count() == 2, "two cards a page")
    check("landscape" in pg.evaluate("document.getElementById('pageLand').textContent"), "landscape page")
    ptk = pg.evaluate("[...document.querySelectorAll('#print .pcard')[2].querySelectorAll('.pc')].map(e => e.classList.contains('free') ? '*' : e.textContent).join(',')")
    check(ptk == tk, "printed teacher card is the on-screen teacher card")
    pg.click("[data-a=bgmine]"); pg.wait_for_timeout(300)
    mtk = pg.evaluate("[...document.querySelectorAll('.bgmine .cell')].map(e => e.classList.contains('free') ? '*' : e.textContent).join(',')")
    check(mtk == tk, "My card is the same teacher card")
    for i in range(3): pg.locator("[data-a=bgm-tap]").nth(i).click(); pg.wait_for_timeout(60)
    pg.reload(); pg.wait_for_timeout(1200)
    check(pg.evaluate("__T.UI.view") == "bgmine" and pg.locator(".bgmine .cell.on").count() == 3 and "1 line" in pg.inner_text(".bgmine"), "My card keeps its stamps and shows the line")
    pg.click("[data-a=bgm-back]"); pg.wait_for_timeout(300)
    pg.click("[data-a=rs-open]"); pg.wait_for_timeout(400)
    txt = pg.inner_text(".rs-blk")
    check("The auction" in txt and "8 lots · E4 red pen" in txt and txt.count("2A") == 2, "2A cue folded into the game row (2A game + 2A score)")
    check("Played · 9,650 money" in txt, "played result shown under the game")
    check(txt.count("2B Case Closed") == 1 and "7 sentences · fixes typed" in txt, "2B: one row with the cue's text")
    check("2C Fix-it" in txt, "a cue with no game of its own stays")
    summ = pg.evaluate("__B.rsBuildDoc(__B.getPack('jl'), __B.rsDoc('jl'))")
    gaps = summ["gaps"]
    check(not any("The auction" in g for g in gaps) and "2C Fix-it — 3 slips" in gaps, "Phase B no longer asks about the folded cue: %s" % gaps)
    check("(The auction: 8 lots · E4 red pen)" in summ["summary"], "the cue's text is in the Phase B summary")
    check(pg.evaluate("JSON.stringify(__B.getPack('jl').runsheet.blocks[0].lines.length)") == "6", "the plan itself is unchanged")
    check(errs == [], "no page errors: %s" % errs)
    done()
