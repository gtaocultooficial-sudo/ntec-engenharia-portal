-- Official NTEC lab scope matrix transcribed from the scope images provided on 2026-10-28.
-- Accreditation status is stored as provided by the user and must be reconfirmed against the current accreditation certificate/scope before external claims.
create table if not exists public.ntec_lab_scope (
  id uuid primary key default gen_random_uuid(),
  activity_area text not null,
  test_description text not null,
  standard_procedure text not null,
  accreditation_status text not null check (accreditation_status in ('Acreditado','Não acreditado')),
  scope_notes text not null default '',
  sort_order integer not null default 100,
  source_label text not null default 'Escopo informado pelo usuário em 28/10/2026',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(activity_area,test_description,standard_procedure)
);
alter table public.ntec_lab_scope enable row level security;
drop policy if exists ntec_lab_scope_admin_all on public.ntec_lab_scope;
create policy ntec_lab_scope_admin_all on public.ntec_lab_scope
  for all using ((select private.is_ntec_admin()))
  with check ((select private.is_ntec_admin()));
grant select,insert,update,delete on public.ntec_lab_scope to authenticated;

insert into public.ntec_lab_scope
(activity_area,test_description,standard_procedure,accreditation_status,scope_notes,sort_order)
values
('Construção Civil / Solo','Execução de Ensaio de Limite de Plasticidade (LP)','ABNT NBR 7180:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',10),
('Construção Civil / Solo','Execução de Ensaio de Limite de Liquidez (LL)','ABNT NBR 6459:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',20),
('Construção Civil / Solo','Determinação da massa específica aparente in situ com emprego de frasco de areia','ABNT NBR 7185:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',30),
('Construção Civil / Solo','Execução de Ensaio de Análise Granulométrica — Preparação e Peneiramento','ABNT NBR 7181:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',40),
('Construção Civil / Solo','Ensaio de compactação — Proctor','ABNT NBR 7182:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',50),
('Construção Civil / Solo','Determinação do teor de umidade — métodos expeditos de ensaio','ABNT NBR 16097:2012','Não acreditado','Escopo transcrito das imagens fornecidas.',60),
('Construção Civil / Solo','Determinação da massa específica aparente in situ com emprego de cilindro de cravação','ABNT NBR 9813:2026','Não acreditado','Escopo transcrito das imagens fornecidas.',70),
('Construção Civil / Solo','Ensaio do Índice de Suporte Califórnia (ISC)','ABNT NBR 9895:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',80),
('Construção Civil / Solo','Determinação da massa específica dos sólidos da fração passante na peneira de abertura 2,0 mm','ABNT NBR 17212:2025','Não acreditado','Escopo transcrito das imagens fornecidas.',90),
('Construção Civil / Solo','Determinação da massa específica dos sólidos, massa específica aparente e absorção de água da fração especificada','ABNT NBR 6458:2025','Não acreditado','Confirmar a fração/material e o título exato na versão controlada do escopo.',100),
('Construção Civil / Blocos Vazados de Concreto Simples para Alvenaria','Determinação das dimensões, absorção de água, área líquida, resistência à compressão e retração por secagem','ABNT NBR 12118:2013 — itens 4, 5, 6 e 7','Acreditado','Conforme status indicado nas imagens; reconfirmar a versão vigente do escopo acreditado.',110),
('Construção Civil / Concreto Convencional','Procedimento para moldagem e cura de corpos de prova','ABNT NBR 5738:2015 — versão corrigida 2016','Não acreditado','Escopo transcrito das imagens fornecidas.',120),
('Construção Civil / Concreto Convencional','Ensaios de compressão de corpos de prova cilíndricos','ABNT NBR 5739:2018','Acreditado','Conforme status indicado nas imagens; reconfirmar a versão vigente do escopo acreditado.',130),
('Construção Civil / Concreto Convencional','Extração, preparo, ensaio e análise de testemunhos de estruturas de concreto — Parte 1: resistência à compressão axial','ABNT NBR 7680-1:2015','Não acreditado','Escopo transcrito das imagens fornecidas.',140),
('Construção Civil / Concreto Convencional','Determinação da consistência pelo abatimento do tronco de cone','ABNT NBR 16889:2020','Não acreditado','Escopo transcrito das imagens fornecidas.',150),
('Construção Civil / Concreto Autoadensável','Classificação, controle e recebimento no estado fresco — Parte 1','ABNT NBR 15823-1:2017','Não acreditado','Escopo transcrito das imagens fornecidas.',160),
('Construção Civil / Concreto Autoadensável','Determinação do espalhamento, tempo de escoamento e índice de estabilidade visual — cone de Abrams, Parte 2','ABNT NBR 15823-2:2017','Não acreditado','Escopo transcrito das imagens fornecidas.',170),
('Construção Civil / Argamassa','Revestimento de paredes de argamassas inorgânicas — determinação da resistência de aderência à tração — Parte 3: aderência superficial','ABNT NBR 13528-3:2019','Não acreditado','Escopo transcrito das imagens fornecidas.',180),
('Construção Civil / Argamassa','Argamassa para revestimento de paredes e tetos — determinação da resistência potencial de aderência à tração','ABNT NBR 15258:2021','Não acreditado','Escopo transcrito das imagens fornecidas.',190),
('Construção Civil / Argamassa','Alvenaria estrutural — Parte 2: ensaio para determinação da resistência à compressão da argamassa (moldagem e compressão)','ABNT NBR 16868-2:2020 — Anexo A','Não acreditado','Confirmar geometria e preparação previstas no Anexo A.',200),
('Construção Civil / Asfalto','Ensaio Marshall','DNER-ME 043:1995','Não acreditado','Escopo transcrito das imagens fornecidas.',210),
('Construção Civil / Asfalto','Determinação da densidade aparente de mistura asfáltica','DNER-ME 117:1994','Não acreditado','Escopo transcrito das imagens fornecidas.',220),
('Construção Civil / Asfalto','Determinação da resistência à tração por compressão diametral de mistura asfáltica','DNIT 136/2018-ME — item 5','Não acreditado','Escopo transcrito das imagens fornecidas.',230),
('Construção Civil / Asfalto','Agregado graúdo — determinação da adesividade ao ligante betuminoso','DNER-ME 078:1994; ABNT NBR 12583:2017','Não acreditado','Escopo transcrito das imagens fornecidas.',240),
('Construção Civil / Asfalto','Determinação da densidade relativa aparente e massa específica aparente de corpos de prova compactados','DNIT 428/2022-ME','Não acreditado','Escopo transcrito das imagens fornecidas.',250),
('Construção Civil / Asfalto','Determinação da massa específica e densidade relativa de material asfáltico','ABNT NBR 6296:2012','Não acreditado','Confirmar material e objeto de medição no método controlado.',260),
('Construção Civil / Asfalto','Determinação da penetração','ABNT NBR 6576:2007; DNIT 155/2010-ME','Não acreditado','Escopo transcrito das imagens fornecidas.',270),
('Construção Civil / Asfalto','Determinação da densidade aparente e massa específica aparente de corpos de prova compactados','ABNT NBR 15573:2012','Não acreditado','Escopo transcrito das imagens fornecidas.',280),
('Construção Civil / Asfalto','Percentagem de betume — determinação do índice percentual de betume','DNER-ME 053:1994','Não acreditado','Escopo transcrito das imagens fornecidas.',290),
('Construção Civil / Asfalto','Misturas asfálticas — teor de betume por Soxhlet, Rotarex e refluxo duplo','ABNT NBR 16208:2013','Não acreditado','Escopo transcrito das imagens fornecidas.',300),
('Construção Civil / Alvenaria Estrutural (Prisma)','Alvenaria estrutural — Parte 3: métodos de ensaio — resistência à compressão de prismas, item 6','ABNT NBR 16868-3:2020 — item 6','Não acreditado','Escopo transcrito das imagens fornecidas.',310)
on conflict(activity_area,test_description,standard_procedure)
do update set accreditation_status=excluded.accreditation_status,scope_notes=excluded.scope_notes,sort_order=excluded.sort_order,updated_at=now();

create index if not exists ntec_lab_scope_area_standard_idx
  on public.ntec_lab_scope(activity_area,standard_procedure);
