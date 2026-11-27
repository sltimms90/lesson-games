/* deno test --allow-env dev/functions/guest-account/guest_test.ts
   A fake Supabase: am_i_teacher / guest_list as the caller, and the auth admin endpoint. */
import { handle } from "./guest.ts";

Deno.env.set("SUPABASE_URL", "https://proj.supabase.co");
Deno.env.set("SUPABASE_ANON_KEY", "anon");
Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "SVC");

type World = { users: string[]; guests: string[]; calls: string[]; adminAuth: string[] };
function fake(w: World) {
  return async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const u = String(input), a = new Headers(init?.headers).get("authorization"); w.calls.push(u);
    if (u.endsWith("/rest/v1/rpc/am_i_teacher")) return new Response(JSON.stringify(a === "Bearer TEACHER"));
    if (u.endsWith("/rest/v1/rpc/guest_list")) return new Response(JSON.stringify(a === "Bearer TEACHER" ? w.guests.map((email) => ({ email, added_at: "2026-11-27T00:00:00Z" })) : []));
    if (u.endsWith("/auth/v1/admin/users")) {
      w.adminAuth.push(String(a));
      if (a !== "Bearer SVC") return new Response("{}", { status: 401 });
      const b = JSON.parse(String(init?.body));
      if (b.email_confirm !== true || "password" in b) return new Response("{}", { status: 400 });
      if (w.users.includes(b.email)) return new Response(JSON.stringify({ code: 422, error_code: "email_exists", msg: "A user with this email address has already been registered" }), { status: 422 });
      w.users.push(b.email); return new Response(JSON.stringify({ id: "u1", email: b.email }));
    }
    return new Response("unexpected " + u, { status: 599 });
  };
}
function req(body: unknown, auth?: string, method = "POST") {
  const h: Record<string, string> = { "content-type": "application/json", origin: "https://sltimms90.github.io" };
  if (auth) h.authorization = auth;
  return new Request("https://proj.supabase.co/functions/v1/guest-account", { method, headers: h, body: method === "POST" ? JSON.stringify(body) : undefined });
}
function assert(c: unknown, m: string) { if (!c) throw new Error(m); }

Deno.test("only the teacher, and only for an email on the guest list", async () => {
  const w: World = { users: [], guests: ["friend@example.com"], calls: [], adminAuth: [] };
  for (const auth of [undefined, "Bearer GUEST", "Bearer STRANGER"]) {
    const r = await handle(req({ email: "friend@example.com" }, auth), fake(w));
    assert(r.status === 401, "401 for " + auth + ", got " + r.status);
  }
  assert(!w.adminAuth.length, "the admin endpoint is never called for a non-teacher");
  const r = await handle(req({ email: "someone@example.com" }, "Bearer TEACHER"), fake(w));
  assert(r.status === 409 && !w.adminAuth.length, "not on the guest list: 409, no account made");
  assert((await handle(req({ email: "not an email" }, "Bearer TEACHER"), fake(w))).status === 400, "bad email 400");
  assert((await handle(req({}, "Bearer TEACHER", "GET"), fake(w))).status === 405, "GET 405");
});
Deno.test("makes a confirmed, passwordless account once; an existing one is left alone", async () => {
  const w: World = { users: ["old@example.com"], guests: ["friend@example.com", "old@example.com"], calls: [], adminAuth: [] };
  let j = await (await handle(req({ email: " Friend@Example.com " }, "Bearer TEACHER"), fake(w))).json();
  assert(j.ok === true && j.created === true && w.users.includes("friend@example.com"), "created");
  j = await (await handle(req({ email: "old@example.com" }, "Bearer TEACHER"), fake(w))).json();
  assert(j.ok === true && j.created === false && w.users.filter((x) => x === "old@example.com").length === 1, "already there: ok, not created");
  assert(w.adminAuth.every((x) => x === "Bearer SVC"), "the service key only ever goes to the admin endpoint");
});
