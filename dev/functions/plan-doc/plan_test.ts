/* deno test --allow-env --allow-read dev/functions/plan-doc/plan_test.ts
   A fake Supabase (am_i_teacher), fake Google token endpoint and fake Drive; the .docx is dev/tests/plan_sample.docx. */
import { handle } from "./plan.ts";

const DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz012345";
const sample = await Deno.readFile(new URL("../../tests/plan_sample.docx", import.meta.url));
const kp = await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const pk = btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.exportKey("pkcs8", kp.privateKey))));
const SA = JSON.stringify({ client_email: "plans@test.iam.gserviceaccount.com", private_key: "-----BEGIN PRIVATE KEY-----\n" + pk + "\n-----END PRIVATE KEY-----\n" });
Deno.env.set("SUPABASE_URL", "https://proj.supabase.co");
Deno.env.set("SUPABASE_ANON_KEY", "anon");

type World = { teacher: boolean; mime: string; calls: string[] };
function fake(w: World) {
  return async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const u = String(input); w.calls.push(u);
    if (u.endsWith("/rest/v1/rpc/am_i_teacher")) {
      const a = new Headers(init?.headers).get("authorization");
      return new Response(JSON.stringify(a === "Bearer TEACHER" && w.teacher), { status: 200 });
    }
    if (u === "https://oauth2.googleapis.com/token") {
      const body = new URLSearchParams(String(init?.body)), jwt = body.get("assertion") || "";
      const [h, c, s] = jwt.split("."), dec = (x: string) => Uint8Array.from(atob(x.replace(/-/g, "+").replace(/_/g, "/") + "==".slice(0, (4 - x.length % 4) % 4)), (ch) => ch.charCodeAt(0));
      const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", kp.publicKey, dec(s), new TextEncoder().encode(h + "." + c));
      const claim = JSON.parse(new TextDecoder().decode(dec(c)));
      if (!ok || claim.scope !== "https://www.googleapis.com/auth/drive.readonly") return new Response("{}", { status: 400 });
      return new Response(JSON.stringify({ access_token: "GTOKEN", expires_in: 3600 }));
    }
    if (u.startsWith("https://www.googleapis.com/drive/v3/files/")) {
      if (new Headers(init?.headers).get("authorization") !== "Bearer GTOKEN") return new Response("{}", { status: 401 });
      if (!u.includes(ID)) return new Response("{}", { status: 404 });
      if (u.includes("alt=media")) return new Response(sample);
      if (u.includes("/export?")) return new Response("<html><body><h2>SEGMENT 1 — NATIVE</h2></body></html>");
      return new Response(JSON.stringify({ name: "Kit_LP12_20261120.docx", mimeType: w.mime, modifiedTime: "2026-11-19T06:00:00Z", size: String(sample.length) }));
    }
    return new Response("unexpected " + u, { status: 599 });
  };
}
function req(body: unknown, auth?: string, method = "POST") {
  const h: Record<string, string> = { "content-type": "application/json", origin: "https://sltimms90.github.io" };
  if (auth) h.authorization = auth;
  return new Request("https://proj.supabase.co/functions/v1/plan-doc", { method, headers: h, body: method === "POST" ? JSON.stringify(body) : undefined });
}
function assert(c: unknown, m: string) { if (!c) throw new Error(m); }

Deno.test("nobody but the teacher gets anything, and Drive is never asked", async () => {
  Deno.env.set("GOOGLE_SERVICE_ACCOUNT", SA);
  for (const [auth, teacher] of [[undefined, true], ["Bearer STUDENT", true], ["Bearer TEACHER", false]] as const) {
    const w: World = { teacher, mime: DOCX, calls: [] };
    const r = await handle(req({ docId: ID }, auth), fake(w));
    assert(r.status === 401, "401 for " + auth + "/" + teacher + ", got " + r.status);
    assert(!w.calls.some((u) => /google/.test(u)), "no Google call for a non-teacher");
    assert(!(await r.text()).includes("SEGMENT"), "no plan text");
  }
});
Deno.test("the teacher gets a .docx plan as plain HTML", async () => {
  Deno.env.set("GOOGLE_SERVICE_ACCOUNT", SA);
  const w: World = { teacher: true, mime: DOCX, calls: [] };
  const r = await handle(req({ docId: ID }, "Bearer TEACHER"), fake(w));
  assert(r.status === 200, "200, got " + r.status);
  assert(r.headers.get("access-control-allow-origin") === "https://sltimms90.github.io", "CORS for the app");
  const j = await r.json();
  assert(/<h2>SEGMENT 1 — TEACHING NOTES/.test(j.html) && /<h3>2A · The paper/.test(j.html), "headings kept");
  assert(/<strong>Key<\/strong>/.test(j.html), "bold labels kept");
  assert(!/style=/.test(j.html), "no inline styles");
  assert(j.name === "Kit_LP12_20261120.docx" && j.mime === DOCX, "name and type");
});
Deno.test("a native Google Doc is exported as HTML", async () => {
  const w: World = { teacher: true, mime: "application/vnd.google-apps.document", calls: [] };
  const j = await (await handle(req({ docId: ID }, "Bearer TEACHER"), fake(w))).json();
  assert(j.html.includes("SEGMENT 1 — NATIVE"), "exported");
});
Deno.test("bad ids, other files, unshared files, no key", async () => {
  const w: World = { teacher: true, mime: DOCX, calls: [] };
  assert((await handle(req({ docId: "../../etc" }, "Bearer TEACHER"), fake(w))).status === 400, "bad id 400");
  assert((await handle(req({ docId: "1ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ" }, "Bearer TEACHER"), fake(w))).status === 404, "not shared 404");
  const w2: World = { teacher: true, mime: "application/pdf", calls: [] };
  assert((await handle(req({ docId: ID }, "Bearer TEACHER"), fake(w2))).status === 415, "pdf 415");
  assert((await handle(req({}, "Bearer TEACHER", "GET"), fake(w))).status === 405, "GET 405");
  assert((await handle(new Request("https://x/", { method: "OPTIONS", headers: { origin: "https://evil.example" } }), fake(w))).headers.get("access-control-allow-origin") === "https://sltimms90.github.io", "CORS only names the app");
});
