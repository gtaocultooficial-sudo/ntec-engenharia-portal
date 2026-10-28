-- Normative links for proposal reference items and proposal lines.
-- Additive and idempotent: preserves all existing prices and proposal data.
alter table public.proposal_reference_values
  add column if not exists normative_references text not null default '',
  add column if not exists normative_note text not null default '';

alter table public.proposal_items
  add column if not exists normative_references text not null default '',
  add column if not exists normative_note text not null default '';

update public.proposal_reference_values
set normative_references = case
  when section_name = 'SONDAGENS' and item_code = '1.1'
    then 'ABNT NBR 9603:2023'
  when section_name = 'SONDAGENS' and item_code = '1.2'
    then 'ABNT NBR 9603:2023 (procedimento do serviço principal; mobilização não tem NBR própria)'
  when section_name = 'SONDAGENS À PERCUSSÃO' and item_code in ('2.1','2.2','2.3','2.4')
    then 'ABNT NBR 6484:2020'
  when section_name = 'SONDAGENS À PERCUSSÃO COM MEDIDA DE TORK' and item_code in ('3.1','3.2','3.3')
    then 'ABNT NBR 6484:2020; ABNT NBR 16797:2020'
  when section_name = 'SONDAGENS À MISTA / ROTATIVAS' and item_code in ('4.1','4.2','4.3','4.4','4.9','4.10')
    then 'ABNT NBR 6122:2022 (investigação para fundações, quando aplicável); ABNT NBR 6490:2016 (reconhecimento/amostragem de rochas, quando aplicável); DNER-PRO 102/1997 (sondagem rotativa em engenharia rodoviária, quando aplicável; não é NBR ABNT)'
  when section_name = 'SONDAGENS À MISTA / ROTATIVAS' and item_code in ('4.5','4.6','4.7','4.8')
    then 'ABNT NBR 6122:2022 (investigação para fundações, quando aplicável); ABNT NBR 6490:2016 (reconhecimento/amostragem de rochas, quando aplicável); DNER-PRO 102/1997 (sondagem rotativa em engenharia rodoviária, quando aplicável; não é NBR ABNT)'
  when section_name = 'ENSAIOS Shelby' and item_code in ('5.1','5.2','5.3','5.4','5.5','5.6')
    then 'ABNT NBR 9820:1997'
  when section_name = 'VANE TEST' and item_code in ('6.1','6.2','6.3','6.4','6.5','6.6','6.7','6.8')
    then 'ABNT NBR 10905:1989'
  when section_name = 'Consultoria em Solo e Rocha'
    then 'Conforme o serviço geotécnico principal e o escopo contratual; podem ser aplicáveis ABNT NBR 9603:2023, NBR 6484:2020, NBR 16797:2020, NBR 9820:1997 ou NBR 10905:1989. Não há uma NBR única para o item comercial de hora, translado ou consultoria.'
  else normative_references
end,
normative_note = case
  when section_name = 'SONDAGENS' and item_code = '1.1'
    then 'Norma de execução de sondagem a trado. Confirmar o escopo, o tipo de trado, profundidade e condições do terreno na proposta.'
  when section_name = 'SONDAGENS' and item_code = '1.2'
    then 'Mobilização/instalação é item comercial acessório: herda a referência do serviço a trado; não declarar que a NBR regula o preço da mobilização.'
  when section_name = 'SONDAGENS À PERCUSSÃO'
    then 'A NBR 6484 rege a execução da sondagem de simples reconhecimento com SPT. A NBR 8036:1983 trata de programação de sondagens para fundações de edifícios, se fizer parte do escopo de planejamento.'
  when section_name = 'SONDAGENS À PERCUSSÃO COM MEDIDA DE TORK'
    then 'Para SPT com torque, associar NBR 6484:2020 à NBR 16797:2020. Medição de energia SPT, se contratada, tem referência própria NBR 16796:2020. Mobilização e plataforma herdam o método principal.'
  when section_name = 'SONDAGENS À MISTA / ROTATIVAS' and item_code in ('4.1','4.2','4.3','4.4','4.9','4.10')
    then 'Não existe uma NBR ABNT única que cubra universalmente toda sondagem rotativa de qualquer finalidade. Usar DNER-PRO 102/1997 apenas no contexto rodoviário e confirmar método/especificação da obra. A NBR 6122 é referência de fundações quando o estudo é para esse fim.'
  when section_name = 'SONDAGENS À MISTA / ROTATIVAS' and item_code in ('4.5','4.6','4.7','4.8')
    then 'Item comercial acessório: não atribuir uma NBR própria a deslocamento, obturação, caixa de amostras ou fornecimento de água. Vincular ao método principal e à especificação da obra.'
  when section_name = 'ENSAIOS Shelby'
    then 'A NBR 9820:1997 aplica-se à coleta, acondicionamento e transporte de amostras indeformadas de solos de baixa consistência. Mobilização, plataforma e deslocamentos são itens acessórios e herdam o método principal.'
  when section_name = 'VANE TEST'
    then 'A NBR 10905:1989 é referência do ensaio de palheta in situ. Os itens de plataforma, mobilização, instalação, perfuração, obturação, caixas e relatório devem ser vinculados ao método e ao escopo efetivamente contratados.'
  when section_name = 'Consultoria em Solo e Rocha'
    then 'O vínculo depende do serviço de campo ou produto técnico contratado. O item comercial de hora, translado ou consultoria não recebe uma NBR genérica sem relação com o método executado.'
  else normative_note
end
where category = 'SONDAGENS E GEOLOGIA';

update public.proposal_items pi
set normative_references = prv.normative_references,
    normative_note = prv.normative_note
from public.proposal_reference_values prv
where pi.reference_value_id = prv.id
  and (coalesce(pi.normative_references,'') = '' or coalesce(pi.normative_note,'') = '');

create index if not exists proposal_reference_values_normative_refs_idx
  on public.proposal_reference_values (category, section_name, item_code);
