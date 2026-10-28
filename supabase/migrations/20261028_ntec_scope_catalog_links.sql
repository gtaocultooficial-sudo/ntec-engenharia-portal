-- Attach the user's lab-scope standards and accreditation statuses to the NTEC proposal price catalogue.
-- Existing prices are preserved. Unpriced scope items are added with "Preço a definir", never with an invented price.
alter table public.proposal_reference_values
  add column if not exists scope_accreditation_status text not null default '';
alter table public.proposal_items
  add column if not exists scope_accreditation_status text not null default '';

-- Soil tests already present in the price table.
update public.proposal_reference_values set normative_references='ABNT NBR 7180:2025',normative_note='Escopo NTEC: limite de plasticidade — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.4';
update public.proposal_reference_values set normative_references='ABNT NBR 6459:2025',normative_note='Escopo NTEC: limite de liquidez — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.5';
update public.proposal_reference_values set normative_references='ABNT NBR 7181:2025',normative_note='Escopo NTEC: análise granulométrica — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.6';
update public.proposal_reference_values set normative_references='ABNT NBR 7182:2025',normative_note='Escopo NTEC: compactação Proctor — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.2';
update public.proposal_reference_values set normative_references='ABNT NBR 16097:2012',normative_note='Escopo NTEC: teor de umidade por método expedito — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.11';
update public.proposal_reference_values set normative_references='ABNT NBR 9895:2025',normative_note='Escopo NTEC: Índice de Suporte Califórnia (ISC) — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code in ('1.3','1.7','1.8');
update public.proposal_reference_values set normative_references='ABNT NBR 7180:2025; ABNT NBR 6459:2025; ABNT NBR 7181:2025; ABNT NBR 7182:2025; ABNT NBR 16097:2012; ABNT NBR 9895:2025; ABNT NBR 7185:2025; ABNT NBR 9813:2026; ABNT NBR 17212:2025; ABNT NBR 6458:2025',normative_note='Serviço auxiliar: mobilização/coleta não é ensaio acreditado por si só.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.1';

-- Concrete, mortar and masonry scope.
update public.proposal_reference_values set normative_references='ABNT NBR 5738:2015',normative_note='Escopo NTEC: procedimento para moldagem e cura — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Ensaios de Concreto' and section_name='ENSAIOS CONCRETO' and item_code='1.3';
update public.proposal_reference_values set normative_references='ABNT NBR 5739:2018',normative_note='Escopo NTEC: compressão de corpos de prova cilíndricos — Acreditado, conforme documento fornecido; confirmar o escopo vigente antes de declarar a acreditação.',scope_accreditation_status='Acreditado'
where category='Ensaios de Concreto' and section_name='ENSAIOS CONCRETO' and item_code='1.7';
update public.proposal_reference_values set normative_references='ABNT NBR 5738:2015; ABNT NBR 5739:2018; ABNT NBR 7680-1:2015; ABNT NBR 16889:2020; ABNT NBR 15823-1:2017; ABNT NBR 15823-2:2017',normative_note='Serviço auxiliar de concreto: mobilização/coleta não é ensaio acreditado por si só.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Ensaios de Concreto' and section_name='ENSAIOS CONCRETO' and item_code in ('1.1','1.2');
update public.proposal_reference_values set normative_references='ABNT NBR 13528-3:2019',normative_note='Escopo NTEC: aderência superficial de revestimento de argamassa — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Ensaios de Argamassa' and section_name='ENSAIOS ARGAMASSA' and item_code='1.8';
update public.proposal_reference_values set normative_references='ABNT NBR 13528-3:2019; ABNT NBR 15258:2021; ABNT NBR 16868-2:2020',normative_note='Serviço auxiliar de argamassa: mobilização/coleta não é ensaio acreditado por si só.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Ensaios de Argamassa' and section_name='ENSAIOS ARGAMASSA' and item_code in ('1.1','1.2');
update public.proposal_reference_values set normative_references='ABNT NBR 12118:2013',normative_note='Serviço auxiliar ligado aos ensaios de blocos; a acreditação aplica-se aos ensaios do escopo, não à mobilização/coleta.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Blocos & Bloquete e Artefatos' and section_name='ENSAIOS  DE BLOCOS EM CONCRETO NÃO ESTRUTURAIS' and item_code in ('1.1','1.2');
update public.proposal_reference_values set normative_references='ABNT NBR 12118:2013',normative_note='Escopo NTEC: ensaios de blocos vazados de concreto simples para alvenaria — Acreditado, conforme documento fornecido; confirmar limites/escopo vigente.',scope_accreditation_status='Acreditado'
where category='Blocos & Bloquete e Artefatos' and section_name='ENSAIOS  DE BLOCOS EM CONCRETO NÃO ESTRUTURAIS' and item_code in ('1.3','1.4','1.5');
update public.proposal_reference_values set normative_references='ABNT NBR 16868-3:2020',normative_note='Escopo NTEC: resistência à compressão de prismas de alvenaria estrutural, item 6 — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Blocos & Bloquete e Artefatos' and section_name='ENSAIO DE RESISTENCIA À COMPRESSÃO DE PRISMA OCO/CHEIO' and item_code='6.3';
update public.proposal_reference_values set normative_references='ABNT NBR 16868-3:2020',normative_note='Serviço auxiliar para ensaio de prismas. O status de acreditação aplica-se ao ensaio específico.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Blocos & Bloquete e Artefatos' and section_name='ENSAIO DE RESISTENCIA À COMPRESSÃO DE PRISMA OCO/CHEIO' and item_code in ('6.1','6.2');
update public.proposal_reference_values set normative_references='ABNT NBR 16868-3:2020',normative_note='Serviço auxiliar para ensaio de prismas. O status de acreditação aplica-se ao ensaio específico.',scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Blocos & Bloquete e Artefatos' and section_name='ENSAIO DE RESISTENCIA À COMPRESSÃO DE PRISMA OCO/CHEIO' and item_code in ('6.1','6.2');

-- Asphalt standards separated by method so different procedures are not conflated.
update public.proposal_reference_values set normative_references='DNER-ME 043:1995',normative_note='Escopo NTEC: Marshall — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Massa Afaltica' and section_name='MISTURA ASFALTICA' and item_code='3.3';
update public.proposal_reference_values set normative_references='ABNT NBR 6576:2007; DNIT 155/2010-ME',normative_note='Escopo NTEC: determinação da penetração — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Massa Afaltica' and section_name='ENSAIOS DE MASSA ASFALTICA EM LABORATORIO' and item_code='1.3';
update public.proposal_reference_values set normative_references='DNER-ME 078:1994; ABNT NBR 12583:2017',normative_note='Escopo NTEC: adesividade de agregado graúdo ao ligante betuminoso — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Massa Afaltica' and section_name='ENSAIOS DE AGREGADOS PARA MASSA ASFALTICA' and item_code='2.2';
update public.proposal_reference_values set normative_references='DNER-ME 053:1994',normative_note='Escopo NTEC: percentagem/índice percentual de betume pelo DNER-ME 053:1994 — Não acreditado, conforme documento fornecido.',scope_accreditation_status='Não acreditado'
where category='Massa Afaltica' and section_name='MISTURA ASFALTICA' and item_code='3.1';
update public.proposal_reference_values set normative_references='',normative_note='Item comercial genérico de densidade; confirmar o método e objeto de medição antes de vincular a uma norma do escopo.',scope_accreditation_status=''
where category='Massa Afaltica' and section_name='ENSAIOS DE MASSA ASFALTICA EM LABORATORIO' and item_code='1.1';

-- New scope tests get explicit unpriced reference rows. Fill prices on the bundle or update the reference later.
with new_refs(item_code,section_name,item_name,category,unit,normative_references,normative_note,scope_accreditation_status) as (
 values
 ('SCOPE-SOLO-7185','ENSAIOS DE SOLO EM CAMPO','Massa específica aparente in situ — frasco de areia','ENSAIOS DE SOLO','Ensaio','ABNT NBR 7185:2025','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-SOLO-9813','ENSAIOS DE SOLO EM CAMPO','Massa específica aparente in situ — cilindro de cravação','ENSAIOS DE SOLO','Ensaio','ABNT NBR 9813:2026','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-SOLO-17212','ENSAIOS DE SOLO EM LABORATORIO','Massa específica dos sólidos da fração passante na peneira de 2,0 mm','ENSAIOS DE SOLO','Ensaio','ABNT NBR 17212:2025','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-SOLO-6458','ENSAIOS DE SOLO EM LABORATORIO','Massa específica dos sólidos/aparente e absorção da fração especificada','ENSAIOS DE SOLO','Ensaio','ABNT NBR 6458:2025','Escopo NTEC: Não acreditado; confirmar fração/material e método.','Não acreditado'),
 ('SCOPE-BLOCO-AREA','ENSAIOS  DE BLOCOS EM CONCRETO NÃO ESTRUTURAIS','Determinação da área líquida de bloco vazado de concreto','Blocos & Bloquete e Artefatos','Ensaio','ABNT NBR 12118:2013','Escopo NTEC: Acreditado, conforme documento fornecido; preço comercial ainda não cadastrado.','Acreditado'),
 ('SCOPE-BLOCO-RETRACAO','ENSAIOS  DE BLOCOS EM CONCRETO NÃO ESTRUTURAIS','Determinação da retração por secagem de bloco vazado de concreto','Blocos & Bloquete e Artefatos','Ensaio','ABNT NBR 12118:2013','Escopo NTEC: Acreditado, conforme documento fornecido; preço comercial ainda não cadastrado.','Acreditado'),
 ('SCOPE-CONC-7680-1','ENSAIOS CONCRETO','Extração e ensaio de testemunhos de estruturas de concreto — resistência à compressão axial','Ensaios de Concreto','Ensaio','ABNT NBR 7680-1:2015','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-CONC-16889','ENSAIOS CONCRETO','Determinação da consistência do concreto pelo abatimento do tronco de cone','Ensaios de Concreto','Ensaio','ABNT NBR 16889:2020','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-CONC-15823-1','CONCRETO AUTOADENSÁVEL','Classificação, controle e recebimento de concreto autoadensável no estado fresco — Parte 1','Ensaios de Concreto','Ensaio','ABNT NBR 15823-1:2017','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-CONC-15823-2','CONCRETO AUTOADENSÁVEL','Determinação do espalhamento, tempo de escoamento e índice de estabilidade visual — Parte 2','Ensaios de Concreto','Ensaio','ABNT NBR 15823-2:2017','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-ARG-15258','ENSAIOS ARGAMASSA','Resistência potencial de aderência à tração de argamassa para revestimento','Ensaios de Argamassa','Ensaio','ABNT NBR 15258:2021','Escopo NTEC: Não acreditado; distinto do ensaio de aderência superficial em parede.','Não acreditado'),
 ('SCOPE-ARG-16868-2','ENSAIOS ARGAMASSA','Moldagem e ensaio de resistência à compressão de argamassa para alvenaria estrutural','Ensaios de Argamassa','Ensaio','ABNT NBR 16868-2:2020','Escopo NTEC: Não acreditado; confirmar geometria e procedimento do Anexo A.','Não acreditado'),
 ('SCOPE-ASF-DNER117','MISTURA ASFALTICA','Determinação da densidade aparente de mistura asfáltica','Massa Afaltica','Ensaio','DNER-ME 117:1994','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-ASF-DNIT136','MISTURA ASFALTICA','Resistência à tração por compressão diametral de mistura asfáltica','Massa Afaltica','Ensaio','DNIT 136/2018-ME','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado'),
 ('SCOPE-ASF-NBR6296','ENSAIOS DE MASSA ASFALTICA EM LABORATORIO','Massa específica e densidade relativa de material asfáltico','Massa Afaltica','Ensaio','ABNT NBR 6296:2012','Escopo NTEC: Não acreditado; confirmar material e objeto de medição.','Não acreditado'),
 ('SCOPE-ASF-DENSIDADE-CP','MISTURA ASFALTICA','Densidade aparente/massa específica aparente de corpos de prova compactados','Massa Afaltica','Ensaio','DNIT 428/2022-ME; ABNT NBR 15573:2012','Escopo NTEC: Não acreditado; confirmar método e objeto de medição.','Não acreditado'),
 ('SCOPE-ASF-NBR16208','MISTURA ASFALTICA','Determinação do teor de betume por Soxhlet, Rotarex ou refluxo duplo','Massa Afaltica','Ensaio','ABNT NBR 16208:2013','Escopo NTEC: Não acreditado; preço comercial ainda não cadastrado.','Não acreditado')
)
insert into public.proposal_reference_values
(item_code,section_name,item_name,category,unit,reference_price,price_label,notes,is_active,source_reference,source_sheet_order,normative_references,normative_note,scope_accreditation_status)
select n.item_code,n.section_name,n.item_name,n.category,n.unit,0,'Preço a definir',
       'Item incluído com base no escopo técnico informado pelo usuário. Preço de referência ainda não cadastrado.',
       true,'Escopo técnico do laboratório informado pelo usuário em 28/10/2026',90,
       n.normative_references,n.normative_note,n.scope_accreditation_status
from new_refs n
where not exists(select 1 from public.proposal_reference_values p where p.category=n.category and p.item_code=n.item_code);

-- Accessory line items are shown in the same normative bundle but clearly marked as non-test services.
update public.proposal_reference_values
set scope_accreditation_status='Serviço auxiliar — não é ensaio',
    normative_note=concat_ws(' ',nullif(normative_note,''),'A acreditação refere-se ao ensaio do escopo, não à mobilização/coleta/deslocamento.')
where item_name ilike '%mobilização%'
   or item_name ilike '%coleta de amostras%'
   or item_name ilike '%deslocamento entre furos%'
   or item_name ilike '%plataforma para execução de furo%';

update public.proposal_reference_values
set normative_references='ABNT NBR 7180:2025; ABNT NBR 6459:2025; ABNT NBR 7181:2025; ABNT NBR 7182:2025; ABNT NBR 16097:2012; ABNT NBR 9895:2025; ABNT NBR 7185:2025; ABNT NBR 9813:2026; ABNT NBR 17212:2025; ABNT NBR 6458:2025',
    normative_note='Serviço auxiliar de solo: mobilização para coleta não é ensaio acreditado por si só.',
    scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='ENSAIOS DE SOLO' and section_name='ENSAIOS DE SOLO EM LABORATORIO' and item_code='1.1';
update public.proposal_reference_values
set normative_references='ABNT NBR 5738:2015; ABNT NBR 5739:2018; ABNT NBR 7680-1:2015; ABNT NBR 16889:2020; ABNT NBR 15823-1:2017; ABNT NBR 15823-2:2017',
    normative_note='Serviço auxiliar de concreto: mobilização/coleta não é ensaio acreditado por si só.',
    scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Ensaios de Concreto' and section_name='ENSAIOS CONCRETO' and item_code in ('1.1','1.2');
update public.proposal_reference_values
set normative_references='ABNT NBR 13528-3:2019; ABNT NBR 15258:2021; ABNT NBR 16868-2:2020',
    normative_note='Serviço auxiliar de argamassa: mobilização/coleta não é ensaio acreditado por si só.',
    scope_accreditation_status='Serviço auxiliar — não é ensaio'
where category='Ensaios de Argamassa' and section_name='ENSAIOS ARGAMASSA' and item_code in ('1.1','1.2');
