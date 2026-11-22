-- Phase B record: one row per lesson pack once its after-class report (Phase B) is done or not needed.
-- Applied to the project as migration `phaseb`.
--
-- A table of its own, not a field in packs.data: the app saves a pack by upserting its whole `data` from the copy it holds
-- (STORE.savePack), so an iPad with a stale copy (offline, or a missed Realtime change) would wipe a mark a planning chat
-- had written in the meantime. Nothing in the app ever writes this table except the Phase B screen.
--
-- Written by:
--   a planning chat at the end of Phase B (Supabase connector, execute_sql), by = 'chat':
--     insert into public.phaseb (pack_id, status, by) values ('<pack id>', 'done', 'chat')
--     on conflict (pack_id) do update set status = excluded.status, at = now(), by = excluded.by, note = excluded.note;
--   the Phase B screen on Lesson Desk, by = 'manual' (mark done, not needed, the launch "everything before" action; undo deletes).
-- Teacher only, like every other table: students' pages never read it.

create table if not exists public.phaseb (
  pack_id text primary key,
  status  text not null check (status in ('done', 'skip')),
  at      timestamptz not null default now(),
  by      text not null default 'chat' check (by in ('chat', 'manual')),
  note    text
);
alter table public.phaseb enable row level security;
alter table public.phaseb replica identity full;
revoke all on public.phaseb from anon;
grant select, insert, update, delete on public.phaseb to authenticated;
create policy "teacher full access" on public.phaseb for all to authenticated
  using ((select private.is_teacher())) with check ((select private.is_teacher()));
alter publication supabase_realtime add table public.phaseb;
