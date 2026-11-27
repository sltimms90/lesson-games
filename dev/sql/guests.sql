-- Guest accounts and the showcase school (27 Nov 2026), migration "guest_showcase".
-- A guest (an email on private.guests, signed in) reads and writes ONLY the showcase: students whose students.data has
-- "showcase": true, and the lessons, results, run sheets and Phase B rows of those students' showcase lessons. Showcase
-- lesson ids start "~sc-" (slug() can't make "~", so no planning chat or app lesson ever gets one by accident).
-- Sam's "teacher full access" policies are untouched; policies are OR'd, so nothing here narrows what Sam can do.
--
-- Rules, enforced here and not by the page:
--   * a guest can't create or delete a student, can't set test or clear showcase on one, and can't change any row's id;
--   * every row a guest writes must still belong to a showcase lesson afterwards (WITH CHECK on every table), so a row
--     can't be moved to a real student or a real lesson;
--   * if a REAL lesson ever names a showcase student (a real "Leo"), that student stops being showcase for guests at once:
--     the guest loses the student and all of its lessons rather than ever seeing a row the real Leo might touch;
--   * boards: read-only, only boards marked showcase. game-pictures: the bucket is public (anyone can open a picture by
--     its address), and uploads stay teacher-only.

create table if not exists private.guests (
  email text primary key check (email = lower(email) and email ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
  added_at timestamptz not null default now()
);
alter table private.guests enable row level security;   -- no policies and no grants: only the functions below touch it
revoke all on private.guests from anon, authenticated;

-- Built like is_teacher(): security definer, empty search_path, email from the caller's JWT.
create or replace function private.is_guest() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce((auth.jwt() ->> 'role') = 'authenticated', false)
     and exists (select 1 from private.guests g where g.email = lower(auth.jwt() ->> 'email'));
$$;
revoke all on function private.is_guest() from public, anon;
grant execute on function private.is_guest() to authenticated;

create or replace function public.am_i_guest() returns boolean
language sql stable set search_path = '' as $$ select private.is_guest(); $$;
revoke all on function public.am_i_guest() from public, anon;
grant execute on function public.am_i_guest() to authenticated, service_role;

-- The app's slug(): lower case, runs of anything but a-z 0-9 → "-", trimmed of "-", "student" if empty.
create or replace function private.slug(n text) returns text
language sql immutable set search_path = '' as $$
  select coalesce(nullif(regexp_replace(regexp_replace(lower(coalesce(n, '')), '[^a-z0-9]+', '-', 'g'), '^-+|-+$', '', 'g'), ''), 'student');
$$;

-- A showcase student: flagged showcase (and not test), and no real lesson (id not "~sc-…") names it.
create or replace function private.is_showcase_name(n text) returns boolean
language sql stable security definer set search_path = '' as $$
  select n is not null and exists (
    select 1 from public.students s
    where s.id = private.slug(n) and s.data -> 'showcase' = 'true'::jsonb and coalesce(s.data -> 'test', 'false'::jsonb) <> 'true'::jsonb
      and not exists (select 1 from public.packs p where p.id not like '~sc-%' and private.slug(p.data ->> 'student') = s.id));
$$;
create or replace function private.is_showcase_student(sid text, d jsonb) returns boolean
language sql stable set search_path = '' as $$
  select d -> 'showcase' = 'true'::jsonb and coalesce(d -> 'test', 'false'::jsonb) <> 'true'::jsonb and private.is_showcase_name(d ->> 'name')
     and private.slug(d ->> 'name') = sid;
$$;
create or replace function private.is_showcase_pack_row(pid text, d jsonb) returns boolean
language sql stable set search_path = '' as $$
  select pid like '~sc-%' and private.is_showcase_name(d ->> 'student');
$$;
create or replace function private.is_showcase_pack(pid text) returns boolean
language sql stable security definer set search_path = '' as $$
  select pid like '~sc-%' and exists (select 1 from public.packs p where p.id = pid and private.is_showcase_pack_row(p.id, p.data));
$$;
revoke all on function private.slug(text), private.is_showcase_name(text), private.is_showcase_student(text, jsonb),
  private.is_showcase_pack_row(text, jsonb), private.is_showcase_pack(text) from public, anon;
grant execute on function private.slug(text), private.is_showcase_name(text), private.is_showcase_student(text, jsonb),
  private.is_showcase_pack_row(text, jsonb), private.is_showcase_pack(text) to authenticated;

-- A guest never changes a row's id (or a Phase B row's pack_id): one showcase row can't be turned into a new student or
-- lesson. Sam, the planning chats and the database's own jobs are not affected.
create or replace function private.keep_id() returns trigger
language plpgsql set search_path = '' as $$
begin
  if private.is_guest() and not private.is_teacher() then
    if (to_jsonb(old) ->> tg_argv[0]) is distinct from (to_jsonb(new) ->> tg_argv[0]) then
      raise exception 'id_locked' using errcode = '42501';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists keep_id on public.students; create trigger keep_id before update on public.students for each row execute function private.keep_id('id');
drop trigger if exists keep_id on public.packs;    create trigger keep_id before update on public.packs    for each row execute function private.keep_id('id');
drop trigger if exists keep_id on public.results;  create trigger keep_id before update on public.results  for each row execute function private.keep_id('id');
drop trigger if exists keep_id on public.sheets;   create trigger keep_id before update on public.sheets   for each row execute function private.keep_id('id');
drop trigger if exists keep_id on public.phaseb;   create trigger keep_id before update on public.phaseb   for each row execute function private.keep_id('pack_id');
drop trigger if exists keep_id on public.boards;   create trigger keep_id before update on public.boards   for each row execute function private.keep_id('id');

-- students: read and edit the showcase students; no insert, no delete.
drop policy if exists "guest reads showcase students" on public.students;
create policy "guest reads showcase students" on public.students for select to authenticated
  using ((select private.is_guest()) and private.is_showcase_student(id, data));
drop policy if exists "guest edits showcase students" on public.students;
create policy "guest edits showcase students" on public.students for update to authenticated
  using ((select private.is_guest()) and private.is_showcase_student(id, data))
  with check ((select private.is_guest()) and private.is_showcase_student(id, data));
-- The app saves with an upsert (INSERT … ON CONFLICT DO UPDATE), which Postgres checks against INSERT policies too. This one
-- passes only for a student that already exists as a showcase student (is_showcase_name looks the row up), so the upsert
-- reaches the UPDATE rules above and a guest still can't create a student (migration guest_showcase_student_upsert).
drop policy if exists "guest saves showcase students" on public.students;
create policy "guest saves showcase students" on public.students for insert to authenticated
  with check ((select private.is_guest()) and private.is_showcase_student(id, data));

-- packs: the showcase lessons; a new one must be a showcase lesson ("~sc-…") of a showcase student.
drop policy if exists "guest showcase lessons" on public.packs;
create policy "guest showcase lessons" on public.packs for all to authenticated
  using ((select private.is_guest()) and private.is_showcase_pack_row(id, data))
  with check ((select private.is_guest()) and private.is_showcase_pack_row(id, data));

-- results: id and lesson both showcase, and the result's student a showcase student.
drop policy if exists "guest showcase results" on public.results;
create policy "guest showcase results" on public.results for all to authenticated
  using ((select private.is_guest()) and id like '~sc-%' and private.is_showcase_pack(data ->> 'packId') and private.is_showcase_name(data ->> 'student'))
  with check ((select private.is_guest()) and id like '~sc-%' and private.is_showcase_pack(data ->> 'packId') and private.is_showcase_name(data ->> 'student'));

-- sheets: keyed by the lesson's id.
drop policy if exists "guest showcase sheets" on public.sheets;
create policy "guest showcase sheets" on public.sheets for all to authenticated
  using ((select private.is_guest()) and private.is_showcase_pack(id) and coalesce(data ->> 'packId', id) = id)
  with check ((select private.is_guest()) and private.is_showcase_pack(id) and coalesce(data ->> 'packId', id) = id);

-- phaseb: one row per lesson.
drop policy if exists "guest showcase phaseb" on public.phaseb;
create policy "guest showcase phaseb" on public.phaseb for all to authenticated
  using ((select private.is_guest()) and private.is_showcase_pack(pack_id))
  with check ((select private.is_guest()) and private.is_showcase_pack(pack_id));

-- boards: read only, showcase boards only (the Snakes & Ladders board the showcase games use).
drop policy if exists "guest reads showcase boards" on public.boards;
create policy "guest reads showcase boards" on public.boards for select to authenticated
  using ((select private.is_guest()) and data -> 'showcase' = 'true'::jsonb);

-- The guest list, for Sam's 🧪 Test page. Teacher only; anyone else gets nothing / an error.
create or replace function public.guest_list() returns table (email text, added_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select g.email, g.added_at from private.guests g where private.is_teacher() order by g.added_at, g.email;
$$;
create or replace function public.guest_add(p_email text) returns void
language plpgsql security definer set search_path = '' as $$
declare e text := lower(btrim(coalesce(p_email, '')));
begin
  if not private.is_teacher() then raise exception 'not_teacher' using errcode = '42501'; end if;
  if e !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' or length(e) > 200 then raise exception 'bad_email'; end if;
  insert into private.guests (email) values (e) on conflict (email) do nothing;
end $$;
create or replace function public.guest_remove(p_email text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not private.is_teacher() then raise exception 'not_teacher' using errcode = '42501'; end if;
  delete from private.guests where email = lower(btrim(coalesce(p_email, '')));
end $$;
revoke all on function public.guest_list(), public.guest_add(text), public.guest_remove(text) from public, anon;
grant execute on function public.guest_list(), public.guest_add(text), public.guest_remove(text) to authenticated;

-- Showcase plans (migration "showcase_plans"): the made-up school's lesson plans, which plan-doc serves for "showcase-…"
-- docIds instead of fetching from Drive. Loaded by dev/sql/showcase_plans.sql (written by dev/build.py). No grants: only
-- public.showcase_plan reads it, and only for the teacher or a guest.
create table if not exists private.showcase_plans (
  doc_id text primary key check (doc_id ~ '^showcase-[a-z0-9-]{11,119}$'),
  name text not null, folder_id text not null default '', html text not null, updated_at timestamptz not null default now()
);
alter table private.showcase_plans enable row level security;
revoke all on private.showcase_plans from anon, authenticated;
create or replace function public.showcase_plan(p_doc text) returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object('html', p.html, 'name', p.name, 'folderId', p.folder_id) from private.showcase_plans p
  where p.doc_id = p_doc and (private.is_teacher() or private.is_guest());
$$;
revoke all on function public.showcase_plan(text) from public, anon;
grant execute on function public.showcase_plan(text) to authenticated;
