/* guest-account — the sign-in for a guest Sam has just added on the 🧪 Test page (27 Nov 2026).
   POST { email } with Sam's own sign-in (Authorization: Bearer <access token>) → { ok, created }.
   Sign-ups are closed on the project, so a guest can't make their own account. This makes it with the service role:
   email confirmed, no password (they sign in with the emailed link or code, as Sam does). It only does that for an email
   that is already on the guest list (rpc guest_list, asked as Sam), and it never changes or deletes an existing account.
   - Who: rpc am_i_teacher with the caller's token, the same rule as RLS. Anyone else gets 401 and nothing happens.
   - Being on the guest list is what lets an account see the showcase (private.is_guest); an account alone sees nothing.
   index.ts serves handle(); guest_test.ts tests it with a fake Supabase (deno test --allow-env).
   Deployed with verify_jwt off because the teacher check is stricter than a valid-JWT check. */

const ORIGINS = ["https://sltimms90.github.io"];
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

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
/* An rpc as the caller (their token), or null on any failure. */
async function rpcAsCaller(req: Request, fn: string, fetchFn: typeof fetch): Promise<unknown> {
  const auth = req.headers.get("authorization") || "";
  if (!/^Bearer\s+\S+/.test(auth)) return null;
  const url = Deno.env.get("SUPABASE_URL"), key = req.headers.get("apikey") || Deno.env.get("SUPABASE_ANON_KEY") || "";
  if (!url || !key) return null;
  try {
    const r = await fetchFn(url + "/rest/v1/rpc/" + fn, { method: "POST", headers: { apikey: key, Authorization: auth, "Content-Type": "application/json" }, body: "{}" });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

export async function handle(req: Request, fetchFn: typeof fetch = fetch): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(req) });
  if (req.method !== "POST") return reply(req, 405, { error: "method" });
  if ((await rpcAsCaller(req, "am_i_teacher", fetchFn)) !== true) return reply(req, 401, { error: "not_teacher" });
  let email = "";
  try { email = String((await req.json()).email || "").trim().toLowerCase(); } catch { /* bad body */ }
  if (!EMAIL.test(email) || email.length > 200) return reply(req, 400, { error: "bad_email" });
  const list = await rpcAsCaller(req, "guest_list", fetchFn);
  if (!Array.isArray(list) || !list.some((g) => g && String((g as { email?: string }).email) === email)) return reply(req, 409, { error: "not_on_list" });
  const url = Deno.env.get("SUPABASE_URL"), svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !svc) return reply(req, 503, { error: "not_set_up" });
  try {
    const r = await fetchFn(url + "/auth/v1/admin/users", { method: "POST", headers: { apikey: svc, Authorization: "Bearer " + svc, "Content-Type": "application/json" },
      body: JSON.stringify({ email, email_confirm: true }) });
    if (r.ok) return reply(req, 200, { ok: true, created: true });
    const j = await r.json().catch(() => ({})) as { code?: string; error_code?: string; msg?: string; message?: string };
    const code = String(j.error_code || j.code || ""), msg = String(j.msg || j.message || "");
    if (r.status === 422 && (/email_exists|user_already_exists/.test(code) || /already (been )?registered|already exists/i.test(msg))) return reply(req, 200, { ok: true, created: false });
    console.error("guest-account", r.status, code);
    return reply(req, 502, { error: "auth" });
  } catch (e) {
    console.error("guest-account", e);
    return reply(req, 500, { error: "failed" });
  }
}
