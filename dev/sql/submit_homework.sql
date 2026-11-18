-- Homework links (Nov 2026): the one door a student's page has into the database.
-- Applied to project prglfopvovvxhzrejhzc as migration "submit_homework".
--
-- A student link (#s=) carries the lesson id, the game id and that game's token (packs.data.hw[<game id>],
-- 32 hex characters, made by the teacher's app; "New link" replaces it and old links stop saving).
-- The function only ever INSERTS one row into results, for that one lesson and game, built here from
-- whitelisted fields. It returns nothing it read. RLS on every table stays teacher-only.

create or replace function public.submit_homework(p_pack text, p_game text, p_token text, p_result jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_pack  jsonb;
  v_game  jsonb;
  v_sid   text;
  v_id    text;
  v_items jsonb;
  v_score jsonb;
  v_sum   text;
  v_when  text;
  v_secs  numeric;
  v_pts   numeric;
  v_data  jsonb;
  v_n     int;
begin
  -- shape of the call
  if p_pack is null or p_pack !~ '^[A-Za-z0-9_.~:@+-]{1,80}$'
     or p_game is null or p_game !~ '^[A-Za-z0-9_.~:@+-]{1,40}$'
     or p_token is null or p_token !~ '^[0-9a-f]{32}$' then
    raise exception 'bad_link';
  end if;
  if p_result is null or jsonb_typeof(p_result) <> 'object' then raise exception 'bad_result'; end if;
  if octet_length(p_result::text) > 65536 then raise exception 'too_big'; end if;

  -- the token must be the one the teacher's app made for this lesson + game
  select data into v_pack from public.packs where id = p_pack;
  if v_pack is null or jsonb_typeof(v_pack->'hw') <> 'object' or (v_pack->'hw'->>p_game) is distinct from p_token then
    raise exception 'bad_link';
  end if;
  select e into v_game from jsonb_array_elements(case when jsonb_typeof(v_pack->'games') = 'array' then v_pack->'games' else '[]'::jsonb end) e
    where e->>'id' = p_game limit 1;
  if v_game is null then raise exception 'bad_link'; end if;

  -- limits: 30 a day per lesson, 300 a day overall
  select count(*) into v_n from public.results
    where updated_at > now() - interval '1 day' and data->>'homework' = 'true' and data->>'packId' = p_pack;
  if v_n >= 30 then raise exception 'too_many'; end if;
  select count(*) into v_n from public.results
    where updated_at > now() - interval '1 day' and data->>'homework' = 'true';
  if v_n >= 300 then raise exception 'too_many'; end if;

  -- the play's own id: the same play sent twice is one row; a live game the teacher also saved is one row
  v_sid := p_result->>'sid';
  if v_sid is null or v_sid !~ '^L?[a-z0-9]{6,20}$' then raise exception 'bad_result'; end if;
  v_id := p_pack || '_' || p_game || '_' || v_sid;

  -- items: up to 300 objects, short scalar fields only
  select coalesce(jsonb_agg(c order by o), '[]'::jsonb) into v_items from (
    select o, (select coalesce(jsonb_object_agg(k, v), '{}'::jsonb) from jsonb_each(i) kv(k, v)
               where k ~ '^[a-zA-Z]{1,12}$'
                 and (jsonb_typeof(v) in ('number', 'boolean', 'null')
                      or (jsonb_typeof(v) = 'string' and char_length(v #>> '{}') <= 600))) c
    from jsonb_array_elements(case when jsonb_typeof(p_result->'items') = 'array' then p_result->'items' else '[]'::jsonb end)
         with ordinality a(i, o)
    where jsonb_typeof(i) = 'object' and o <= 300) s;

  if jsonb_typeof(p_result->'score') = 'object' then
    select coalesce(jsonb_object_agg(k, v), '{}'::jsonb) into v_score from jsonb_each(p_result->'score') kv(k, v)
      where k ~ '^[a-zA-Z]{1,12}$'
        and (jsonb_typeof(v) in ('number', 'boolean', 'null')
             or (jsonb_typeof(v) = 'string' and char_length(v #>> '{}') <= 200));
  end if;

  v_secs := case when jsonb_typeof(p_result->'activeSecs') = 'number' then least(greatest((p_result->>'activeSecs')::numeric, 0), 86400) else 0 end;
  v_pts  := case when jsonb_typeof(p_result->'points') = 'number' then least(greatest((p_result->>'points')::numeric, 0), 1000000) else null end;

  -- summary: "Title — ..." becomes "Title (homework, played 18 Nov 20:14) — ..."
  v_when := to_char(now() at time zone 'Asia/Taipei', 'FMDD Mon HH24:MI');
  v_sum  := case when jsonb_typeof(p_result->'summary') = 'string' then left(p_result->>'summary', 4000) else '' end;
  if position(' — ' in v_sum) > 0 then
    v_sum := regexp_replace(v_sum, '^(.*?) — ', '\1 (homework, played ' || v_when || ') — ');
  else
    v_sum := 'Homework, played ' || v_when || case when v_sum <> '' then ' — ' || v_sum else '' end;
  end if;

  v_data := jsonb_build_object(
    'id', v_id, 'packId', p_pack, 'student', coalesce(v_pack->>'student', ''), 'lp', v_pack->'lp',
    'gameId', p_game, 'type', v_game->>'type',
    'title', left(coalesce(nullif(v_game->>'title', ''), v_game->>'type'), 200) || ' (homework)',
    'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
    'summary', v_sum, 'score', v_score, 'items', v_items, 'activeSecs', round(v_secs),
    'points', v_pts, 'homework', true, 'online', true);
  if left(v_sid, 1) = 'L' then v_data := v_data || jsonb_build_object('liveGen', substr(v_sid, 2)); end if;

  insert into public.results (id, data) values (v_id, v_data) on conflict (id) do nothing;
  return jsonb_build_object('ok', true, 'new', found);
end;
$$;

revoke all on function public.submit_homework(text, text, text, jsonb) from public;
grant execute on function public.submit_homework(text, text, text, jsonb) to anon;
-- (student pages use the publishable key with no session, so only anon needs it; migration "submit_homework_anon_only")
