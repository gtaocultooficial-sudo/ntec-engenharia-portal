-- Annual review history for NTEC reference prices.
-- Safe additive migration: preserves existing reference values and proposal data.
create table if not exists public.proposal_price_reviews (
  id uuid primary key default gen_random_uuid(),
  reference_value_id uuid not null references public.proposal_reference_values(id) on delete cascade,
  reviewed_by uuid references auth.users(id) on delete set null,
  item_name text not null,
  item_code text,
  category text not null,
  unit text not null,
  base_price numeric(14,2) not null check (base_price >= 0),
  recommended_price numeric(14,2) not null check (recommended_price >= 0),
  market_price_min numeric(14,2) not null check (market_price_min >= 0),
  market_price_max numeric(14,2) not null check (market_price_max >= market_price_min),
  annual_adjustment_percent numeric(8,4) not null,
  band_percent numeric(8,4) not null default 10 check (band_percent >= 0 and band_percent <= 50),
  index_name text not null,
  index_period text not null,
  years_elapsed numeric(8,3) not null default 1 check (years_elapsed >= 0),
  assessment text not null check (assessment in ('abaixo','na_faixa','acima','sem_preco_numerico')),
  notes text not null default '',
  applied_to_reference boolean not null default false,
  applied_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists proposal_price_reviews_reference_created_idx
  on public.proposal_price_reviews(reference_value_id, created_at desc);
alter table public.proposal_price_reviews enable row level security;
drop policy if exists ntec_proposal_price_reviews_admin_all on public.proposal_price_reviews;
create policy ntec_proposal_price_reviews_admin_all
  on public.proposal_price_reviews
  for all
  using ((select private.is_ntec_admin()))
  with check ((select private.is_ntec_admin()));
grant select, insert, update, delete on public.proposal_price_reviews to authenticated;
