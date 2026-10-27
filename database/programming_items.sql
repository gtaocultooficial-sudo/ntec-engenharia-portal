-- NTEC Engenharia: programação de atividades por obra.
-- Aplicar no projeto Supabase NTEC antes de publicar a interface que usa esta tabela.
create table public.programming_items (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id),
  proposal_id uuid null references public.proposals(id) on delete set null,
  report_id uuid null references public.reports(id) on delete set null,
  parent_item_id uuid null references public.programming_items(id) on delete set null,
  item_type text not null default 'outro'
    check (item_type = any (array[
      'visita_tecnica','programacao_obra','moldagem','ruptura','ensaio','emissao_relatorio','outro'
    ])),
  title text not null
    check (length(trim(title)) between 1 and 180),
  description text not null default '',
  scheduled_date date not null,
  scheduled_time time without time zone null,
  duration_minutes integer null
    check (duration_minutes is null or duration_minutes between 1 and 1440),
  sample_series integer null
    check (sample_series is null or sample_series > 0),
  test_age_days integer null
    check (test_age_days is null or test_age_days >= 0),
  quantity numeric(12,3) null
    check (quantity is null or quantity >= 0),
  unit text not null default '',
  status text not null default 'planejado'
    check (status = any (array[
      'planejado','agendado','em_andamento','aguardando_resultado','concluido','cancelado'
    ])),
  notes text not null default '',
  created_by uuid null references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index programming_items_project_date_idx
  on public.programming_items (project_id, scheduled_date);
create index programming_items_proposal_idx
  on public.programming_items (proposal_id);
create index programming_items_report_idx
  on public.programming_items (report_id);
create index programming_items_parent_item_idx
  on public.programming_items (parent_item_id);
create index programming_items_status_date_idx
  on public.programming_items (status, scheduled_date);

alter table public.programming_items enable row level security;

create policy ntec_programming_items_admin_all
  on public.programming_items
  for all
  to authenticated
  using ((select private.is_ntec_admin()))
  with check ((select private.is_ntec_admin()));
