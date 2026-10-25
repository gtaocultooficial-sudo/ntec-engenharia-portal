alter table public.ntec_report_sequences
  add column if not exists last_series_number bigint not null default 0;

update public.ntec_report_sequences s
set last_series_number = greatest(
  s.last_series_number,
  coalesce((
    select max((r.structured_data #>> '{fields,series}')::bigint)
    from public.reports r
    where r.project_id = s.project_id
      and (r.structured_data #>> '{fields,series}') ~ '^[0-9]+$'
  ), 0)
);

create or replace function private.assign_ntec_sample_series()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare
  v_work_number bigint;
  v_last_series bigint := 0;
  v_requested bigint;
  v_series bigint;
  v_raw text;
  v_fields jsonb;
begin
  if not (coalesce(new.structured_data -> 'fields', '{}'::jsonb) ? 'series') then
    return new;
  end if;

  select p.work_number into v_work_number
  from public.projects p where p.id = new.project_id;
  if v_work_number is null then
    raise exception 'A obra ainda não possui número interno. Atualize o cadastro e tente novamente.';
  end if;

  insert into public.ntec_report_sequences
    (project_id, work_number, last_report_number, last_series_number)
  values (new.project_id, v_work_number, 0, 0)
  on conflict (project_id) do nothing;

  select s.last_series_number into v_last_series
  from public.ntec_report_sequences s
  where s.project_id = new.project_id for update;

  v_raw := coalesce(new.structured_data #>> '{fields,series}', '');
  if v_raw ~ '^[0-9]+$' then v_requested := v_raw::bigint; else v_requested := null; end if;

  if coalesce(v_last_series, 0) > 0 then
    v_series := greatest(coalesce(v_requested, v_last_series + 1), v_last_series + 1);
  else
    v_series := greatest(coalesce(v_requested, 1), 1);
  end if;

  v_fields := coalesce(new.structured_data -> 'fields', '{}'::jsonb)
              || jsonb_build_object('series', v_series::text);
  new.structured_data := jsonb_set(coalesce(new.structured_data, '{}'::jsonb), '{fields}', v_fields, true);

  update public.ntec_report_sequences set last_series_number = v_series
  where project_id = new.project_id;
  return new;
end;
$$;

create or replace function private.track_ntec_sample_series_updates()
returns trigger language plpgsql security definer set search_path = ''
as $$
declare
  v_work_number bigint;
  v_series_text text;
  v_series bigint;
begin
  v_series_text := coalesce(new.structured_data #>> '{fields,series}', '');
  if v_series_text !~ '^[0-9]+$' then return new; end if;
  v_series := v_series_text::bigint;

  select p.work_number into v_work_number from public.projects p where p.id = new.project_id;
  if v_work_number is null then return new; end if;

  insert into public.ntec_report_sequences
    (project_id, work_number, last_report_number, last_series_number)
  values (new.project_id, v_work_number, 0, v_series)
  on conflict (project_id) do update
  set last_series_number = greatest(public.ntec_report_sequences.last_series_number, excluded.last_series_number);
  return new;
end;
$$;

drop trigger if exists trg_assign_ntec_sample_series on public.reports;
create trigger trg_assign_ntec_sample_series before insert on public.reports
for each row execute function private.assign_ntec_sample_series();

drop trigger if exists trg_track_ntec_sample_series_updates on public.reports;
create trigger trg_track_ntec_sample_series_updates after update of structured_data on public.reports
for each row execute function private.track_ntec_sample_series_updates();

revoke all on function private.assign_ntec_sample_series() from public, anon, authenticated;
revoke all on function private.track_ntec_sample_series_updates() from public, anon, authenticated;