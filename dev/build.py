"""Run after every edit to app/index.html:  python3 dev/build.py
Stamps the Content-Security-Policy with the hash of the app's one inline script (so injected inline code,
e.g. an onerror= attribute, can't run) and copies the app over the student page (index.html)."""
import base64, hashlib, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
p = os.path.join(ROOT, "app", "index.html"); s = open(p, encoding="utf-8").read()
# The build id (APP_B): a hash of the script with the id blanked, so every change to the app gets a new one. Live
# messages and presence carry it, so a class-link page older than the teacher's app can tell and reload itself.
assert len(re.findall(r'var APP_B = "[0-9a-f]*";', s)) == 1, "expected one var APP_B"
s = re.sub(r'var APP_B = "[0-9a-f]*";', 'var APP_B = "";', s)
b0 = re.findall(r"<script>(.*?)</script>", s, re.S)[0]
bid = hashlib.sha256(b0.encode("utf-8")).hexdigest()[:10]
s = s.replace('var APP_B = "";', 'var APP_B = "%s";' % bid, 1)
scripts = re.findall(r"<script>(.*?)</script>", s, re.S)
assert len(scripts) == 1, "expected exactly one inline <script>, found %d" % len(scripts)
h = base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode()
csp = "script-src 'self' 'sha256-%s'; object-src 'none'; base-uri 'none'" % h
tag = '<meta http-equiv="Content-Security-Policy" content="%s">' % csp
if re.search(r'<meta http-equiv="Content-Security-Policy"[^>]*>', s): s = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>', tag, s)
else: s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + tag, 1); assert tag in s
open(p, "w", encoding="utf-8").write(s)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(s)
print("build %s · CSP sha256-%s · app/index.html copied to index.html" % (bid, h))
