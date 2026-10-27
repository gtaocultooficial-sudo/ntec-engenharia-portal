-- NTEC Engenharia: classificar propostas aprovadas e preparar programação.
-- Esta migração já foi aplicada ao projeto Supabase NTEC.
alter table public.proposals
  add column if not exists service_mode text null
    check (service_mode is null or service_mode = any (array['mensal','diaria','pontual','revisar'])),
  add column if not exists staff_count integer null
    check (staff_count is null or staff_count between 1 and 100),
  add column if not exists service_start_date date null,
  add column if not exists service_end_date date null,
  add column if not exists work_weekdays integer[] not null default array[1,2,3,4,5],
  add column if not exists programming_generated_at timestamptz null;

alter table public.programming_items
  add column if not exists scheduled_end_date date null,
  add column if not exists schedule_key text null;

create unique index if not exists programming_items_schedule_key_uidx
  on public.programming_items(schedule_key);
create index if not exists proposals_service_schedule_idx
  on public.proposals(status, programming_generated_at);
