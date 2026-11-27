-- Guest access, tested against the real database (27 Nov 2026). Run it whole in the SQL editor (or MCP execute_sql).
-- It ALWAYS rolls itself back: it ends by raising its own result, so nothing it adds or changes is ever kept.
--   ALL PASS (n checks)   → every rule held          FAIL: …   → the first rule that didn't
-- As the owner it adds throwaway fixtures (a guest email, a showcase student "RLS SC Kid" and a sandbox test student with a
-- lesson, result, run sheet and Phase B row each, and a showcase board), then acts as: a guest on the list, a signed-in
-- stranger, anon, and Sam (his email is read from private.is_teacher(), so it isn't written here), through the same JWT
-- claims PostgREST sets. Real students' rows are only ever counted by the owner, never changed.
do $$
declare
  n int; m int; ok int := 0; failed boolean;
  G constant text := 'guest-rls-test@example.invalid';
  S constant text := 'stranger-rls-test@example.invalid';
  T text := substring(pg_get_functiondef('private.is_teacher'::regproc) from '''([^'' ]+@[^'' ]+)''');
  real_pack text; real_student text; real_name text; real_result text;
  before jsonb; after jsonb;
begin
  -- ---------- fixtures, as the owner ----------
  select id into real_pack from public.packs where id not like '~sc-%' order by id limit 1;
  select id, data ->> 'name' into real_student, real_name from public.students where id <> '~teacher' and data ->> 'name' <> '' and not coalesce(data -> 'showcase' = 'true'::jsonb, false) order by id limit 1;
  select id into real_result from public.results where id not like '~sc-%' order by id limit 1;
  if real_pack is null or real_student is null or real_result is null or T is null then raise exception 'FAIL: fixtures: no real rows to test against, or no teacher email'; end if;
  insert into private.guests (email) values (G);
  insert into public.students (id, data) values
    ('rls-sc-kid', '{"id":"rls-sc-kid","name":"RLS SC Kid","showcase":true}'),
    ('rls-test-kid', '{"id":"rls-test-kid","name":"RLS Test Kid","test":true}'),
    ('rls-both-kid', '{"id":"rls-both-kid","name":"RLS Both Kid","test":true,"showcase":true}');
  insert into public.packs (id, data) values
    ('~sc-rls-sc-kid-lp1', '{"id":"~sc-rls-sc-kid-lp1","student":"RLS SC Kid","lp":1}'),
    ('rls-test-kid-lp1', '{"id":"rls-test-kid-lp1","student":"RLS Test Kid","lp":1}'),
    ('~sc-rls-both-kid-lp1', '{"id":"~sc-rls-both-kid-lp1","student":"RLS Both Kid","lp":1}');
  insert into public.results (id, data) values
    ('~sc-rls-sc-kid-lp1_g1_x', '{"id":"~sc-rls-sc-kid-lp1_g1_x","packId":"~sc-rls-sc-kid-lp1","student":"RLS SC Kid"}'),
    ('rls-test-kid-lp1_g1_x', '{"id":"rls-test-kid-lp1_g1_x","packId":"rls-test-kid-lp1","student":"RLS Test Kid"}');
  insert into public.sheets (id, data) values ('~sc-rls-sc-kid-lp1', '{"id":"~sc-rls-sc-kid-lp1","packId":"~sc-rls-sc-kid-lp1"}'), ('rls-test-kid-lp1', '{"id":"rls-test-kid-lp1","packId":"rls-test-kid-lp1"}');
  insert into public.phaseb (pack_id, status, by) values ('~sc-rls-sc-kid-lp1', 'done', 'manual'), ('rls-test-kid-lp1', 'done', 'manual');
  insert into public.boards (id, data) values ('~sc-rls-board', '{"id":"~sc-rls-board","name":"RLS board","showcase":true}');
  select jsonb_build_object('packs', (select jsonb_agg(md5(data::text) order by id) from public.packs where id not like '~sc-%'),
    'results', (select jsonb_agg(md5(data::text) order by id) from public.results where id not like '~sc-%'),
    'students', (select jsonb_agg(md5(data::text) order by id) from public.students where not coalesce(data -> 'showcase' = 'true'::jsonb, false)),
    'sheets', (select jsonb_agg(md5(data::text) order by id) from public.sheets where id not like '~sc-%'),
    'phaseb', (select jsonb_agg(md5(to_jsonb(b)::text) order by pack_id) from public.phaseb b where pack_id not like '~sc-%'),
    'boards', (select jsonb_agg(md5(data::text) order by id) from public.boards where not coalesce(data -> 'showcase' = 'true'::jsonb, false))) into before;

  -- ================= a guest on the list =================
  perform set_config('request.jwt.claims', json_build_object('role', 'authenticated', 'email', upper(G))::text, true);
  execute 'set local role authenticated';
  if not (select public.am_i_guest()) or (select public.am_i_teacher()) then raise exception 'FAIL: am_i_guest / am_i_teacher for the guest'; end if; ok := ok + 1;
  -- reads: showcase rows only, from every table
  select count(*) into n from public.students where not coalesce(data -> 'showcase' = 'true'::jsonb, false) or coalesce(data -> 'test' = 'true'::jsonb, false);
  if n <> 0 then raise exception 'FAIL: guest sees % non-showcase / test students', n; end if; ok := ok + 1;
  if not exists (select 1 from public.students where id = 'rls-sc-kid') then raise exception 'FAIL: guest can''t see the showcase student'; end if; ok := ok + 1;
  select count(*) into n from public.packs where id not like '~sc-%' or id = '~sc-rls-both-kid-lp1'; if n <> 0 then raise exception 'FAIL: guest sees % real / test lessons', n; end if; ok := ok + 1;
  if not exists (select 1 from public.packs where id = '~sc-rls-sc-kid-lp1') then raise exception 'FAIL: guest can''t see the showcase lesson'; end if; ok := ok + 1;
  select count(*) into n from public.results where id not like '~sc-%'; if n <> 0 then raise exception 'FAIL: guest sees % real / test results', n; end if; ok := ok + 1;
  select count(*) into n from public.sheets where id not like '~sc-%'; if n <> 0 then raise exception 'FAIL: guest sees % real / test run sheets', n; end if; ok := ok + 1;
  select count(*) into n from public.phaseb where pack_id not like '~sc-%'; if n <> 0 then raise exception 'FAIL: guest sees % real / test Phase B rows', n; end if; ok := ok + 1;
  select count(*) into n from public.boards where not coalesce(data -> 'showcase' = 'true'::jsonb, false); if n <> 0 then raise exception 'FAIL: guest sees % of Sam''s boards', n; end if; ok := ok + 1;
  select count(*) into n from public.guest_list(); if n <> 0 then raise exception 'FAIL: guest reads the guest list'; end if; ok := ok + 1;
  failed := false; begin perform public.guest_add('x@example.invalid'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest added a guest'; end if; ok := ok + 1;
  -- writes that must be refused (an error) or reach nothing (0 rows)
  failed := false; begin insert into public.packs (id, data) values ('~sc-' || real_student || '-lp99', jsonb_build_object('student', real_name)); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest made a lesson for a non-showcase student'; end if; ok := ok + 1;
  failed := false; begin insert into public.packs (id, data) values ('rls-sc-kid-lp2', '{"student":"RLS SC Kid"}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest made a lesson without a ~sc- id'; end if; ok := ok + 1;
  failed := false; begin insert into public.packs (id, data) values ('~sc-rls-test-kid-lp2', '{"student":"RLS Test Kid"}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest made a lesson for a test student'; end if; ok := ok + 1;
  insert into public.packs (id, data) values ('~sc-rls-sc-kid-lp2', '{"id":"~sc-rls-sc-kid-lp2","student":"RLS SC Kid","lp":2}');   -- allowed: a showcase lesson
  insert into public.packs (id, data) values ('~sc-rls-sc-kid-lp2', '{"id":"~sc-rls-sc-kid-lp2","student":"RLS SC Kid","lp":3}') on conflict (id) do update set data = excluded.data;   -- the app's upsert
  ok := ok + 1;
  update public.packs set data = data || '{"x":1}' where id = real_pack; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest changed a real lesson'; end if; ok := ok + 1;
  delete from public.packs where id = real_pack; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest deleted a real lesson'; end if; ok := ok + 1;
  failed := false; begin insert into public.packs (id, data) values (real_pack, '{"student":"RLS SC Kid"}') on conflict (id) do update set data = excluded.data; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest overwrote a real lesson by upsert'; end if; ok := ok + 1;
  failed := false; begin update public.packs set data = jsonb_set(data, '{student}', to_jsonb(real_name)) where id = '~sc-rls-sc-kid-lp1'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest moved a showcase lesson to another student'; end if; ok := ok + 1;
  failed := false; begin update public.packs set id = '~sc-rls-sc-kid-lp7' where id = '~sc-rls-sc-kid-lp1'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest changed a lesson''s id'; end if; ok := ok + 1;
  -- students: no new ones, no flag changes, no real ones; the app's upsert of a showcase student works
  failed := false; begin insert into public.students (id, data) values ('rls-new-kid', '{"id":"rls-new-kid","name":"RLS New Kid","showcase":true}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest created a student'; end if; ok := ok + 1;
  failed := false; begin insert into public.students (id, data) values (real_student, jsonb_build_object('id', real_student, 'name', real_student, 'showcase', true)) on conflict (id) do update set data = excluded.data; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest flipped showcase on a real student (upsert)'; end if; ok := ok + 1;
  update public.students set data = data || '{"showcase":true}' where id = real_student; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest flipped showcase on a real student (update)'; end if; ok := ok + 1;
  failed := false; begin update public.students set data = data || '{"test":true}' where id = 'rls-sc-kid'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest set test on a showcase student'; end if; ok := ok + 1;
  failed := false; begin update public.students set data = data - 'showcase' where id = 'rls-sc-kid'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest cleared showcase on a showcase student'; end if; ok := ok + 1;
  failed := false; begin update public.students set id = 'rls-renamed' where id = 'rls-sc-kid'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest changed a student''s id'; end if; ok := ok + 1;
  delete from public.students where id = 'rls-sc-kid'; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest deleted a student'; end if; ok := ok + 1;
  insert into public.students (id, data) values ('rls-sc-kid', '{"id":"rls-sc-kid","name":"RLS SC Kid","showcase":true,"look":"chalk"}') on conflict (id) do update set data = excluded.data;   -- Reset demo's save
  ok := ok + 1;
  -- results, run sheets, Phase B: only for showcase lessons, and they can't be moved off one
  failed := false; begin insert into public.results (id, data) values ('~sc-x_g1_y', jsonb_build_object('packId', real_pack, 'student', 'RLS SC Kid')); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest added a result to a real lesson'; end if; ok := ok + 1;
  failed := false; begin insert into public.results (id, data) values ('plain_g1_y', '{"packId":"~sc-rls-sc-kid-lp1","student":"RLS SC Kid"}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest added a result without a ~sc- id'; end if; ok := ok + 1;
  failed := false; begin update public.results set data = jsonb_set(data, '{packId}', to_jsonb(real_pack)) where id = '~sc-rls-sc-kid-lp1_g1_x'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest moved a result to a real lesson'; end if; ok := ok + 1;
  update public.results set data = data || '{"x":1}' where id = real_result; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest changed a real result'; end if; ok := ok + 1;
  insert into public.results (id, data) values ('~sc-rls-sc-kid-lp2_g1_z', '{"packId":"~sc-rls-sc-kid-lp2","student":"RLS SC Kid"}'); ok := ok + 1;
  failed := false; begin insert into public.sheets (id, data) values (real_pack, jsonb_build_object('packId', real_pack)) on conflict (id) do update set data = excluded.data; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest wrote a real lesson''s run sheet'; end if; ok := ok + 1;
  failed := false; begin insert into public.sheets (id, data) values ('~sc-rls-sc-kid-lp2', '{"packId":"~sc-rls-sc-kid-lp1"}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest wrote a run sheet pointing at another lesson'; end if; ok := ok + 1;
  insert into public.sheets (id, data) values ('~sc-rls-sc-kid-lp2', '{"packId":"~sc-rls-sc-kid-lp2"}'); ok := ok + 1;
  failed := false; begin insert into public.phaseb (pack_id, status, by) values (real_pack, 'done', 'manual') on conflict (pack_id) do update set status = excluded.status; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest wrote a real lesson''s Phase B'; end if; ok := ok + 1;
  failed := false; begin update public.phaseb set pack_id = 'rls-test-kid-lp1' where pack_id = '~sc-rls-sc-kid-lp1'; exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest moved a Phase B row'; end if; ok := ok + 1;
  insert into public.phaseb (pack_id, status, by) values ('~sc-rls-sc-kid-lp2', 'skip', 'manual') on conflict (pack_id) do update set status = excluded.status; ok := ok + 1;
  failed := false; begin insert into public.boards (id, data) values ('~sc-rls-board2', '{"showcase":true}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest made a board'; end if; ok := ok + 1;
  update public.boards set data = data || '{"x":1}' where id = '~sc-rls-board'; get diagnostics n = row_count; if n <> 0 then raise exception 'FAIL: guest changed a board'; end if; ok := ok + 1;
  -- Reset demo's deletes: everything the guest can delete, at once; only showcase rows go
  delete from public.results; delete from public.sheets; delete from public.phaseb; delete from public.packs;
  ok := ok + 1;
  failed := false; begin insert into storage.objects (bucket_id, name) values ('game-pictures', '0123456789abcdef0123456789abcdef.png'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: guest uploaded a picture'; end if; ok := ok + 1;

  -- ================= a real lesson names a showcase student: switched off for guests at once =================
  execute 'reset role';
  insert into public.packs (id, data) values ('~sc-rls-sc-kid-lp5', '{"student":"RLS SC Kid"}'), ('rls-sc-kid-lp5', '{"student":"RLS SC Kid"}');
  execute 'set local role authenticated';
  select count(*) into n from public.packs where data ->> 'student' = 'RLS SC Kid'; select count(*) into m from public.students where id = 'rls-sc-kid';
  if n + m <> 0 then raise exception 'FAIL: a showcase student a real lesson names is still visible to guests (% lessons, % student)', n, m; end if; ok := ok + 1;

  -- ================= a signed-in stranger (not on the list) =================
  execute 'reset role';
  perform set_config('request.jwt.claims', json_build_object('role', 'authenticated', 'email', S)::text, true);
  execute 'set local role authenticated';
  if (select public.am_i_guest()) or (select public.am_i_teacher()) then raise exception 'FAIL: the stranger is a guest or teacher'; end if; ok := ok + 1;
  select (select count(*) from public.students) + (select count(*) from public.packs) + (select count(*) from public.results) + (select count(*) from public.sheets)
       + (select count(*) from public.phaseb) + (select count(*) from public.boards) + (select count(*) from public.guest_list()) into n;
  if n <> 0 then raise exception 'FAIL: a signed-in stranger sees % rows', n; end if; ok := ok + 1;
  failed := false; begin insert into public.packs (id, data) values ('~sc-rls-sc-kid-lp6', '{"student":"RLS SC Kid"}'); exception when others then failed := true; end;
  if not failed then raise exception 'FAIL: a stranger wrote a lesson'; end if; ok := ok + 1;

  -- ================= anon =================
  execute 'reset role';
  perform set_config('request.jwt.claims', json_build_object('role', 'anon')::text, true);
  execute 'set local role anon';
  failed := false; begin select count(*) into n from public.packs; exception when others then failed := true; n := 0; end;
  if n <> 0 then raise exception 'FAIL: anon sees % lessons', n; end if; ok := ok + 1;

  -- ================= Sam: everything, as before =================
  execute 'reset role';
  select count(*) into m from public.packs;
  perform set_config('request.jwt.claims', json_build_object('role', 'authenticated', 'email', T)::text, true);
  execute 'set local role authenticated';
  select count(*) into n from public.packs; if n <> m or not (select public.am_i_teacher()) then raise exception 'FAIL: Sam sees % of % lessons', n, m; end if; ok := ok + 1;
  select count(*) into n from public.guest_list(); if n < 1 then raise exception 'FAIL: Sam can''t read the guest list'; end if; ok := ok + 1;

  -- ================= nothing real was touched =================
  execute 'reset role';
  select jsonb_build_object('packs', (select jsonb_agg(md5(data::text) order by id) from public.packs where id not like '~sc-%' and id <> 'rls-sc-kid-lp5'),
    'results', (select jsonb_agg(md5(data::text) order by id) from public.results where id not like '~sc-%'),
    'students', (select jsonb_agg(md5(data::text) order by id) from public.students where not coalesce(data -> 'showcase' = 'true'::jsonb, false)),
    'sheets', (select jsonb_agg(md5(data::text) order by id) from public.sheets where id not like '~sc-%'),
    'phaseb', (select jsonb_agg(md5(to_jsonb(b)::text) order by pack_id) from public.phaseb b where pack_id not like '~sc-%'),
    'boards', (select jsonb_agg(md5(data::text) order by id) from public.boards where not coalesce(data -> 'showcase' = 'true'::jsonb, false))) into after;
  if after is distinct from before then raise exception 'FAIL: a real or test row changed during the guest''s writes'; end if; ok := ok + 1;

  raise exception 'ALL PASS (% checks) — rolled back, nothing kept', ok;
end $$;
