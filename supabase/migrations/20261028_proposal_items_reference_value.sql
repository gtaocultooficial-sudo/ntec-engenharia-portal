alter table public.proposal_items
  add column if not exists reference_value_id uuid;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'proposal_items_reference_value_id_fkey'
      and conrelid = 'public.proposal_items'::regclass
  ) then
    alter table public.proposal_items
      add constraint proposal_items_reference_value_id_fkey
      foreign key (reference_value_id)
      references public.proposal_reference_values(id)
      on delete set null;
  end if;
end $$;

create index if not exists proposal_items_reference_value_id_idx
  on public.proposal_items(reference_value_id);

comment on column public.proposal_items.reference_value_id is
  'Optional link to the reference-price row used when composing the proposal item.';