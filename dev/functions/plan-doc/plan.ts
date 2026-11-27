/* plan-doc — the lesson plan for the teacher app's Plan tab (Nov 2026).
   POST { docId } with the teacher's own sign-in (Authorization: Bearer <access token>) →
   { html, name, modified, mime, folderId }.  folderId is the file's Drive folder (the student's lesson-plan folder,
   where the WS, print pack and HW PDFs are filed), from the same metadata call, or "" if Drive doesn't say.  Anyone else gets 401 and nothing from Drive.

   - Who: the caller's token is checked by the database itself (rpc am_i_teacher), the same rule as RLS.
   - Drive: a Google service account, read-only scope. Its JSON key is the Edge Function secret
     GOOGLE_SA_KEY. It sees only what Sam has shared with its email (the Tutorial Lesson Plans folder: one sub-folder per student).
   - Native Google Docs come back through files.export (text/html). The LP files are .docx on Drive,
     so those are downloaded and turned into plain HTML here (mammoth: headings, bold, lists; no styles).
   - The app cleans the HTML again before showing it; nothing here is trusted by the page.
   index.ts serves handle(); plan_test.ts tests it with a fake Google (deno test --allow-env --allow-read).
   Deployed with verify_jwt off because the teacher check below is stricter than a valid-JWT check.
   - Showcase plans (27 Nov): a docId starting "showcase-" is one of the made-up school's plans. They live in the database
     (private.showcase_plans, loaded by dev/sql/showcase_plans.sql, which dev/build.py writes from dev/showcase/plans/), read
     with the caller's own token through rpc showcase_plan, which answers only the teacher or a guest (an email on the guest
     list). Drive is never asked for them. Every other docId stays teacher only, guests included. */
import mammoth from "npm:mammoth@1.8.0";
import { Buffer } from "node:buffer";

const ORIGINS = ["https://sltimms90.github.io"];
const DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const GDOC = "application/vnd.google-apps.document";
const MAX_BYTES = 8 * 1024 * 1024;

function cors(req: Request): Record<string, string> {
  const o = req.headers.get("origin") || "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}
function reply(req: Request, status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

/* The caller is the teacher (or, for showcase plans, a guest): the database's own check, with the caller's token. */
async function rpc(req: Request, fn: string, body: unknown, fetchFn = fetch): Promise<unknown> {
  const auth = req.headers.get("authorization") || "";
  if (!/^Bearer\s+\S+/.test(auth)) return null;
  const url = Deno.env.get("SUPABASE_URL"), key = req.headers.get("apikey") || Deno.env.get("SUPABASE_ANON_KEY") || "";
  if (!url || !key) return null;
  try {
    const r = await fetchFn(url + "/rest/v1/rpc/" + fn, { method: "POST", headers: { apikey: key, Authorization: auth, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}
export async function isTeacher(req: Request, fetchFn = fetch): Promise<boolean> { return (await rpc(req, "am_i_teacher", {}, fetchFn)) === true; }
export async function isGuest(req: Request, fetchFn = fetch): Promise<boolean> { return (await rpc(req, "am_i_guest", {}, fetchFn)) === true; }

/* Google access token for the service account (JWT bearer grant), kept until shortly before it expires. */
let TOKEN: { v: string; exp: number } | null = null;
function b64url(b: ArrayBuffer | Uint8Array | string): string {
  const bytes = typeof b === "string" ? new TextEncoder().encode(b) : new Uint8Array(b);
  let s = ""; for (const x of bytes) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
async function googleToken(fetchFn = fetch): Promise<string> {
  if (TOKEN && TOKEN.exp > Date.now() + 60_000) return TOKEN.v;
  const raw = Deno.env.get("GOOGLE_SA_KEY");
  if (!raw) throw new Failure(503, "not_set_up");
  let sa: { client_email: string; private_key: string; token_uri?: string };
  try { sa = JSON.parse(raw); } catch { throw new Failure(503, "bad_key"); }
  if (!sa.client_email || !sa.private_key) throw new Failure(503, "bad_key");
  const pem = sa.private_key.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("pkcs8", der, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const now = Math.floor(Date.now() / 1000), aud = sa.token_uri || "https://oauth2.googleapis.com/token";
  const head = b64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claim = b64url(JSON.stringify({ iss: sa.client_email, scope: "https://www.googleapis.com/auth/drive.readonly", aud, iat: now, exp: now + 3600 }));
  const sig = b64url(await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(head + "." + claim)));
  const r = await fetchFn(aud, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer", assertion: head + "." + claim + "." + sig }) });
  if (!r.ok) throw new Failure(502, "google_auth");
  const j = await r.json();
  TOKEN = { v: j.access_token, exp: Date.now() + (j.expires_in || 3600) * 1000 };
  return TOKEN.v;
}
class Failure extends Error { constructor(public status: number, public code: string) { super(code); } }

const DRIVE = "https://www.googleapis.com/drive/v3/files/";
export async function planHtml(docId: string, fetchFn = fetch) {
  const tok = await googleToken(fetchFn), h = { Authorization: "Bearer " + tok };
  const m = await fetchFn(DRIVE + encodeURIComponent(docId) + "?fields=name,mimeType,modifiedTime,size,parents&supportsAllDrives=true", { headers: h });
  if (m.status === 404 || m.status === 403) throw new Failure(404, "not_found");
  if (!m.ok) throw new Failure(502, "drive");
  const meta = await m.json();
  if (meta.size && +meta.size > MAX_BYTES) throw new Failure(413, "too_big");
  let html: string;
  if (meta.mimeType === GDOC) {
    const r = await fetchFn(DRIVE + encodeURIComponent(docId) + "/export?mimeType=text/html", { headers: h });
    if (!r.ok) throw new Failure(502, "drive");
    html = await r.text();
  } else if (meta.mimeType === DOCX) {
    const r = await fetchFn(DRIVE + encodeURIComponent(docId) + "?alt=media&supportsAllDrives=true", { headers: h });
    if (!r.ok) throw new Failure(502, "drive");
    const buf = await r.arrayBuffer();
    if (buf.byteLength > MAX_BYTES) throw new Failure(413, "too_big");
    const out = await mammoth.convertToHtml({ buffer: Buffer.from(buf) }, { convertImage: mammoth.images.imgElement(() => Promise.resolve({ src: "" })) });
    html = out.value;
  } else throw new Failure(415, "not_a_doc");
  if (html.length > MAX_BYTES) throw new Failure(413, "too_big");
  const parent = Array.isArray(meta.parents) ? String(meta.parents[0] || "") : "";
  const folderId = /^[A-Za-z0-9_-]{10,128}$/.test(parent) ? parent : "";
  return { html, name: String(meta.name || ""), modified: String(meta.modifiedTime || ""), mime: meta.mimeType, folderId };
}

export async function handle(req: Request, fetchFn = fetch): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(req) });
  if (req.method !== "POST") return reply(req, 405, { error: "method" });
  let docId = "";
  try { docId = String((await req.json()).docId || ""); } catch { /* bad body */ }
  const showcase = docId.startsWith("showcase-");
  if (!(await isTeacher(req, fetchFn)) && !(showcase && await isGuest(req, fetchFn))) return reply(req, 401, { error: "not_teacher" });
  if (!/^[A-Za-z0-9_-]{20,128}$/.test(docId)) return reply(req, 400, { error: "bad_id" });
  if (showcase) {
    const p = await rpc(req, "showcase_plan", { p_doc: docId }, fetchFn) as { html?: unknown; name?: unknown; folderId?: unknown } | null;
    if (!p || typeof p.html !== "string") return reply(req, 404, { error: "not_found" });
    return reply(req, 200, { html: p.html, name: String(p.name || ""), modified: "", mime: DOCX, folderId: typeof p.folderId === "string" ? p.folderId : "" });
  }
  try { return reply(req, 200, await planHtml(docId, fetchFn)); }
  catch (e) {
    if (e instanceof Failure) return reply(req, e.status, { error: e.code });
    console.error("plan-doc", e);
    return reply(req, 500, { error: "failed" });
  }
}

