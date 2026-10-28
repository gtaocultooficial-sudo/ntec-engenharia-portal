-- Keep generic commercial rows out of per-standard service bundles.
-- These items have no single NBR: their relevance depends on the contracted field method.
update public.proposal_reference_values
set normative_references = 'Vínculo a definir conforme método e escopo contratado; esta rubrica comercial não possui NBR própria.',
    normative_note = 'O vínculo normativo depende do serviço geotécnico principal executado. Exemplos possíveis conforme escopo: ABNT NBR 9603:2023, ABNT NBR 6484:2020, ABNT NBR 16797:2020, ABNT NBR 9820:1997 ou ABNT NBR 10905:1989. Esses exemplos não constituem associação automática do profissional, translado ou hora parada a todas essas normas.'
where category = 'SONDAGENS E GEOLOGIA'
  and section_name = 'Consultoria em Solo e Rocha';
