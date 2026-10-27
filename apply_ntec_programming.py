#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/admin/index.html")
s = path.read_text(encoding="utf-8")

def once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: esperado 1 trecho, encontrados {count}")
    s = s.replace(old, new, 1)

# Extend the authenticated Supabase API. The table is protected by RLS and these
# write methods also require the NTEC administrator role.
api_methods = r"""async loadProgrammingData(){
 if(!currentSession)throw new Error('Faça login para acessar a programação.');
 if(currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário para a programação.');
 const [itemsResult,projectsResult,proposalsResult,reportsResult]=await Promise.all([
  supabase.from('programming_items').select('id,project_id,proposal_id,report_id,parent_item_id,item_type,title,description,scheduled_date,scheduled_end_date,scheduled_time,duration_minutes,sample_series,test_age_days,quantity,unit,status,notes,created_at,updated_at,projects(name,work_number,client_id,clients(company_name)),proposals(proposal_number,status,description,service_mode,staff_count),reports(report_number,title,report_type,status)').order('scheduled_date',{ascending:true}).order('scheduled_time',{ascending:true}),
  supabase.from('projects').select('id,name,client_id,work_number,status,created_at,clients(company_name)').order('created_at',{ascending:false}),
  supabase.from('proposals').select('id,proposal_number,client_id,project_id,description,amount,status,valid_until,service_mode,staff_count,service_start_date,service_end_date,work_weekdays,programming_generated_at,created_at,clients(company_name)').order('created_at',{ascending:false}),
  supabase.from('reports').select('id,project_id,report_number,title,report_type,report_date,status').order('report_date',{ascending:false})
 ]);
 for(const result of [itemsResult,projectsResult,proposalsResult,reportsResult])if(result.error)throw result.error;
 return {items:itemsResult.data||[],projects:projectsResult.data||[],proposals:proposalsResult.data||[],reports:reportsResult.data||[]};
},
async approveProposalAndSchedule(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!payload?.proposal_id)throw new Error('Selecione uma proposta.');
 if(!['mensal','diaria','pontual'].includes(payload.service_mode))throw new Error('Confirme se o atendimento é mensal, por diária ou pontual.');
 if(!payload.project_id||!payload.service_start_date||!payload.service_end_date)throw new Error('Selecione a obra e o período de início e fim.');
 if(payload.service_end_date<payload.service_start_date)throw new Error('A data final não pode ser anterior à data inicial.');
 const {data:proposal,error:readError}=await supabase.from('proposals').select('id,proposal_number,client_id,project_id,description,status,programming_generated_at').eq('id',payload.proposal_id).single();
 if(readError)throw readError;
 if(proposal.programming_generated_at)throw new Error('Esta proposta já gerou programação. Atualize a lista para conferir as atividades existentes.');
 const start=new Date(payload.service_start_date+'T12:00:00'),end=new Date(payload.service_end_date+'T12:00:00');
 const staff=Math.max(1,Math.min(100,Math.floor(Number(payload.staff_count||1))));
 const weekdays=(Array.isArray(payload.work_weekdays)?payload.work_weekdays:[]).map(Number).filter(n=>n>=1&&n<=7);
 if(payload.service_mode==='diaria'&&!weekdays.length)throw new Error('Selecione pelo menos um dia da semana para as diárias.');
 const baseTitle=payload.service_mode==='mensal'?'Funcionário mensal':payload.service_mode==='diaria'?'Funcionário por diária':'Atendimento pontual';
 const description=String(proposal.description||'').trim();
 const rows=[];
 const makeRow=(date,endDate,key,title,quantity,unit,notes)=>({
  project_id:payload.project_id,proposal_id:proposal.id,item_type:'programacao_obra',title,description,
  scheduled_date:date,scheduled_end_date:endDate,scheduled_time:null,duration_minutes:null,sample_series:null,test_age_days:null,
  quantity,unit,status:'agendado',notes,schedule_key:key,created_by:currentSession.user.id,updated_at:new Date().toISOString()
 });
 if(payload.service_mode==='mensal'){
  let cursor=new Date(start.getFullYear(),start.getMonth(),1,12);
  while(cursor<=end){
   const monthStart=new Date(cursor.getFullYear(),cursor.getMonth(),1,12);
   const monthEnd=new Date(cursor.getFullYear(),cursor.getMonth()+1,0,12);
   const a=monthStart<start?start:monthStart,b=monthEnd>end?end:monthEnd;
   const iso=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
   const key=proposal.id+':mensal:'+iso(a)+':'+iso(b);
   rows.push(makeRow(iso(a),iso(b),key,baseTitle+' — '+(proposal.proposal_number||'Proposta'),staff,'funcionário/mês','Período de atendimento mensal gerado a partir da proposta '+(proposal.proposal_number||proposal.id)+'. Revise escala e horários antes de iniciar. Escopo: '+description));
   cursor=new Date(cursor.getFullYear(),cursor.getMonth()+1,1,12);
  }
 }else{
  const iso=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  if(payload.service_mode==='pontual'){
   const date=iso(start),endDate=iso(end),key=proposal.id+':pontual:'+date+':'+endDate;
   rows.push(makeRow(date,endDate,key,baseTitle+' — '+(proposal.proposal_number||'Proposta'),staff,'atendimento','Atividade pontual criada a partir da proposta '+(proposal.proposal_number||proposal.id)+'. Confirme data e escopo antes da execução. Escopo: '+description));
  }else{
   for(let d=new Date(start);d<=end;d.setDate(d.getDate()+1)){
    if(!weekdays.includes(d.getDay()===0?7:d.getDay()))continue;
    const date=iso(d),key=proposal.id+':diaria:'+date;
    rows.push(makeRow(date,date,key,baseTitle+' — '+(proposal.proposal_number||'Proposta'),staff,'funcionário/diária','Atividade diária criada a partir da proposta '+(proposal.proposal_number||proposal.id)+'. É uma programação prevista, não um registro de serviço executado. Escopo: '+description));
   }
  }
 }
 if(!rows.length)throw new Error('Nenhuma atividade foi gerada. Revise período e dias selecionados.');
 const {error:rowsError}=await supabase.from('programming_items').upsert(rows,{onConflict:'schedule_key',ignoreDuplicates:true});
 if(rowsError)throw rowsError;
 const {data:updated,error:updateError}=await supabase.from('proposals').update({
  project_id:payload.project_id,status:'aprovada',service_mode:payload.service_mode,staff_count:staff,
  service_start_date:payload.service_start_date,service_end_date:payload.service_end_date,
  work_weekdays:weekdays,programming_generated_at:new Date().toISOString()
 }).eq('id',proposal.id).select('id,proposal_number,status,programming_generated_at').single();
 if(updateError)throw updateError;
 return {proposal:updated,scheduledCount:rows.length,mode:payload.service_mode};
},
async saveProgrammingItem(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!payload?.project_id||!payload?.scheduled_date||!String(payload?.title||'').trim())throw new Error('Informe a obra, o título e a data programada.');
 const row={project_id:payload.project_id,proposal_id:payload.proposal_id||null,report_id:payload.report_id||null,parent_item_id:payload.parent_item_id||null,schedule_key:payload.schedule_key||null,item_type:payload.item_type||'outro',title:String(payload.title).trim(),description:String(payload.description||''),scheduled_date:payload.scheduled_date,scheduled_end_date:payload.scheduled_end_date||null,scheduled_time:payload.scheduled_time||null,duration_minutes:payload.duration_minutes==null||payload.duration_minutes===''?null:Number(payload.duration_minutes),sample_series:payload.sample_series==null||payload.sample_series===''?null:Number(payload.sample_series),test_age_days:payload.test_age_days==null||payload.test_age_days===''?null:Number(payload.test_age_days),quantity:payload.quantity==null||payload.quantity===''?null:Number(payload.quantity),unit:String(payload.unit||''),status:payload.status||'planejado',notes:String(payload.notes||''),updated_at:new Date().toISOString()};
 let result;
 if(payload.id)result=await supabase.from('programming_items').update(row).eq('id',payload.id).select('id').single();
 else result=await supabase.from('programming_items').insert({...row,created_by:currentSession.user.id}).select('id').single();
 if(result.error)throw result.error;
 return result.data;
},
async deleteProgrammingItem(id){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 const {error}=await supabase.from('programming_items').delete().eq('id',id);
 if(error)throw error;
 return true;
},
async syncProgrammingRuptures(reportId,measuredByAge,reportComplete=false){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 const {data:items,error}=await supabase.from('programming_items').select('id,test_age_days,quantity,status').eq('report_id',reportId).eq('item_type','ruptura').neq('status','cancelado');
 if(error)throw error;
 for(const item of items||[]){
  const age=Number(item.test_age_days),measured=Math.max(0,Number(measuredByAge?.[age]||0)),required=Math.max(0,Number(item.quantity||0));
  const complete=measured>0&&(required>0?measured>=required:Boolean(reportComplete));
  const status=complete?'concluido':measured>0?'em_andamento':'agendado';
  const {error:updateError}=await supabase.from('programming_items').update({status,updated_at:new Date().toISOString()}).eq('id',item.id);
  if(updateError)throw updateError;
 }
 return true;
},
async loadProposalIntake(){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Faça login como administrador para analisar solicitações.');
 const [requestsResult,projectsResult,proposalsResult]=await Promise.all([
  supabase.from('proposal_requests').select('id,full_name,company_name,email,phone,service,project_location,details,consent_to_contact,status,created_at').order('created_at',{ascending:false}),
  supabase.from('projects').select('id,name,client_id,work_number,status,clients(company_name)').order('created_at',{ascending:false}),
  supabase.from('proposals').select('id,proposal_number,source_request_id,status,amount,valid_until,description,created_at,client_id,project_id,service_mode,staff_count,clients(company_name,contact_name,email,phone),projects(name,address,work_number,clients(company_name))').order('created_at',{ascending:false})
 ]);
 for(const result of [requestsResult,projectsResult,proposalsResult])if(result.error)throw result.error;
 const linked=proposalsResult.data||[];
 return {requests:(requestsResult.data||[]).map(r=>({...r,linked_proposal:linked.find(p=>p.source_request_id===r.id)||null})),projects:projectsResult.data||[],proposals:linked};
},
async updateProposalRequestStatus(id,status){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!['recebida','em_atendimento','proposta_criada','encerrada'].includes(status))throw new Error('Status de solicitação inválido.');
 const {data,error}=await supabase.from('proposal_requests').update({status}).eq('id',id).select('id,status').single();
 if(error)throw error;
 return data;
},
async createDraftProposalFromRequest(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!payload?.request_id)throw new Error('Selecione uma solicitação original.');
 if(!String(payload.service||'').trim())throw new Error('Informe o serviço da proposta.');
 if(!String(payload.description||'').trim())throw new Error('Revise e preencha o escopo proposto.');
 const amount=Number(payload.amount);
 if(!Number.isFinite(amount)||amount<=0)throw new Error('Informe um valor maior que zero para a proposta.');
 if(payload.service_mode&&!['mensal','diaria','pontual','revisar'].includes(payload.service_mode))throw new Error('Modelo de cobrança inválido.');
 const {data:request,error:requestError}=await supabase.from('proposal_requests').select('id,full_name,company_name,email,phone,service,project_location,details,status').eq('id',payload.request_id).single();
 if(requestError)throw requestError;
 const {data:prior,error:priorError}=await supabase.from('proposals').select('id,proposal_number,status').eq('source_request_id',request.id).limit(1);
 if(priorError)throw priorError;
 if(prior?.length)throw new Error('Esta solicitação já tem uma proposta vinculada: '+prior[0].proposal_number+'. Atualize a lista para conferi-la.');
 let client=null;
 if(String(request.email||'').trim()){
  const found=await supabase.from('clients').select('id,company_name,contact_name,email,phone').eq('email',String(request.email).trim()).limit(1);
  if(found.error)throw found.error;
  client=found.data?.[0]||null;
 }
 const company=String(request.company_name||request.full_name||'Cliente da solicitação').trim();
 if(!client){
  const found=await supabase.from('clients').select('id,company_name,contact_name,email,phone').eq('company_name',company).limit(1);
  if(found.error)throw found.error;
  client=found.data?.[0]||null;
 }
 if(!client){
  const created=await supabase.from('clients').insert({company_name:company,contact_name:String(request.full_name||''),email:String(request.email||''),phone:String(request.phone||'')}).select('id,company_name,contact_name,email,phone').single();
  if(created.error)throw created.error;
  client=created.data;
 }
 const proposalNumber='PROP-'+new Date().toISOString().slice(0,10).replaceAll('-','')+'-'+Math.random().toString(36).slice(2,6).toUpperCase();
 const staffMode=['mensal','diaria'].includes(payload.service_mode);
 const proposalPayload={client_id:client.id,project_id:payload.project_id||null,proposal_number:proposalNumber,description:String(payload.description).trim(),amount,valid_until:payload.valid_until||null,status:'rascunho',source_request_id:request.id,service_mode:payload.service_mode||'revisar',staff_count:staffMode?Math.max(1,Math.min(100,Math.floor(Number(payload.staff_count||1)))):null};
 proposalPayload.description=String(payload.service).trim()+'\\n\\n'+String(payload.description).trim();
 const createdProposal=await supabase.from('proposals').insert(proposalPayload).select('id,proposal_number,status,amount,source_request_id,client_id,project_id,description,valid_until,service_mode,staff_count,created_at').single();
 if(createdProposal.error)throw createdProposal.error;
 const statusUpdate=await supabase.from('proposal_requests').update({status:'proposta_criada'}).eq('id',request.id);
 return {proposal:createdProposal.data,requestStatusUpdated:!statusUpdate.error,warning:statusUpdate.error?.message||null};
},
getProgrammingAccess(){return Boolean(currentSession&&currentProfile?.role==='admin');},
"""
once("async saveReport(r){", api_methods + "async saveReport(r){", "API do módulo de programação")

nav_anchor = '<button data-page="propostas">▤ <span>Propostas</span></button><button data-page="medicoes">▧ <span>Medições</span></button>'
nav_new = '<button data-page="propostas">▤ <span>Propostas</span></button><button data-page="programacao">▦ <span>Programação</span></button><button data-page="medicoes">▧ <span>Medições</span></button>'
once(nav_anchor, nav_new, "navegação da programação")

section = r'''<section class="page hidden" id="page-programacao">
 <div class="titleline"><div><h1>Programação de atividades</h1><p>Organize visitas, moldagens, rupturas, ensaios e entregas por obra, usando propostas aprovadas como referência.</p></div><button class="btn primary" id="ntec-pg-new" type="button">+ Nova atividade</button></div>
 <div class="panel" id="ntec-pg-proposal-queue">
  <h2>Propostas aguardando fechamento e programação</h2>
  <p class="sub">Ao analisar uma proposta, o sistema procura indícios de atendimento mensal ou por diária no texto do escopo. Confirme a classificação, o período, a quantidade de funcionários e os dias de trabalho antes de aprovar.</p>
  <div class="tablewrap"><table class="ntec-pg-table"><thead><tr><th>Proposta / cliente</th><th>Escopo</th><th>Leitura inicial</th><th>Status</th><th>Ação</th></tr></thead><tbody id="ntec-pg-proposal-queue-body"><tr><td colspan="5" class="empty">Carregando propostas…</td></tr></tbody></table></div>
 </div>
 <div class="panel hidden" id="ntec-pg-proposal-review">
  <h2>Analisar proposta e montar programação</h2>
  <input id="ntec-pg-review-proposal-id" type="hidden"/>
  <div class="ntec-pg-proposal-summary" id="ntec-pg-review-summary"></div>
  <div class="formgrid">
   <div class="field"><label for="ntec-pg-review-project">Obra para programar *</label><select id="ntec-pg-review-project" required><option value="">Selecione a obra</option></select></div>
   <div class="field"><label for="ntec-pg-review-mode">Modelo de atendimento identificado *</label><select id="ntec-pg-review-mode"><option value="revisar">Não identificado — revisar</option><option value="mensal">Funcionário mensal</option><option value="diaria">Funcionário por diária</option><option value="pontual">Serviço pontual</option></select><small class="muted small">A classificação é uma sugestão baseada no texto, não uma decisão automática definitiva.</small></div>
   <div class="field"><label for="ntec-pg-review-staff">Quantidade de funcionários *</label><input id="ntec-pg-review-staff" type="number" min="1" max="100" step="1" value="1" required/></div>
   <div class="field"><label for="ntec-pg-review-start">Início do atendimento *</label><input id="ntec-pg-review-start" type="date" required/></div>
   <div class="field"><label for="ntec-pg-review-end">Fim do atendimento *</label><input id="ntec-pg-review-end" type="date" required/></div>
  </div>
  <div class="field" id="ntec-pg-review-weekdays">
   <label>Dias da semana para as diárias *</label>
   <div class="ntec-pg-weekdays">
    <label><input type="checkbox" value="1" data-pg-weekday checked/> Seg</label><label><input type="checkbox" value="2" data-pg-weekday checked/> Ter</label><label><input type="checkbox" value="3" data-pg-weekday checked/> Qua</label><label><input type="checkbox" value="4" data-pg-weekday checked/> Qui</label><label><input type="checkbox" value="5" data-pg-weekday checked/> Sex</label><label><input type="checkbox" value="6" data-pg-weekday/> Sáb</label><label><input type="checkbox" value="7" data-pg-weekday/> Dom</label>
   </div>
   <small class="muted small">De segunda a sexta vêm marcados como sugestão; ajuste conforme a proposta.</small>
  </div>
  <div class="ntec-pg-schedule-preview" id="ntec-pg-review-preview">Preencha o modelo e o período para conferir como a programação será criada.</div>
  <div class="ntec-pg-actions"><button class="btn primary" id="ntec-pg-review-approve" type="button">Aprovar proposta e gerar programação</button><button class="btn" id="ntec-pg-review-cancel" type="button">Cancelar</button><span id="ntec-pg-review-message" role="status" aria-live="polite"></span></div>
 </div>
 <div class="cards ntec-pg-metrics">
  <div class="metric"><div class="metric-top"><span>Planejadas / agendadas</span><span class="metric-icon">▦</span></div><strong id="ntec-pg-count-planned">0</strong><small>Atividades futuras ou organizadas</small></div>
  <div class="metric"><div class="metric-top"><span>Em andamento</span><span class="metric-icon">◷</span></div><strong id="ntec-pg-count-active">0</strong><small>Em execução ou aguardando resultado</small></div>
  <div class="metric"><div class="metric-top"><span>Concluídas</span><span class="metric-icon">✓</span></div><strong id="ntec-pg-count-done">0</strong><small>Atividades marcadas como concluídas</small></div>
 </div>
 <div class="panel hidden" id="ntec-pg-form">
  <h2 id="ntec-pg-form-title">Nova atividade</h2>
  <input type="hidden" id="ntec-pg-id"/><input type="hidden" id="ntec-pg-parent"/>
  <div class="formgrid">
   <div class="field"><label for="ntec-pg-project">Obra *</label><select id="ntec-pg-project" required><option value="">Carregando obras…</option></select></div>
   <div class="field"><label for="ntec-pg-proposal">Proposta aprovada vinculada</label><select id="ntec-pg-proposal"><option value="">Sem proposta vinculada</option></select><small class="muted small">Só aparecem propostas aprovadas do cliente/obra selecionada.</small></div>
   <div class="field"><label for="ntec-pg-type">Tipo de atividade *</label><select id="ntec-pg-type"><option value="visita_tecnica">Visita técnica</option><option value="programacao_obra">Atividade de obra</option><option value="moldagem">Moldagem</option><option value="ruptura">Ruptura de corpo de prova</option><option value="ensaio">Ensaio</option><option value="emissao_relatorio">Emissão de relatório</option><option value="outro">Outro</option></select></div>
   <div class="field"><label for="ntec-pg-title">Título da atividade *</label><input id="ntec-pg-title" maxlength="180" placeholder="Ex.: Moldagem de concreto — bloco A" required/></div>
   <div class="field"><label for="ntec-pg-date">Data programada *</label><input id="ntec-pg-date" type="date" required/></div>
   <div class="field"><label for="ntec-pg-time">Horário</label><input id="ntec-pg-time" type="time"/></div>
   <div class="field"><label for="ntec-pg-duration">Duração prevista (minutos)</label><input id="ntec-pg-duration" type="number" min="1" max="1440" step="1" placeholder="Ex.: 120"/></div>
   <div class="field"><label for="ntec-pg-status">Status</label><select id="ntec-pg-status"><option value="planejado">Planejado</option><option value="agendado">Agendado</option><option value="em_andamento">Em andamento</option><option value="aguardando_resultado">Aguardando resultado</option><option value="concluido">Concluído</option><option value="cancelado">Cancelado</option></select></div>
   <div class="field"><label for="ntec-pg-series">Série de controle (opcional)</label><input id="ntec-pg-series" type="number" min="1" step="1" placeholder="Número da série"/></div>
   <div class="field"><label for="ntec-pg-age">Idade do ensaio (dias)</label><input id="ntec-pg-age" type="number" min="0" step="1" placeholder="Ex.: 7 ou 28"/></div>
   <div class="field"><label for="ntec-pg-quantity">Quantidade prevista</label><input id="ntec-pg-quantity" type="number" min="0" step="0.001" placeholder="Opcional"/></div>
   <div class="field"><label for="ntec-pg-unit">Unidade</label><input id="ntec-pg-unit" maxlength="30" placeholder="m³, un., amostras…"/></div>
   <div class="field"><label for="ntec-pg-report">Relatório relacionado (opcional)</label><select id="ntec-pg-report"><option value="">Vincular depois</option></select></div>
  </div>
  <div class="ntec-pg-molding-options hidden" id="ntec-pg-molding-options">
   <label class="ntec-pg-auto-label"><input id="ntec-pg-auto-ruptures" type="checkbox" checked/> Programar rupturas automaticamente aos 7 e 28 dias</label>
   <div class="field"><label for="ntec-pg-cp-per-age">Quantidade de CPs por idade</label><input id="ntec-pg-cp-per-age" type="number" min="1" max="100" step="1" value="2"/><small class="muted small">Será criada uma atividade de ruptura para cada idade. Isso agenda os ensaios; não lança resultados.</small></div>
  </div>
  <div class="field"><label for="ntec-pg-description">Descrição / escopo</label><textarea id="ntec-pg-description" rows="2" placeholder="Serviço previsto, elemento, local ou instrução de campo."></textarea></div>
  <div class="field"><label for="ntec-pg-notes">Observações internas</label><textarea id="ntec-pg-notes" rows="2" placeholder="Pendências e informações para a equipe."></textarea></div>
  <div class="ntec-pg-actions"><button class="btn primary" id="ntec-pg-save" type="button">Salvar atividade</button><button class="btn" id="ntec-pg-cancel" type="button">Cancelar</button><span id="ntec-pg-message" role="status" aria-live="polite"></span></div>
 </div>
 <div class="toolbar ntec-pg-toolbar"><input id="ntec-pg-search" class="btn" placeholder="Buscar obra, atividade ou proposta…"/><select id="ntec-pg-filter" aria-label="Filtrar por status"><option value="">Todos os status</option><option value="planejado">Planejado</option><option value="agendado">Agendado</option><option value="em_andamento">Em andamento</option><option value="aguardando_resultado">Aguardando resultado</option><option value="concluido">Concluído</option><option value="cancelado">Cancelado</option></select><button class="btn" id="ntec-pg-refresh" type="button">Atualizar</button></div>
 <div class="tablewrap"><table class="ntec-pg-table"><thead><tr><th>Data / período</th><th>Atividade / obra</th><th>Proposta / relatório</th><th>Série / idade</th><th>Status</th><th>Ações</th></tr></thead><tbody id="ntec-pg-body"><tr><td colspan="6" class="empty">Abra Programação para carregar as atividades.</td></tr></tbody></table></div>
 <p class="footnote">A programação registra previsões. A data prevista de ruptura não comprova que o ensaio foi executado; leituras de prensa e resultados reais continuam sendo lançados no módulo de ensaios.</p>
</section>
'''
import re
_medicoes = re.findall(r'<section\b(?=[^>]*\bid=["\']page-medicoes["\'])[^>]*>', s)
if len(_medicoes) != 1:
    raise SystemExit("seção da programação: esperado 1 início de seção page-medicoes, encontrados " + str(len(_medicoes)))
s = s.replace(_medicoes[0], section + "\n" + _medicoes[0], 1)

css = r'''
.ntec-pg-proposal-summary,.ntec-pg-schedule-preview{padding:12px;background:#f4f7fa;border:1px solid var(--line);border-radius:9px;margin:10px 0 14px;line-height:1.5;font-size:13px}.ntec-pg-weekdays{display:flex;gap:12px;flex-wrap:wrap;padding:8px 0}.ntec-pg-weekdays label{display:flex;align-items:center;gap:5px}.ntec-pg-weekdays input{width:auto}.ntec-pg-molding-options{margin:10px 0;padding:12px;background:#f4f7fa;border:1px solid var(--line);border-radius:9px}.ntec-pg-auto-label{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}.ntec-pg-auto-label input{width:auto}.ntec-pg-molding-options .field{margin:10px 0 0;max-width:260px}.ntec-pg-metrics{margin:12px 0 18px}.ntec-pg-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.ntec-pg-toolbar input{flex:1;min-width:200px}.ntec-pg-toolbar select{min-height:40px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px 10px;color:var(--ink)}.ntec-pg-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:12px}.ntec-pg-actions [role=status]{font-size:12px;color:var(--muted)}.ntec-pg-table td{vertical-align:top}.ntec-pg-sub{display:block;color:var(--muted);font-size:12px;margin-top:4px}.ntec-pg-tag{display:inline-block;border-radius:999px;background:#edf2f7;color:#334155;padding:4px 8px;font-size:11px;font-weight:700;white-space:nowrap}.ntec-pg-tag.overdue{background:#fff1f0;color:#9b1c1c}.ntec-pg-tag.done{background:#e9f7ef;color:#166534}.ntec-pg-buttons{display:flex;gap:5px;flex-wrap:wrap}.ntec-pg-buttons .btn{padding:6px 8px;font-size:11px}.ntec-pg-empty{padding:22px;text-align:center;color:var(--muted)}@media(max-width:700px){.ntec-pg-toolbar>*{width:100%;min-width:0}.ntec-pg-actions #ntec-pg-message{width:100%}}
'''
if '</style>' not in s:
    raise SystemExit("estilos da programação: tag style não encontrada")
s = s.replace('</style>', css + '</style>', 1)

request_intake_runtime = "<script>\n(function(){\n const api=()=>window.NTEC_SUPABASE;\n const norm=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');\n const esc=v=>String(v??'').replace(/[&<>\"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[ch]));\n const ptDate=v=>{if(!v)return '—';const m=String(v).match(/^(\\d{4})-(\\d{2})-(\\d{2})/);return m?m[3]+'/'+m[2]+'/'+m[1]:String(v).slice(0,10)};\n const today=()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};\n const addDays=(v,n)=>{const d=new Date(v+'T12:00:00');d.setDate(d.getDate()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};\n const modeLabel={mensal:'Funcionário mensal',diaria:'Funcionário por diária',pontual:'Serviço pontual',revisar:'A definir na análise'};\n let state={requests:[],projects:[],proposals:[]},selected=null,busy=false,initialized=false;\n function classify(r){const t=norm([r.service,r.details].join(' '));const m=/(mensal|mensalista|funcionario fixo|por mes)/.test(t),d=/(diaria|diario|diarista|por dia trabalhado|por dia)/.test(t);return m&&!d?'mensal':d&&!m?'diaria':'revisar'}\n function heading(){return [...document.querySelectorAll('h1,h2,h3')].find(el=>norm(el.textContent).includes('solicitacoes de proposta recebidas pelo site'))}\n function ensureUI(){\n  const h=heading();if(!h)return false;if(document.getElementById('ntec-request-intake-panel'))return true;\n  const panel=document.createElement('div');panel.id='ntec-request-intake-panel';panel.className='panel';panel.style.margin='14px 0';\n  panel.innerHTML='<div class=\"titleline\"><div><h3>Análise do pedido inicial do cliente</h3><p class=\"sub\">Leia a solicitação original, avalie o escopo e prepare uma proposta comercial em rascunho. Nada é aprovado nem programado nesta etapa.</p></div><button type=\"button\" class=\"btn\" id=\"ntec-request-intake-refresh\">Atualizar pedidos</button></div><div class=\"tablewrap\"><table class=\"ntec-pg-table\"><thead><tr><th>Cliente e contato</th><th>Serviço solicitado</th><th>Local / detalhes</th><th>Recebida em</th><th>Status</th><th>Ação</th></tr></thead><tbody id=\"ntec-request-intake-body\"><tr><td colspan=\"6\" class=\"empty\">Carregando solicitações…</td></tr></tbody></table></div><div id=\"ntec-request-analysis-form\" class=\"panel hidden\" style=\"margin-top:16px\"><h3>Revisar solicitação e montar proposta</h3><div id=\"ntec-request-analysis-original\" class=\"ntec-pg-proposal-summary\"></div><div class=\"formgrid\"><div class=\"field\"><label for=\"ntec-request-service\">Serviço / título da proposta *</label><input id=\"ntec-request-service\" maxlength=\"180\" required/></div><div class=\"field\"><label for=\"ntec-request-mode\">Modelo de atendimento / cobrança *</label><select id=\"ntec-request-mode\"><option value=\"revisar\">Precisa definir / confirmar escopo</option><option value=\"mensal\">Funcionário mensal</option><option value=\"diaria\">Funcionário por diária</option><option value=\"pontual\">Serviço pontual / por entrega</option></select></div><div class=\"field\"><label for=\"ntec-request-staff\">Quantidade de funcionários (quando aplicável)</label><input id=\"ntec-request-staff\" type=\"number\" min=\"1\" max=\"100\" step=\"1\" value=\"1\"/></div><div class=\"field\"><label for=\"ntec-request-amount\">Valor proposto (R$) *</label><input id=\"ntec-request-amount\" type=\"number\" min=\"0.01\" step=\"0.01\" placeholder=\"Digite o valor após analisar o escopo\" required/></div><div class=\"field\"><label for=\"ntec-request-valid\">Validade da proposta *</label><input id=\"ntec-request-valid\" type=\"date\" required/></div><div class=\"field\"><label for=\"ntec-request-project\">Obra existente para vincular (opcional)</label><select id=\"ntec-request-project\"><option value=\"\">Não vincular obra agora</option></select></div></div><div class=\"field\"><label for=\"ntec-request-scope\">Escopo e condições da proposta *</label><textarea id=\"ntec-request-scope\" rows=\"7\" placeholder=\"Revise aqui o escopo que será enviado ao cliente.\" required></textarea></div><div class=\"ntec-pg-actions\"><button class=\"btn primary\" type=\"button\" id=\"ntec-request-create-draft\">Criar proposta em rascunho</button><button class=\"btn\" type=\"button\" id=\"ntec-request-analysis-cancel\">Cancelar análise</button><span id=\"ntec-request-analysis-message\" role=\"status\" aria-live=\"polite\"></span></div><p class=\"footnote\">A proposta ficará em rascunho para revisão. Este botão não envia a proposta ao cliente, não aprova contratação e não gera programação.</p></div>';\n  const desc=h.nextElementSibling?.tagName==='P'?h.nextElementSibling:h;desc.insertAdjacentElement('afterend',panel);\n  document.getElementById('ntec-request-intake-refresh').addEventListener('click',()=>load(true));\n  document.getElementById('ntec-request-analysis-cancel').addEventListener('click',()=>{document.getElementById('ntec-request-analysis-form').classList.add('hidden');selected=null});\n  document.getElementById('ntec-request-mode').addEventListener('change',toggleStaff);\n  document.getElementById('ntec-request-create-draft').addEventListener('click',createDraft);return true;\n }\n function toggleStaff(){const mode=document.getElementById('ntec-request-mode').value;document.getElementById('ntec-request-staff').disabled=!['mensal','diaria'].includes(mode)}\n function renderProjects(request){\n  const select=document.getElementById('ntec-request-project');if(!select)return;\n  const matching=state.projects.filter(p=>request?.company_name&&norm(p.clients?.company_name)===norm(request.company_name));\n  select.innerHTML='<option value=\"\">Não vincular obra agora</option>'+matching.map(p=>'<option value=\"'+esc(p.id)+'\">'+esc((p.work_number?'OBRA'+String(p.work_number).padStart(3,'0')+' · ':'')+p.name)+'</option>').join('');\n  if(request?.project_location&&norm(request.project_location).includes('obra teste')){const p=matching.find(x=>norm(x.name).includes('obra teste'));if(p)select.value=p.id}\n }\n function render(){\n  const body=document.getElementById('ntec-request-intake-body');if(!body)return;\n  body.innerHTML=state.requests.length?state.requests.map(r=>{\n   const status=r.status==='proposta_criada'?'Proposta criada':r.status==='em_atendimento'?'Em análise':r.status==='encerrada'?'Encerrada':'Recebida';\n   const linked=Boolean(r.linked_proposal)||r.status==='proposta_criada';const closed=r.status==='encerrada';\n   return '<tr><td><strong>'+esc(r.full_name)+'</strong><span class=\"ntec-pg-sub\">'+esc(r.company_name||'Empresa não informada')+'</span><span class=\"ntec-pg-sub\">'+esc(r.email)+' · '+esc(r.phone)+'</span></td><td>'+esc(r.service)+'</td><td><strong>'+esc(r.project_location||'Local não informado')+'</strong><span class=\"ntec-pg-sub\">'+esc(r.details)+'</span></td><td>'+esc(ptDate(r.created_at))+'</td><td><span class=\"ntec-pg-tag\">'+esc(status)+'</span>'+(r.linked_proposal?'<span class=\"ntec-pg-sub\">'+esc(r.linked_proposal.proposal_number)+' ('+esc(r.linked_proposal.status)+')</span>':'')+'</td><td><button type=\"button\" class=\"btn'+(linked||closed?'':' primary')+'\" data-ntec-analyze-request=\"'+esc(r.id)+'\" '+(linked||closed?'disabled':'')+'>'+(r.linked_proposal?'Proposta vinculada':closed?'Encerrada':'Analisar solicitação')+'</button></td></tr>';\n  }).join(''):'<tr><td colspan=\"6\" class=\"empty\">Nenhuma solicitação recebida pelo site.</td></tr>';\n  body.querySelectorAll('[data-ntec-analyze-request]').forEach(b=>b.addEventListener('click',()=>openAnalysis(b.dataset.ntecAnalyzeRequest)));\n  decorateExistingRequestRows();\n }\n function matchRequestToRow(row,button){\n  const text=norm(row?.textContent||'');\n  let request=state.requests.find(r=>(r.full_name&&text.includes(norm(r.full_name)))||(r.email&&text.includes(norm(r.email)))||(r.phone&&text.includes(norm(r.phone))));\n  if(request)return request;\n  const eligible=state.requests.filter(r=>!r.linked_proposal&&!['proposta_criada','encerrada'].includes(r.status));\n  const allButtons=[...document.querySelectorAll('button')].filter(b=>norm(b.textContent).includes('preparar proposta'));\n  const index=Math.max(0,allButtons.indexOf(button));\n  if(eligible.length===1)return eligible[0];\n  return eligible[index]||null;\n }\n function decorateExistingRequestRows(){\n  const buttons=[...document.querySelectorAll('button')].filter(b=>norm(b.textContent)==='preparar proposta'&&!b.dataset.ntecAnalysisAdded);\n  buttons.forEach(button=>{\n   const row=button.closest('tr');\n   if(!row)return;\n   button.dataset.ntecAnalysisAdded='1';\n   const request=matchRequestToRow(row,button);\n   const action=document.createElement('button');\n   action.type='button';action.className='btn primary';action.textContent='Analisar solicitação';\n   action.style.display='block';action.style.marginTop='6px';action.style.whiteSpace='normal';\n   if(request)action.dataset.ntecRequestId=request.id;\n   action.addEventListener('click',async()=>{\n    action.disabled=true;action.textContent='Abrindo análise…';\n    try{\n     if(!state.requests.length||!action.dataset.ntecRequestId)await load();\n     let selectedId=action.dataset.ntecRequestId;\n     let request=state.requests.find(r=>String(r.id)===String(selectedId));\n     if(!request)request=matchRequestToRow(row,button);\n     if(!request){const msg=document.getElementById('ntec-request-analysis-message');if(msg)msg.textContent='Não consegui vincular esta linha ao pedido original. Use “Atualizar pedidos” e tente novamente.';throw new Error('Solicitação não identificada na lista.')}\n     action.dataset.ntecRequestId=request.id;\n     await openAnalysis(request.id);\n    }catch(e){const msg=document.getElementById('ntec-request-analysis-message');if(msg)msg.textContent=e?.message||'Não foi possível abrir a análise.';else alert(e?.message||'Não foi possível abrir a análise.')}\n    finally{action.disabled=false;action.textContent='Analisar solicitação'}\n   });\n   button.insertAdjacentElement('afterend',action);\n  });\n }\n async function load(){\n  if(!ensureUI()||!api()?.loadProposalIntake)return;\n  const body=document.getElementById('ntec-request-intake-body');if(body)body.innerHTML='<tr><td colspan=\"6\" class=\"empty\">Carregando solicitações…</td></tr>';\n  try{state=await api().loadProposalIntake();render();decorateExistingRequestRows();decorateProposalRows()}\n  catch(e){if(body)body.innerHTML='<tr><td colspan=\"6\" class=\"empty\">Não foi possível carregar: '+esc(e?.message||'erro desconhecido')+'</td></tr>'}\n }\n async function openAnalysis(id){\n  selected=state.requests.find(r=>String(r.id)===String(id));if(!selected)return;\n  const form=document.getElementById('ntec-request-analysis-form');\n  document.getElementById('ntec-request-analysis-original').innerHTML='<strong>'+esc(selected.company_name||selected.full_name)+'</strong> · '+esc(selected.full_name)+'<br><strong>E-mail:</strong> '+esc(selected.email)+' · <strong>Telefone:</strong> '+esc(selected.phone)+'<br><strong>Serviço solicitado:</strong> '+esc(selected.service)+'<br><strong>Local:</strong> '+esc(selected.project_location||'Não informado')+'<hr><strong>Pedido original do cliente</strong><p>'+esc(selected.details)+'</p><small>Status atual: '+esc(selected.status)+'</small>';\n  document.getElementById('ntec-request-service').value=selected.service||'';\n  document.getElementById('ntec-request-mode').value=classify(selected);document.getElementById('ntec-request-staff').value='1';\n  document.getElementById('ntec-request-amount').value='';document.getElementById('ntec-request-valid').value=addDays(today(),7);\n  document.getElementById('ntec-request-scope').value='Serviço solicitado: '+(selected.service||'não especificado')+'\\nLocal: '+(selected.project_location||'não informado')+'\\n\\nEscopo informado pelo cliente:\\n'+(selected.details||'')+'\\n\\nEscopo, entregáveis, exclusões e condições comerciais a revisar antes do envio.';\n  renderProjects(selected);toggleStaff();document.getElementById('ntec-request-analysis-message').textContent='';\n  form.classList.remove('hidden');form.scrollIntoView({behavior:'smooth',block:'start'});\n  if(selected.status==='recebida'){try{await api().updateProposalRequestStatus(selected.id,'em_atendimento');selected.status='em_atendimento';await load();form.classList.remove('hidden')}catch(e){document.getElementById('ntec-request-analysis-message').textContent='A análise abriu, mas o status não foi atualizado: '+(e?.message||'erro')}} \n }\n async function createDraft(){\n  if(busy||!selected)return;const msg=document.getElementById('ntec-request-analysis-message');\n  const service=document.getElementById('ntec-request-service').value.trim(),mode=document.getElementById('ntec-request-mode').value;\n  const amount=Number(document.getElementById('ntec-request-amount').value),valid=document.getElementById('ntec-request-valid').value;\n  const scope=document.getElementById('ntec-request-scope').value.trim(),project=document.getElementById('ntec-request-project').value||null;\n  const staff=Number(document.getElementById('ntec-request-staff').value||1);\n  if(!service||!scope||!Number.isFinite(amount)||amount<=0||!valid){msg.textContent='Preencha o serviço, valor maior que zero, validade e escopo revisado.';return}\n  if(['mensal','diaria'].includes(mode)&&(!Number.isInteger(staff)||staff<1||staff>100)){msg.textContent='Informe uma quantidade válida de funcionários.';return}\n  if(!confirm('Criar a proposta comercial em RASCUNHO a partir desta solicitação? Ela ainda não será enviada ao cliente.'))return;\n  busy=true;const btn=document.getElementById('ntec-request-create-draft');btn.disabled=true;btn.textContent='Criando proposta…';msg.textContent='Salvando proposta em rascunho…';\n  try{\n   const result=await api().createDraftProposalFromRequest({request_id:selected.id,service,service_mode:mode,staff_count:staff,amount,valid_until:valid,project_id:project,description:scope});\n   msg.textContent='Proposta '+result.proposal.proposal_number+' criada em rascunho. Ainda não foi enviada nem programada.';\n   if(result.warning)msg.textContent+=' Aviso: o pedido foi salvo, mas seu status não foi atualizado: '+result.warning;\n   await load();document.getElementById('ntec-request-analysis-form').classList.add('hidden');selected=null;\n   openProposalPreview(result.proposal.id);\n  }catch(e){msg.textContent='Não foi possível criar a proposta: '+(e?.message||'erro desconhecido')}\n  finally{busy=false;btn.disabled=false;btn.textContent='Criar proposta em rascunho'}\n }\n\n function money(value){return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(value||0))}\n function proposalService(p){\n  const first=(String(p.description||'').split(/\\r?\\n/).map(x=>x.trim()).find(Boolean)||p.proposal_number||'Serviço proposto');\n  if(/^serviço solicitado:/i.test(first))return first.replace(/^serviço solicitado:\\s*/i,'')||'Serviço proposto';\n  return first.length>150?first.slice(0,147)+'…':first;\n }\n function proposalDocument(p){\n  const client=p.clients||{},project=p.projects||{};\n  const issued=p.created_at?new Date(p.created_at).toLocaleDateString('pt-BR'):(new Date()).toLocaleDateString('pt-BR');\n  const description=esc(String(p.description||'Escopo não informado.')).replace(/\\r\\n?/g,'\\n').replace(/\\n/g,'<br>');\n  const service=esc(proposalService(p)),clientName=esc(client.company_name||'Cliente não informado');\n  const contact=esc(client.contact_name||''),email=esc(client.email||''),phone=esc(client.phone||'');\n  const projectName=esc(project.name||'Não vinculada'),projectAddress=esc(project.address||''),valid=esc(ptDate(p.valid_until||''));\n  const status=String(p.status||'rascunho').toUpperCase();\n  return '<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>'+esc(p.proposal_number||'Proposta comercial')+' — NTEC</title><style>'+\n  '@page{size:A4 portrait;margin:16mm 15mm 18mm}*{box-sizing:border-box}body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;margin:0;font-size:11pt;line-height:1.5}.head{border-bottom:3px solid #d8a94c;padding-bottom:14px;margin-bottom:22px;display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.brand{font-size:18pt;font-weight:800;color:#142b46;letter-spacing:.3px}.brand-sub{font-size:8.5pt;color:#64748b;margin-top:4px}.doc-kicker{font-size:9pt;letter-spacing:1px;color:#64748b;font-weight:bold;text-transform:uppercase}.docno{font-size:14pt;font-weight:bold;color:#142b46;margin-top:5px;text-align:right}.status{display:inline-block;font-size:8pt;font-weight:bold;color:#92400e;background:#fef3c7;padding:4px 8px;border-radius:4px;margin-top:7px}.title{font-size:20pt;line-height:1.2;margin:0 0 5px;color:#142b46}.subtitle{color:#64748b;margin:0 0 18px;font-size:10pt}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:16px 0 20px}.box{border:1px solid #d8e0e8;border-radius:6px;padding:10px 12px;break-inside:avoid}.label{font-size:8pt;font-weight:bold;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}.value{font-size:10pt;font-weight:600;overflow-wrap:anywhere}.section{font-size:11pt;font-weight:bold;color:#142b46;border-bottom:1px solid #d8e0e8;padding-bottom:5px;margin:20px 0 8px;break-after:avoid}.scope{white-space:normal;overflow-wrap:anywhere}.amount{background:#f8fafc;border-left:4px solid #d8a94c;padding:13px 15px;margin:18px 0}.amount strong{display:block;font-size:19pt;color:#142b46;margin-top:4px}.foot{margin-top:30px;border-top:1px solid #d8e0e8;padding-top:10px;font-size:8pt;color:#64748b}.sign{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:40px;break-inside:avoid}.sigline{border-top:1px solid #64748b;text-align:center;padding-top:7px;font-size:9pt}.actions{display:flex;gap:10px;margin:12px 0 25px}.actions button{background:#142b46;color:white;border:0;border-radius:5px;padding:10px 14px;font-weight:bold;cursor:pointer}.actions button.secondary{background:#e2e8f0;color:#142b46}.note{font-size:9pt;color:#92400e;border:1px solid #f0d18b;background:#fffbeb;padding:9px 11px;border-radius:5px;margin-top:15px}@media print{.actions{display:none!important}.status,.box,.amount,.note{print-color-adjust:exact;-webkit-print-color-adjust:exact}}'+\n  '</style></head><body><div class=\"actions\"><button onclick=\"window.print()\">Imprimir / Salvar PDF</button><button class=\"secondary\" onclick=\"window.close()\">Fechar</button></div>'+\n  '<header class=\"head\"><div><div class=\"brand\">NTEC ENGENHARIA &amp; GEOTECNIA</div><div class=\"brand-sub\">Propostas técnicas e comerciais</div></div><div style=\"text-align:right\"><div class=\"doc-kicker\">Proposta comercial</div><div class=\"docno\">'+esc(p.proposal_number||'Número pendente')+'</div><span class=\"status\">'+esc(status)+' — PARA REVISÃO</span></div></header>'+\n  '<h1 class=\"title\">'+service+'</h1><p class=\"subtitle\">Proposta elaborada com base no escopo informado e sujeita à revisão comercial antes do envio ao cliente.</p>'+\n  '<div class=\"grid\"><div class=\"box\"><div class=\"label\">Cliente / empresa</div><div class=\"value\">'+clientName+'</div>'+(contact?'<div>'+contact+'</div>':'')+(email?'<div>'+email+'</div>':'')+(phone?'<div>'+phone+'</div>':'')+'</div>'+\n  '<div class=\"box\"><div class=\"label\">Identificação</div><div class=\"value\">Proposta: '+esc(p.proposal_number||'A definir')+'</div><div>Data: '+esc(issued)+'</div><div>Validade: '+(valid||'A definir')+'</div></div>'+\n  '<div class=\"box\"><div class=\"label\">Obra / local</div><div class=\"value\">'+projectName+'</div>'+(projectAddress?'<div>'+projectAddress+'</div>':'')+'</div>'+\n  '<div class=\"box\"><div class=\"label\">Modelo de atendimento</div><div class=\"value\">'+esc(modeLabel[p.service_mode]||'Conforme escopo descrito')+'</div>'+(p.staff_count?'<div>Quantidade prevista: '+esc(p.staff_count)+' funcionário(s)</div>':'')+'</div></div>'+\n  '<h2 class=\"section\">1. Escopo proposto</h2><div class=\"scope\">'+description+'</div>'+\n  '<div class=\"amount\"><div class=\"label\">Valor total proposto</div><strong>'+money(p.amount)+'</strong></div>'+\n  '<h2 class=\"section\">2. Validade e condições</h2><div>Esta proposta é válida até <strong>'+(valid||'data a confirmar')+'</strong>. As condições de pagamento, mobilização, jornada, exclusões e demais premissas comerciais devem ser confirmadas no escopo acima antes do envio ao cliente.</div>'+\n  '<div class=\"note\"><strong>Documento em rascunho.</strong> Não representa aceite, contratação, autorização de início ou confirmação de disponibilidade. Revise os dados cadastrais da NTEC, escopo, valor, validade e condições antes de enviar.</div>'+\n  '<div class=\"sign\"><div class=\"sigline\">NTEC Engenharia &amp; Geotecnia<br>Responsável comercial</div><div class=\"sigline\">Cliente<br>De acordo (após envio e aceite formal)</div></div>'+\n  '<footer class=\"foot\">Documento gerado pelo Portal de Gestão NTEC. Dados cadastrais e de contato da empresa devem ser completados no cadastro oficial antes da emissão externa.</footer></body></html>';\n }\n function ensureProposalPreview(){\n  let modal=document.getElementById('ntec-proposal-preview-modal');if(modal)return modal;\n  modal=document.createElement('div');modal.id='ntec-proposal-preview-modal';modal.style.cssText='display:none;position:fixed;inset:0;z-index:10050;background:rgba(15,23,42,.68);padding:18px;overflow:auto';\n  modal.innerHTML='<div style=\"max-width:900px;margin:18px auto;background:#fff;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.25);overflow:hidden\"><div style=\"display:flex;justify-content:space-between;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid #e2e8f0;position:sticky;top:0;background:#fff;z-index:2\"><strong id=\"ntec-proposal-preview-heading\">Visualizar proposta</strong><div style=\"display:flex;gap:8px;flex-wrap:wrap\"><button class=\"btn primary\" id=\"ntec-proposal-preview-pdf\" type=\"button\">Imprimir / Salvar PDF</button><button class=\"btn\" id=\"ntec-proposal-preview-close\" type=\"button\">Fechar</button></div></div><div id=\"ntec-proposal-preview-content\" style=\"padding:24px;max-width:800px;margin:auto\"></div></div>';\n  document.body.appendChild(modal);modal.addEventListener('click',e=>{if(e.target===modal)modal.style.display='none'});\n  modal.querySelector('#ntec-proposal-preview-close').addEventListener('click',()=>modal.style.display='none');\n  modal.querySelector('#ntec-proposal-preview-pdf').addEventListener('click',()=>{if(modal._proposal)printProposal(modal._proposal)});\n  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal.style.display!=='none')modal.style.display='none'});return modal;\n }\n function openProposalPreview(id){\n  const p=(state.proposals||[]).find(x=>String(x.id)===String(id));\n  if(!p){alert('Não consegui carregar os dados desta proposta. Clique em Atualizar pedidos e tente novamente.');return}\n  const modal=ensureProposalPreview();modal._proposal=p;\n  document.getElementById('ntec-proposal-preview-heading').textContent='Proposta '+(p.proposal_number||'sem número')+' · Visualização';\n  const html=proposalDocument(p),start=html.indexOf('<body>')+6,end=html.indexOf('</body>');\n  document.getElementById('ntec-proposal-preview-content').innerHTML=html.slice(start,end).replace('<div class=\"actions\"><button onclick=\"window.print()\">Imprimir / Salvar PDF</button><button class=\"secondary\" onclick=\"window.close()\">Fechar</button></div>','');\n  modal.style.display='block';modal.scrollTop=0;\n }\n function printProposal(p){\n  const win=window.open('','_blank');\n  if(!win){alert('O navegador bloqueou a janela de PDF. Permita pop-ups para este painel e tente novamente.');return}\n  win.document.open();win.document.write(proposalDocument(p));win.document.close();win.focus();setTimeout(()=>{try{win.print()}catch(e){}},500);\n }\n function decorateProposalRows(){\n  const body=document.getElementById('propsbody');if(!body||!Array.isArray(state.proposals))return;\n  const table=body.closest('table'),header=table?.querySelector('thead tr');if(!header)return;\n  if(!header.querySelector('[data-ntec-proposal-document-heading]')){const th=document.createElement('th');th.dataset.ntecProposalDocumentHeading='1';th.textContent='Documento';header.appendChild(th)}\n  for(const row of body.querySelectorAll('tr')){\n   if(row.querySelector('td[colspan]')||row.querySelector('[data-ntec-proposal-document-actions]'))continue;\n   const rowText=norm(row.textContent||'');const p=state.proposals.find(x=>x.proposal_number&&rowText.includes(norm(x.proposal_number)));if(!p)continue;\n   const cell=document.createElement('td');cell.dataset.ntecProposalDocumentActions='1';cell.style.minWidth='120px';\n   const view=document.createElement('button');view.type='button';view.className='btn';view.textContent='Ver proposta';view.style.display='block';view.style.marginBottom='5px';view.addEventListener('click',()=>openProposalPreview(p.id));\n   const pdf=document.createElement('button');pdf.type='button';pdf.className='btn primary';pdf.textContent='PDF';pdf.title='Abrir versão para imprimir ou salvar como PDF';pdf.addEventListener('click',()=>printProposal(p));\n   cell.append(view,pdf);row.appendChild(cell);\n  }\n  body.querySelectorAll('td[colspan]').forEach(td=>{td.colSpan=header.querySelectorAll('th').length});\n }\n function init(){\n  if(initialized)return;\n  if(!ensureUI()){\n   const obs=new MutationObserver(()=>{if(ensureUI()){obs.disconnect();init()}});\n   obs.observe(document.body,{childList:true,subtree:true});\n   return;\n  }\n  if(!api()?.loadProposalIntake){setTimeout(init,300);return}\n  initialized=true;\n  document.querySelector('#nav [data-page=\"comercial\"]')?.addEventListener('click',()=>load());\n  const rowObserver=new MutationObserver(()=>{decorateExistingRequestRows();decorateProposalRows()});\n  rowObserver.observe(document.body,{childList:true,subtree:true});\n  const proposalsBody=document.getElementById('propsbody');\n  if(proposalsBody)new MutationObserver(()=>decorateProposalRows()).observe(proposalsBody,{childList:true,subtree:true});\n  decorateProposalRows();\n  document.addEventListener('click',async event=>{\n   const button=event.target?.closest?.('button');\n   if(!button||norm(button.textContent)!=='preparar proposta')return;\n   event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();\n   const row=button.closest('tr');if(!row)return;\n   try{\n    await load();\n    const request=matchRequestToRow(row,button);\n    if(!request)throw new Error('Não consegui localizar o pedido original. Atualize os pedidos e tente novamente.');\n    await openAnalysis(request.id);\n   }catch(error){const msg=document.getElementById('ntec-request-analysis-message');if(msg)msg.textContent=error?.message||'Não foi possível abrir a solicitação.';else alert(error?.message||'Não foi possível abrir a solicitação.')}\n  },true);\n  load();\n }\n if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();\n})();\n</script>"

runtime = r'''<script>
(function(){
 const $=id=>document.getElementById(id);
 const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 const statusLabel={planejado:'Planejado',agendado:'Agendado',em_andamento:'Em andamento',aguardando_resultado:'Aguardando resultado',concluido:'Concluído',cancelado:'Cancelado'};
 const typeLabel={visita_tecnica:'Visita técnica',programacao_obra:'Atividade de obra',moldagem:'Moldagem',ruptura:'Ruptura',ensaio:'Ensaio',emissao_relatorio:'Emissão de relatório',outro:'Outro'};
 let data={items:[],projects:[],proposals:[],reports:[]},loaded=false,busy=false;
 const datePt=value=>{if(!value)return '—';const m=String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);return m?m[3]+'/'+m[2]+'/'+m[1]:String(value)};
 const addDaysIso=(value,days)=>{const d=new Date(String(value)+'T12:00:00');if(Number.isNaN(d.getTime()))return '';d.setDate(d.getDate()+Number(days));return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};
 const projectLabel=p=>'OBRA'+String(p.work_number||'').padStart(3,'0')+' · '+(p.clients?.company_name||'Cliente')+' — '+p.name;
 const selectedProject=()=>(data.projects||[]).find(p=>String(p.id)===$('ntec-pg-project').value);
 function message(text,isError=false){const el=$('ntec-pg-message');if(el){el.textContent=text||'';el.style.color=isError?'#b42318':''}}
 function setBusy(value){busy=value;const btn=$('ntec-pg-save');if(btn){btn.disabled=value;btn.textContent=value?'Salvando…':($('ntec-pg-id').value?'Atualizar atividade':'Salvar atividade')}}
 function approvedProposalsForProject(projectId){
  const p=data.projects.find(x=>String(x.id)===String(projectId));if(!p)return [];
  return data.proposals.filter(x=>x.status==='aprovada'&&(String(x.project_id||'')===String(projectId)||(!x.project_id&&String(x.client_id)===String(p.client_id))));
 }
 function normalizeProposalText(value){return String(value||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
 function inferProposalMode(proposal){
  if(['mensal','diaria','pontual'].includes(proposal?.service_mode))return proposal.service_mode;
  const text=normalizeProposalText((proposal?.description||'')+' '+(proposal?.service_mode||''));
  const monthly=/(mensal|mensalista|funcionario fixo|por mes|por m[eê]s)/.test(text);
  const daily=/(diaria|diario|diarista|por dia|por diaria|por dia trabalhado)/.test(text);
  if(monthly&&!daily)return 'mensal';
  if(daily&&!monthly)return 'diaria';
  return 'revisar';
 }
 const serviceModeLabel={mensal:'Funcionário mensal',diaria:'Funcionário por diária',pontual:'Serviço pontual',revisar:'Revisar escopo'};
 function renderProposalQueue(){
  const body=$('ntec-pg-proposal-queue-body');if(!body)return;
  const queue=(data.proposals||[]).filter(p=>!['recusada','expirada'].includes(p.status)&&!p.programming_generated_at);
  body.innerHTML=queue.length?queue.map(p=>{
   const mode=inferProposalMode(p),status=p.status==='aprovada'?'Aprovada':p.status==='enviada'?'Enviada':'Rascunho';
   const project=p.project_id?data.projects.find(x=>String(x.id)===String(p.project_id)):null;
   const client=p.clients?.company_name||project?.clients?.company_name||'Cliente';
   const action=p.status==='aprovada'?'Gerar programação':'Analisar e fechar';
   return '<tr><td><strong>'+esc(p.proposal_number||'Proposta sem número')+'</strong><span class="ntec-pg-sub">'+esc(client)+'</span>'+(project?'<span class="ntec-pg-sub">'+esc(project.name)+'</span>':'<span class="ntec-pg-sub">Obra ainda não vinculada</span>')+'</td><td>'+esc(p.description||'Escopo não informado')+'</td><td><span class="ntec-pg-tag">'+esc(serviceModeLabel[mode]||mode)+'</span></td><td>'+esc(status)+'</td><td><button type="button" class="btn primary" data-pg-review-proposal="'+esc(p.id)+'">'+action+'</button></td></tr>';
  }).join(''):'<tr><td colspan="5" class="empty">Nenhuma proposta aguardando programação. Propostas recusadas/expiradas não aparecem; propostas já programadas ficam registradas na lista de atividades.</td></tr>';
  body.querySelectorAll('[data-pg-review-proposal]').forEach(button=>button.addEventListener('click',()=>openProposalReview(button.dataset.pgReviewProposal)));
  injectProposalActions();
 }
 function injectProposalActions(){
  const body=$('propsbody');if(!body)return;
  const table=body.closest('table'),header=table?.querySelector('thead tr');
  if(!table||!header)return;
  if(!header.querySelector('[data-pg-proposal-action-heading]')){
   const th=document.createElement('th');th.dataset.pgProposalActionHeading='1';th.textContent='Programação';header.appendChild(th);
  }
  for(const row of [...body.querySelectorAll('tr')]){
   if(row.querySelector('td[colspan]')||row.querySelector('[data-pg-review-existing]'))continue;
   const text=row.textContent||'';
   const proposal=data.proposals.find(p=>p.proposal_number&&text.includes(p.proposal_number));
   if(!proposal)continue;
   const cell=document.createElement('td'),button=document.createElement('button');
   button.type='button';button.className='btn'+(proposal.programming_generated_at?'':' primary');
   button.dataset.pgReviewExisting=proposal.id;
   button.textContent=proposal.programming_generated_at?'Programação criada':proposal.status==='aprovada'?'Programar já aprovada':'Analisar e fechar';
   button.disabled=Boolean(proposal.programming_generated_at);
   button.addEventListener('click',()=>openProposalReviewFromExisting(proposal.id));
   cell.appendChild(button);row.appendChild(cell);
  }
  body.querySelectorAll('td[colspan]').forEach(td=>{td.colSpan=header.querySelectorAll('th').length});
 }
 async function openProposalReviewFromExisting(id){
  // Load the authoritative proposal/project rows before trying to populate the
  // review form. The proposal list can be opened before Programação was loaded.
  await loadData(true);
  const nav=document.querySelector('#nav [data-page="programacao"]');
  if(nav)nav.click();
  else document.querySelectorAll('.page').forEach(el=>el.classList.toggle('hidden',el.id!=='page-programacao'));
  openProposalReview(id);
 }
 function localToday(){
  const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
 }
 function renderReviewProjectOptions(proposal,selected=''){
  const clientId=proposal?.client_id;
  const eligible=data.projects.filter(p=>!clientId||String(p.client_id)===String(clientId)||String(p.id)===String(proposal.project_id));
  $('ntec-pg-review-project').innerHTML='<option value="">Selecione uma obra</option>'+eligible.map(p=>'<option value="'+esc(p.id)+'">'+esc(projectLabel(p))+'</option>').join('');
  if(selected&&eligible.some(p=>String(p.id)===String(selected)))$('ntec-pg-review-project').value=selected;
  else if(proposal?.project_id&&eligible.some(p=>String(p.id)===String(proposal.project_id)))$('ntec-pg-review-project').value=proposal.project_id;
 }
 function openProposalReview(id){
  const proposal=data.proposals.find(p=>String(p.id)===String(id));if(!proposal)return;
  $('ntec-pg-review-proposal-id').value=proposal.id;
  $('ntec-pg-review-summary').innerHTML='<strong>'+esc(proposal.proposal_number||'Proposta')+'</strong> · '+esc(proposal.clients?.company_name||'Cliente')+'<p>'+esc(proposal.description||'Escopo não informado')+'</p><small>Status atual: '+esc(proposal.status||'rascunho')+'. Ao confirmar, a proposta ficará aprovada e as atividades serão vinculadas a ela.</small>';
  renderReviewProjectOptions(proposal,proposal.project_id||'');
  $('ntec-pg-review-mode').value=inferProposalMode(proposal);
  $('ntec-pg-review-staff').value=String(proposal.staff_count||1);
  $('ntec-pg-review-start').value=proposal.service_start_date||localToday();
  $('ntec-pg-review-end').value=proposal.service_end_date||'';
  document.querySelectorAll('[data-pg-weekday]').forEach(el=>{el.checked=Array.isArray(proposal.work_weekdays)?proposal.work_weekdays.includes(Number(el.value)):[1,2,3,4,5].includes(Number(el.value))});
  $('ntec-pg-review-message').textContent='';
  $('ntec-pg-proposal-review').classList.remove('hidden');
  updateReviewPreview();
  $('ntec-pg-proposal-review').scrollIntoView({behavior:'smooth',block:'start'});
 }
 function updateReviewPreview(){
  const mode=$('ntec-pg-review-mode').value,start=$('ntec-pg-review-start').value,end=$('ntec-pg-review-end').value;
  const staff=Math.max(1,Number($('ntec-pg-review-staff').value||1));
  $('ntec-pg-review-weekdays').classList.toggle('hidden',mode!=='diaria');
  let count=0;
  if(start&&end&&end>=start){
   const a=new Date(start+'T12:00:00'),b=new Date(end+'T12:00:00');
   if(mode==='mensal'){
    let cursor=new Date(a.getFullYear(),a.getMonth(),1,12);
    while(cursor<=b){count++;cursor=new Date(cursor.getFullYear(),cursor.getMonth()+1,1,12)}
   }else if(mode==='pontual')count=1;
   else if(mode==='diaria'){
    const days=[...document.querySelectorAll('[data-pg-weekday]:checked')].map(el=>Number(el.value));
    for(let d=new Date(a);d<=b;d.setDate(d.getDate()+1))if(days.includes(d.getDay()===0?7:d.getDay()))count++;
   }
  }
  const units=mode==='mensal'?'faixa(s) mensal(is)':mode==='diaria'?'diária(s)':mode==='pontual'?'serviço pontual':'atividade(s)';
  let text=mode==='revisar'?'O escopo não deixa claro se o atendimento é mensal, por diária ou pontual. Selecione o modelo correto antes de aprovar.':count?('Serão criadas '+count+' '+units+' para '+staff+' funcionário(s), vinculadas à proposta.'): 'Informe um período válido e, para diária, marque ao menos um dia da semana.';
  $('ntec-pg-review-preview').textContent=text;
  return {count,mode};
 }
 async function approveSelectedProposal(){
  const button=$('ntec-pg-review-approve'),proposalId=$('ntec-pg-review-proposal-id').value,mode=$('ntec-pg-review-mode').value;
  const projectId=$('ntec-pg-review-project').value,start=$('ntec-pg-review-start').value,end=$('ntec-pg-review-end').value;
  const staff=Number($('ntec-pg-review-staff').value||1);
  const weekdays=[...document.querySelectorAll('[data-pg-weekday]:checked')].map(el=>Number(el.value));
  const preview=updateReviewPreview(),msg=$('ntec-pg-review-message');
  if(!proposalId||!projectId||!start||!end||end<start||mode==='revisar'||!Number.isInteger(staff)||staff<1||staff>100||(mode==='diaria'&&!weekdays.length)){
   msg.textContent='Revise o modelo de atendimento, a obra, a quantidade, o período e os dias de trabalho.';msg.style.color='#b42318';return;
  }
  if(!preview.count){msg.textContent='O período não gera nenhuma atividade. Revise as datas e os dias selecionados.';msg.style.color='#b42318';return}
  const proposal=data.proposals.find(p=>String(p.id)===String(proposalId));
  if(!proposal)return;
  if(!confirm('Aprovar a proposta '+(proposal.proposal_number||'')+' e gerar '+preview.count+' atividade(s) de '+serviceModeLabel[mode]+'? As atividades ficarão vinculadas à proposta e poderão ser editadas depois.'))return;
  button.disabled=true;button.textContent='Aprovando e programando…';msg.textContent='Salvando aprovação e criando atividades…';msg.style.color='';
  try{
   const result=await window.NTEC_SUPABASE.approveProposalAndSchedule({
    proposal_id:proposalId,project_id:projectId,service_mode:mode,staff_count:staff,
    service_start_date:start,service_end_date:end,work_weekdays:weekdays
   });
   const proposalAction=[...document.querySelectorAll('#propsbody [data-pg-review-existing]')].find(el=>String(el.dataset.pgReviewExisting)===String(proposalId));
   const proposalRow=proposalAction?.closest('tr');
   if(proposalRow){if(proposalRow.children[5])proposalRow.children[5].textContent='Aprovada';if(proposalAction){proposalAction.textContent='Programação criada';proposalAction.disabled=true;}}
   $('ntec-pg-proposal-review').classList.add('hidden');
   loaded=false;await loadData(true);
   message('Proposta '+(result.proposal?.proposal_number||'')+' aprovada. '+result.scheduledCount+' atividade(s) criada(s) na programação.');
  }catch(error){msg.textContent='Não foi possível fechar a proposta e gerar a programação: '+(error?.message||'erro desconhecido');msg.style.color='#b42318'}
  finally{button.disabled=false;button.textContent='Aprovar proposta e gerar programação'}
 }
 function refreshLinkedOptions(keepProposal='',keepReport=''){
  const projectId=$('ntec-pg-project').value;
  const proposals=approvedProposalsForProject(projectId),proposalEl=$('ntec-pg-proposal');
  proposalEl.innerHTML='<option value="">Sem proposta vinculada</option>'+proposals.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.proposal_number||'Proposta')+' · '+esc(p.description||'Escopo não informado')+' · R$ '+esc(Number(p.amount||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}))+'</option>').join('');
  if(keepProposal&&proposals.some(p=>String(p.id)===String(keepProposal)))proposalEl.value=keepProposal;
  const reports=data.reports.filter(r=>String(r.project_id)===String(projectId));
  $('ntec-pg-report').innerHTML='<option value="">Vincular depois</option>'+reports.map(r=>'<option value="'+esc(r.id)+'">'+esc(r.report_number||'Sem número')+' · '+esc(r.title||typeLabel[r.report_type]||'Relatório')+' ('+esc(r.status||'rascunho')+')</option>').join('');
  if(keepReport&&reports.some(r=>String(r.id)===String(keepReport)))$('ntec-pg-report').value=keepReport;
 }
 function syncMoldingOptions(){const wrap=$('ntec-pg-molding-options');if(wrap)wrap.classList.toggle('hidden',$('ntec-pg-type').value!=='moldagem')}
 function renderProjects(selected=''){
  $('ntec-pg-project').innerHTML='<option value="">Selecione uma obra</option>'+(data.projects||[]).map(p=>'<option value="'+esc(p.id)+'">'+esc(projectLabel(p))+'</option>').join('');
  if(selected)$('ntec-pg-project').value=selected;
  refreshLinkedOptions();
 }
 function renderTable(){
  const query=$('ntec-pg-search').value.trim().toLowerCase(),filter=$('ntec-pg-filter').value;
  const items=data.items.filter(item=>{
   const project=item.projects?.name||'',client=item.projects?.clients?.company_name||'',proposal=item.proposals?.proposal_number||'',text=[item.title,item.description,project,client,proposal,item.item_type,item.status].join(' ').toLowerCase();
   return (!query||text.includes(query))&&(!filter||item.status===filter);
  });
  $('ntec-pg-count-planned').textContent=data.items.filter(x=>['planejado','agendado'].includes(x.status)).length;
  $('ntec-pg-count-active').textContent=data.items.filter(x=>['em_andamento','aguardando_resultado'].includes(x.status)).length;
  $('ntec-pg-count-done').textContent=data.items.filter(x=>x.status==='concluido').length;
  $('ntec-pg-body').innerHTML=items.length?items.map(item=>{
   const project=item.projects||{},proposal=item.proposals||{},report=item.reports||{};
   const details=[typeLabel[item.item_type]||item.item_type,item.description].filter(Boolean).join(' · ');
   const series=item.sample_series?'Série '+item.sample_series:'Série não definida',age=item.test_age_days!=null?String(item.test_age_days)+' dia(s)':'Idade não definida';
   const statusClass=item.status==='concluido'?' done':item.status==='cancelado'?' overdue':'';
   const parentText=item.parent_item_id?'Ruptura programada a partir da moldagem':'';
   const ruptureAction=item.item_type==='ruptura'&&item.report_id?'<button type="button" class="btn" data-pg-open-rupture="'+esc(item.report_id)+'">Lançar ensaio</button>':'';
   return '<tr><td><strong>'+esc(datePt(item.scheduled_date))+(item.scheduled_end_date&&item.scheduled_end_date!==item.scheduled_date?' a '+esc(datePt(item.scheduled_end_date)):'')+'</strong><span class="ntec-pg-sub">'+esc(item.scheduled_time?String(item.scheduled_time).slice(0,5):'Horário não definido')+(item.duration_minutes?' · '+esc(item.duration_minutes)+' min':'')+'</span></td><td><strong>'+esc(item.title)+'</strong><span class="ntec-pg-sub">'+esc(project.name||'Obra')+' · '+esc(project.clients?.company_name||'Cliente')+'</span><span class="ntec-pg-sub">'+esc(details)+'</span>'+(parentText?'<span class="ntec-pg-sub">'+esc(parentText)+'</span>':'')+'</td><td>'+(proposal.proposal_number?'<strong>'+esc(proposal.proposal_number)+'</strong>':'<span class="ntec-pg-sub">Sem proposta</span>')+'<span class="ntec-pg-sub">'+(report.report_number?esc(report.report_number)+' · ':'')+esc(report.title||'Sem relatório vinculado')+'</span>'+(item.quantity!=null?'<span class="ntec-pg-sub">Quantidade prevista: '+esc(item.quantity)+' '+esc(item.unit)+'</span>':'')+'</td><td>'+esc(series)+'<span class="ntec-pg-sub">'+esc(age)+'</span></td><td><span class="ntec-pg-tag'+statusClass+'">'+esc(statusLabel[item.status]||item.status)+'</span></td><td><div class="ntec-pg-buttons">'+ruptureAction+'<button type="button" class="btn" data-pg-edit="'+esc(item.id)+'">Editar</button><button type="button" class="btn" data-pg-delete="'+esc(item.id)+'">Excluir</button></div></td></tr>';
  }).join(''):'<tr><td class="ntec-pg-empty" colspan="6">'+(data.items.length?'Nenhuma atividade corresponde ao filtro.':'Nenhuma atividade programada. Clique em “Nova atividade” para começar.')+'</td></tr>';
  $('ntec-pg-body').querySelectorAll('[data-pg-edit]').forEach(button=>button.addEventListener('click',()=>editItem(button.dataset.pgEdit)));
  $('ntec-pg-body').querySelectorAll('[data-pg-delete]').forEach(button=>button.addEventListener('click',()=>deleteItem(button.dataset.pgDelete)));
  $('ntec-pg-body').querySelectorAll('[data-pg-open-rupture]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.pgOpenRupture;if(typeof window.openRuptureEntry==='function')window.openRuptureEntry(id);else alert('Abra Relatórios técnicos e use “Lançar ruptura” no relatório vinculado.')})); 
 }
 async function loadData(force=false){
  if(loaded&&!force){renderTable();return}
  message('Carregando dados da programação…');
  try{
   data=await window.NTEC_SUPABASE.loadProgrammingData();loaded=true;
   renderProjects($('ntec-pg-project').value);
   renderProposalQueue();renderTable();message('');
  }catch(error){
   const text=error?.message||'erro desconhecido';message('Não foi possível carregar a programação: '+text,true);
   if(/administrativo|login/i.test(text)){
    const nav=document.querySelector('#nav [data-page="programacao"]');if(nav)nav.hidden=true;
   }
  }
 }
 function resetForm(){
  $('ntec-pg-id').value='';$('ntec-pg-parent').value='';$('ntec-pg-form-title').textContent='Nova atividade';
  ['ntec-pg-title','ntec-pg-description','ntec-pg-notes','ntec-pg-time','ntec-pg-duration','ntec-pg-series','ntec-pg-age','ntec-pg-quantity','ntec-pg-unit'].forEach(id=>$(id).value='');
  $('ntec-pg-type').value='visita_tecnica';$('ntec-pg-status').value='planejado';$('ntec-pg-date').value=new Date().toISOString().slice(0,10);$('ntec-pg-auto-ruptures').checked=true;$('ntec-pg-auto-ruptures').disabled=false;$('ntec-pg-cp-per-age').value='2';syncMoldingOptions();
  $('ntec-pg-project').value='';refreshLinkedOptions();$('ntec-pg-form').classList.add('hidden');message('');
  $('ntec-pg-save').textContent='Salvar atividade';
 }
 function editItem(id){
  const item=data.items.find(x=>String(x.id)===String(id));if(!item)return;
  $('ntec-pg-id').value=item.id;$('ntec-pg-parent').value=item.parent_item_id||'';$('ntec-pg-form-title').textContent='Editar atividade';
  renderProjects(item.project_id);
  $('ntec-pg-proposal').value=item.proposal_id||'';$('ntec-pg-report').value=item.report_id||'';
  $('ntec-pg-type').value=item.item_type||'outro';$('ntec-pg-auto-ruptures').checked=false;$('ntec-pg-auto-ruptures').disabled=true;$('ntec-pg-cp-per-age').value='2';syncMoldingOptions();$('ntec-pg-title').value=item.title||'';
  $('ntec-pg-date').value=item.scheduled_date||'';$('ntec-pg-time').value=item.scheduled_time?String(item.scheduled_time).slice(0,5):'';
  $('ntec-pg-duration').value=item.duration_minutes??'';$('ntec-pg-status').value=item.status||'planejado';
  $('ntec-pg-series').value=item.sample_series??'';$('ntec-pg-age').value=item.test_age_days??'';
  $('ntec-pg-quantity').value=item.quantity??'';$('ntec-pg-unit').value=item.unit||'';
  $('ntec-pg-description').value=item.description||'';$('ntec-pg-notes').value=item.notes||'';
  $('ntec-pg-form').classList.remove('hidden');$('ntec-pg-save').textContent='Atualizar atividade';message('');
  $('ntec-pg-form').scrollIntoView({behavior:'smooth',block:'start'});
 }
 async function saveItem(){
  if(busy)return;
  const projectId=$('ntec-pg-project').value,title=$('ntec-pg-title').value.trim(),date=$('ntec-pg-date').value;
  if(!projectId||!title||!date){message('Preencha obra, título e data programada.',true);return}
  const proposalId=$('ntec-pg-proposal').value||null;
  const proposal=data.proposals.find(p=>String(p.id)===String(proposalId));
  const project=data.projects.find(p=>String(p.id)===String(projectId));
  if(proposal&&project&&String(proposal.project_id||'')!==String(projectId)&&String(proposal.client_id)!==String(project.client_id)){message('A proposta selecionada não pertence à obra/cliente escolhido.',true);return}
  const payload={
   id:$('ntec-pg-id').value||undefined,project_id:projectId,proposal_id:proposalId,report_id:$('ntec-pg-report').value||null,parent_item_id:$('ntec-pg-parent').value||null,
   item_type:$('ntec-pg-type').value,title,scheduled_date:date,scheduled_time:$('ntec-pg-time').value||null,
   duration_minutes:$('ntec-pg-duration').value||null,sample_series:$('ntec-pg-series').value||null,test_age_days:$('ntec-pg-age').value||null,
   quantity:$('ntec-pg-quantity').value===''?null:$('ntec-pg-quantity').value,unit:$('ntec-pg-unit').value.trim(),
   status:$('ntec-pg-status').value,description:$('ntec-pg-description').value.trim(),notes:$('ntec-pg-notes').value.trim()
  };
  setBusy(true);message('Salvando atividade…');
  let parentSaved=false,generated=0;
  const isNew=!payload.id,generateRuptures=isNew&&payload.item_type==='moldagem'&&$('ntec-pg-auto-ruptures').checked;
  const cpPerAge=Math.max(1,Math.min(100,Math.floor(Number($('ntec-pg-cp-per-age').value||2))));
  try{
   const saved=await window.NTEC_SUPABASE.saveProgrammingItem(payload);parentSaved=true;
   if(generateRuptures){
    if(!saved?.id)throw new Error('Moldagem salva, mas não foi retornado o identificador para vincular as rupturas.');
    for(const age of [7,28]){
     const ruptureDate=addDaysIso(payload.scheduled_date,age);
     await window.NTEC_SUPABASE.saveProgrammingItem({
      project_id:payload.project_id,proposal_id:payload.proposal_id,report_id:payload.report_id,parent_item_id:saved.id,
      item_type:'ruptura',title:'Ruptura'+(payload.sample_series?' — Série '+payload.sample_series:'')+' — '+age+' dias',
      description:'Atividade prevista automaticamente a partir da moldagem de '+datePt(payload.scheduled_date)+'. Confirme a execução real do ensaio e registre os resultados somente após a ruptura.',
      scheduled_date:ruptureDate,scheduled_time:null,duration_minutes:null,sample_series:payload.sample_series||null,test_age_days:age,
      quantity:cpPerAge,unit:'CPs',status:'agendado',
      notes:'Gerada automaticamente pela atividade de moldagem '+saved.id+'. Data prevista; não representa ensaio realizado nem resultado medido.'
     });
     generated++;
    }
   }
   loaded=false;await loadData(true);resetForm();
   message(generateRuptures?'Moldagem salva e '+generated+' rupturas programadas para 7 e 28 dias. Nenhum resultado foi lançado.':(payload.item_type==='moldagem'&&!isNew?'Moldagem atualizada. As rupturas já existentes foram preservadas.':'Atividade salva.'));
  }catch(error){
   if(parentSaved){loaded=false;await loadData(true);resetForm();message('A moldagem foi salva, mas a geração automática das rupturas ficou incompleta. Confira as atividades e programe as idades pendentes manualmente. Detalhe: '+(error?.message||'erro desconhecido'),true)}
   else message('Não foi possível salvar: '+(error?.message||'erro desconhecido'),true);
  }finally{setBusy(false);if(!$('ntec-pg-id').value)$('ntec-pg-save').textContent='Salvar atividade'}
 }
 async function deleteItem(id){
  const item=data.items.find(x=>String(x.id)===String(id));if(!item)return;
  if(!confirm('Excluir a atividade "'+item.title+'"? Esta ação não pode ser desfeita.'))return;
  try{await window.NTEC_SUPABASE.deleteProgrammingItem(id);loaded=false;await loadData(true);message('Atividade excluída.')}
  catch(error){message('Não foi possível excluir: '+(error?.message||'erro desconhecido'),true)}
 }
 function init(){
  if(!window.NTEC_SUPABASE)return;
  const nav=document.querySelector('#nav [data-page="programacao"]');
  nav?.addEventListener('click',()=>loadData(false));
  const proposalsNav=document.querySelector('#nav [data-page="propostas"]');
  proposalsNav?.addEventListener('click',()=>loadData(false));
  const proposalsBody=$('propsbody');
  if(proposalsBody&&typeof MutationObserver!=='undefined')new MutationObserver(()=>injectProposalActions()).observe(proposalsBody,{childList:true,subtree:true});
  $('ntec-pg-new')?.addEventListener('click',()=>{$('ntec-pg-form').classList.remove('hidden');resetForm();$('ntec-pg-form').classList.remove('hidden');$('ntec-pg-title').focus()});
  $('ntec-pg-cancel')?.addEventListener('click',resetForm);
  $('ntec-pg-save')?.addEventListener('click',saveItem);
  $('ntec-pg-refresh')?.addEventListener('click',()=>loadData(true));
  $('ntec-pg-search')?.addEventListener('input',renderTable);
  $('ntec-pg-filter')?.addEventListener('change',renderTable);
  $('ntec-pg-project')?.addEventListener('change',()=>refreshLinkedOptions());
  $('ntec-pg-review-mode')?.addEventListener('change',updateReviewPreview);
  $('ntec-pg-review-start')?.addEventListener('change',updateReviewPreview);
  $('ntec-pg-review-end')?.addEventListener('change',updateReviewPreview);
  $('ntec-pg-review-staff')?.addEventListener('input',updateReviewPreview);
  document.querySelectorAll('[data-pg-weekday]').forEach(el=>el.addEventListener('change',updateReviewPreview));
  $('ntec-pg-review-approve')?.addEventListener('click',approveSelectedProposal);
  $('ntec-pg-review-cancel')?.addEventListener('click',()=>{$('ntec-pg-proposal-review').classList.add('hidden');$('ntec-pg-review-message').textContent=''});
  $('ntec-pg-type')?.addEventListener('change',()=>{
   const type=$('ntec-pg-type').value;syncMoldingOptions();
   if(type==='ruptura'&&$('ntec-pg-status').value==='planejado')$('ntec-pg-status').value='aguardando_resultado';
   if(type==='moldagem'&&!$('ntec-pg-title').value)$('ntec-pg-title').value='Moldagem de concreto';
   if(type==='ruptura'&&!$('ntec-pg-title').value)$('ntec-pg-title').value='Ensaio de ruptura de corpo de prova';
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>
'''
_closing = re.search(r'</body>\s*</html>\s*$', s, flags=re.I)
if not _closing:
    raise SystemExit("script do módulo de programação: final do documento não encontrado")
s = s[:_closing.start()] + runtime + "\n" + request_intake_runtime + "\n" + s[_closing.start():]

for token in ["page-programacao","ntec-pg-body","loadProgrammingData","saveProgrammingItem","data-page=\"programacao\""]:
    if token not in s:
        raise SystemExit("Validação do módulo de programação falhou: " + token)

path.write_text(s, encoding="utf-8")
print("Applied NTEC programming module to", path)
