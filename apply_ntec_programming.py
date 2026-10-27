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
  supabase.from('programming_items').select('id,project_id,proposal_id,report_id,parent_item_id,item_type,title,description,scheduled_date,scheduled_time,duration_minutes,sample_series,test_age_days,quantity,unit,status,notes,created_at,updated_at,projects(name,work_number,client_id,clients(company_name)),proposals(proposal_number,status,description),reports(report_number,title,report_type,status)').order('scheduled_date',{ascending:true}).order('scheduled_time',{ascending:true}),
  supabase.from('projects').select('id,name,client_id,work_number,status,created_at,clients(company_name)').order('created_at',{ascending:false}),
  supabase.from('proposals').select('id,proposal_number,client_id,project_id,description,amount,status,valid_until,created_at,clients(company_name)').eq('status','aprovada').order('created_at',{ascending:false}),
  supabase.from('reports').select('id,project_id,report_number,title,report_type,report_date,status').order('report_date',{ascending:false})
 ]);
 for(const result of [itemsResult,projectsResult,proposalsResult,reportsResult])if(result.error)throw result.error;
 return {items:itemsResult.data||[],projects:projectsResult.data||[],proposals:proposalsResult.data||[],reports:reportsResult.data||[]};
},
async saveProgrammingItem(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!payload?.project_id||!payload?.scheduled_date||!String(payload?.title||'').trim())throw new Error('Informe a obra, o título e a data programada.');
 const row={project_id:payload.project_id,proposal_id:payload.proposal_id||null,report_id:payload.report_id||null,parent_item_id:payload.parent_item_id||null,item_type:payload.item_type||'outro',title:String(payload.title).trim(),description:String(payload.description||''),scheduled_date:payload.scheduled_date,scheduled_time:payload.scheduled_time||null,duration_minutes:payload.duration_minutes==null||payload.duration_minutes===''?null:Number(payload.duration_minutes),sample_series:payload.sample_series==null||payload.sample_series===''?null:Number(payload.sample_series),test_age_days:payload.test_age_days==null||payload.test_age_days===''?null:Number(payload.test_age_days),quantity:payload.quantity==null||payload.quantity===''?null:Number(payload.quantity),unit:String(payload.unit||''),status:payload.status||'planejado',notes:String(payload.notes||''),updated_at:new Date().toISOString()};
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
getProgrammingAccess(){return Boolean(currentSession&&currentProfile?.role==='admin');},
"""
once("async saveReport(r){", api_methods + "async saveReport(r){", "API do módulo de programação")

nav_anchor = '<button data-page="propostas">▤ <span>Propostas</span></button><button data-page="medicoes">▧ <span>Medições</span></button>'
nav_new = '<button data-page="propostas">▤ <span>Propostas</span></button><button data-page="programacao">▦ <span>Programação</span></button><button data-page="medicoes">▧ <span>Medições</span></button>'
once(nav_anchor, nav_new, "navegação da programação")

section = r'''<section class="page hidden" id="page-programacao">
 <div class="titleline"><div><h1>Programação de atividades</h1><p>Organize visitas, moldagens, rupturas, ensaios e entregas por obra, usando propostas aprovadas como referência.</p></div><button class="btn primary" id="ntec-pg-new" type="button">+ Nova atividade</button></div>
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
 <div class="tablewrap"><table class="ntec-pg-table"><thead><tr><th>Data / horário</th><th>Atividade / obra</th><th>Proposta / relatório</th><th>Série / idade</th><th>Status</th><th>Ações</th></tr></thead><tbody id="ntec-pg-body"><tr><td colspan="6" class="empty">Abra Programação para carregar as atividades.</td></tr></tbody></table></div>
 <p class="footnote">A programação registra previsões. A data prevista de ruptura não comprova que o ensaio foi executado; leituras de prensa e resultados reais continuam sendo lançados no módulo de ensaios.</p>
</section>
'''
import re
_medicoes = re.findall(r'<section\b(?=[^>]*\bid=["\']page-medicoes["\'])[^>]*>', s)
if len(_medicoes) != 1:
    raise SystemExit("seção da programação: esperado 1 início de seção page-medicoes, encontrados " + str(len(_medicoes)))
s = s.replace(_medicoes[0], section + "\n" + _medicoes[0], 1)

css = r'''
.ntec-pg-molding-options{margin:10px 0;padding:12px;background:#f4f7fa;border:1px solid var(--line);border-radius:9px}.ntec-pg-auto-label{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}.ntec-pg-auto-label input{width:auto}.ntec-pg-molding-options .field{margin:10px 0 0;max-width:260px}.ntec-pg-metrics{margin:12px 0 18px}.ntec-pg-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.ntec-pg-toolbar input{flex:1;min-width:200px}.ntec-pg-toolbar select{min-height:40px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px 10px;color:var(--ink)}.ntec-pg-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:12px}.ntec-pg-actions [role=status]{font-size:12px;color:var(--muted)}.ntec-pg-table td{vertical-align:top}.ntec-pg-sub{display:block;color:var(--muted);font-size:12px;margin-top:4px}.ntec-pg-tag{display:inline-block;border-radius:999px;background:#edf2f7;color:#334155;padding:4px 8px;font-size:11px;font-weight:700;white-space:nowrap}.ntec-pg-tag.overdue{background:#fff1f0;color:#9b1c1c}.ntec-pg-tag.done{background:#e9f7ef;color:#166534}.ntec-pg-buttons{display:flex;gap:5px;flex-wrap:wrap}.ntec-pg-buttons .btn{padding:6px 8px;font-size:11px}.ntec-pg-empty{padding:22px;text-align:center;color:var(--muted)}@media(max-width:700px){.ntec-pg-toolbar>*{width:100%;min-width:0}.ntec-pg-actions #ntec-pg-message{width:100%}}
'''
if '</style>' not in s:
    raise SystemExit("estilos da programação: tag style não encontrada")
s = s.replace('</style>', css + '</style>', 1)

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
  return data.proposals.filter(x=>String(x.project_id||'')===String(projectId)||(!x.project_id&&String(x.client_id)===String(p.client_id)));
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
   return '<tr><td><strong>'+esc(datePt(item.scheduled_date))+'</strong><span class="ntec-pg-sub">'+esc(item.scheduled_time?String(item.scheduled_time).slice(0,5):'Horário não definido')+(item.duration_minutes?' · '+esc(item.duration_minutes)+' min':'')+'</span></td><td><strong>'+esc(item.title)+'</strong><span class="ntec-pg-sub">'+esc(project.name||'Obra')+' · '+esc(project.clients?.company_name||'Cliente')+'</span><span class="ntec-pg-sub">'+esc(details)+'</span>'+(parentText?'<span class="ntec-pg-sub">'+esc(parentText)+'</span>':'')+'</td><td>'+(proposal.proposal_number?'<strong>'+esc(proposal.proposal_number)+'</strong>':'<span class="ntec-pg-sub">Sem proposta</span>')+'<span class="ntec-pg-sub">'+(report.report_number?esc(report.report_number)+' · ':'')+esc(report.title||'Sem relatório vinculado')+'</span>'+(item.quantity!=null?'<span class="ntec-pg-sub">Quantidade prevista: '+esc(item.quantity)+' '+esc(item.unit)+'</span>':'')+'</td><td>'+esc(series)+'<span class="ntec-pg-sub">'+esc(age)+'</span></td><td><span class="ntec-pg-tag'+statusClass+'">'+esc(statusLabel[item.status]||item.status)+'</span></td><td><div class="ntec-pg-buttons">'+ruptureAction+'<button type="button" class="btn" data-pg-edit="'+esc(item.id)+'">Editar</button><button type="button" class="btn" data-pg-delete="'+esc(item.id)+'">Excluir</button></div></td></tr>';
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
   renderTable();message('');
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
  $('ntec-pg-new')?.addEventListener('click',()=>{$('ntec-pg-form').classList.remove('hidden');resetForm();$('ntec-pg-form').classList.remove('hidden');$('ntec-pg-title').focus()});
  $('ntec-pg-cancel')?.addEventListener('click',resetForm);
  $('ntec-pg-save')?.addEventListener('click',saveItem);
  $('ntec-pg-refresh')?.addEventListener('click',()=>loadData(true));
  $('ntec-pg-search')?.addEventListener('input',renderTable);
  $('ntec-pg-filter')?.addEventListener('change',renderTable);
  $('ntec-pg-project')?.addEventListener('change',()=>refreshLinkedOptions());
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
s = s[:_closing.start()] + runtime + "\n" + s[_closing.start():]

for token in ["page-programacao","ntec-pg-body","loadProgrammingData","saveProgrammingItem","data-page=\"programacao\""]:
    if token not in s:
        raise SystemExit("Validação do módulo de programação falhou: " + token)

path.write_text(s, encoding="utf-8")
print("Applied NTEC programming module to", path)
