"""Builds plan_sample.docx: a made-up lesson plan in the LP layout (no real student), for the Plan tab tests.
   python3 make_plan_sample.py   (needs python-docx). plan_sample.html is the same plan as mammoth turns it into
   (what the plan-doc function sends); regenerate it with:  node -e "require('mammoth').convertToHtml({path:'plan_sample.docx'}).then(r=>require('fs').writeFileSync('plan_sample.html', r.value))" """
import os
from docx import Document
HERE = os.path.dirname(os.path.abspath(__file__))
d = Document()
def para(text, bold_label=None, style=None):
    p = d.add_paragraph(style=style)
    if bold_label: p.add_run(bold_label).bold = True
    if text: p.add_run(text)
    return p
def lines(*ls):
    p = d.add_paragraph()
    for i, l in enumerate(ls):
        r = p.add_run(l)
        if i < len(ls) - 1: r.add_break()
d.add_heading("LP12 · Kit · Friday, November 20, 2026", 1)
d.add_heading("LESSON AT A GLANCE", 2)
para(" Kit planted the seeds.", "Last time:")
d.add_heading("SEGMENT 0 — ARRIVAL (~10 min, 17:00–17:10)", 2)
para("Material: timer", None)
d.add_heading("0A · Warm-up chat (5 min, 17:00–17:05)", 3)
para(" Say: “Tell me about your weekend.”", "Rules.")
para("⚠ TRAP (cold)", None, "List Bullet")
para("Spring: “Where did you go yesterday?”", None, "List Bullet 2")
para("Right: “I went to the park.”", None, "List Bullet 2")
para("Also right: “I went to the zoo.”", None, "List Bullet 2")
para("Expect: “I go to the park.”", None, "List Bullet 2")
para("Repair: “Yesterday… I…?” Wait.", None, "List Bullet 2")
para("After a miss: “Yesterday is past: went.”", None, "List Bullet 2")
d.add_heading("0B · Spelling test (5 min, 17:05–17:10)", 3)
para(" all ten are typed.", "Done when:")
d.add_heading("SEGMENT 1 — TEACHING NOTES: PAST SIMPLE (~15 min, 17:10–17:25)", 2)
d.add_heading("1A · Went, saw, ate (8 min, 17:10–17:18)", 3)
para(" Say: “Yesterday I went to the park. I saw a dog.”", "Build.")
for i in range(40): para("Teacher line %d: point at the card and say the next past form out loud." % (i + 1))
d.add_heading("1B · Bomb Squad (7 min, 17:18–17:25)", 3)
para(" Point at the book. Say: “Find the bad wire.”", "Rules.")
para("Key", "")
d.paragraphs[-1].runs[0].bold = True
lines("1 The bad wire is “go”. I went home.", "2 The bad wire is “eat”. She ate rice.")
para(" items said.", "Done when:")
d.add_heading("SEGMENT 2 — EXAM: PAPER 1 (~15 min, 17:25–17:40)", 2)
d.add_heading("2A · The paper (10 min, 17:25–17:35)", 3)
para(" Hand the paper. Say: “Ten minutes. Go.”", "Rules.")
for i in range(40): para("Paper note %d: watch where he stops and rubs out; say nothing." % (i + 1))
d.add_heading("2B · Read, fix (5 min, 17:35–17:40)", 3)
para(" He reads each answer.", "Fix.")
p = para("Paper 1 key", ""); p.runs[0].bold = True
lines("1 went   watch: goed", "2 saw   watch: seed")
para("Accept said: 1 walked to.")
d.add_heading("BUFFER (~2 min, 17:40–17:42)", 2)
para("Overrun only. Nothing new.")
d.add_heading("PLANNING RECORD", 2)
para(" past simple.", "Main:")
d.save(os.path.join(HERE, "plan_sample.docx"))
print("plan_sample.docx written")
