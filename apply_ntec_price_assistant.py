#!/usr/bin/env python3
"""Adds the NTEC price-review helper and reference-price autocomplete to the admin site."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/admin/index.html")
s = path.read_text(encoding="utf-8")

def once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: esperado 1 trecho, encontrados {count}")
    s = s.replace(old, new, 1)

api_methods = r"""async requestProposalPriceAI(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 const {data,error}=await supabase.functions.invoke('ntec-price-ai',{body:payload});
 if(error){
  let detail=null;
  try{const response=error.context;if(response&&typeof response.clone==='function')detail=await response.clone().json()}catch{}
  if(detail?.error)throw new Error(String(detail.error)+(detail.detail?' — '+detail.detail:''));
  throw new Error(error.message||'Falha ao chamar a IA de precificação.');
 }
 if(data?.error)throw new Error(data.error+(data.detail?' — '+data.detail:''));
 if(!data?.estimate)throw new Error('A IA não retornou uma estimativa utilizável.');
 return data.estimate;
},
async loadProposalPriceReviews(referenceValueId){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 let query=supabase.from('proposal_price_reviews').select('id,reference_value_id,reviewed_by,item_name,item_code,category,unit,base_price,recommended_price,market_price_min,market_price_max,annual_adjustment_percent,band_percent,index_name,index_period,years_elapsed,assessment,notes,applied_to_reference,applied_at,created_at').order('created_at',{ascending:false}).limit(100);
 if(referenceValueId)query=query.eq('reference_value_id',referenceValueId);
 const {data,error}=await query;
 if(error)throw error;
 return data||[];
},
async saveProposalPriceReview(payload){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 if(!payload?.reference_value_id)throw new Error('Selecione um item de referência.');
 const requiredNumbers=['base_price','recommended_price','market_price_min','market_price_max','annual_adjustment_percent','band_percent','years_elapsed'];
 for(const key of requiredNumbers){if(!Number.isFinite(Number(payload[key])))throw new Error('Valor inválido na análise: '+key);}
 if(Number(payload.base_price)<0||Number(payload.recommended_price)<0||Number(payload.market_price_min)<0||Number(payload.market_price_max)<Number(payload.market_price_min))throw new Error('A faixa de preço informada é inválida.');
 if(!['abaixo','na_faixa','acima','sem_preco_numerico'].includes(payload.assessment))throw new Error('Classificação da análise inválida.');
 const row={reference_value_id:payload.reference_value_id,reviewed_by:currentSession.user.id,item_name:String(payload.item_name||'').slice(0,250),item_code:String(payload.item_code||'').slice(0,30)||null,category:String(payload.category||'').slice(0,180),unit:String(payload.unit||'').slice(0,40),base_price:Number(payload.base_price),recommended_price:Number(payload.recommended_price),market_price_min:Number(payload.market_price_min),market_price_max:Number(payload.market_price_max),annual_adjustment_percent:Number(payload.annual_adjustment_percent),band_percent:Number(payload.band_percent),index_name:String(payload.index_name||'').slice(0,100),index_period:String(payload.index_period||'').slice(0,40),years_elapsed:Number(payload.years_elapsed),assessment:payload.assessment,notes:String(payload.notes||'').slice(0,3000)};
 const {data,error}=await supabase.from('proposal_price_reviews').insert(row).select('id,reference_value_id,item_name,base_price,recommended_price,market_price_min,market_price_max,annual_adjustment_percent,band_percent,index_name,index_period,years_elapsed,assessment,notes,applied_to_reference,applied_at,created_at').single();
 if(error)throw error;
 return data;
},
async applyProposalPriceReview(reviewId){
 if(!currentSession||currentProfile?.role!=='admin')throw new Error('Acesso administrativo necessário.');
 const {data:review,error:readError}=await supabase.from('proposal_price_reviews').select('id,reference_value_id,recommended_price,applied_to_reference').eq('id',reviewId).single();
 if(readError)throw readError;
 const appliedAt=new Date().toISOString();
 const {data:reference,error:updateReferenceError}=await supabase.from('proposal_reference_values').update({reference_price:Number(review.recommended_price),price_label:null,updated_at:appliedAt}).eq('id',review.reference_value_id).select('id,item_name,reference_price,updated_at').single();
 if(updateReferenceError)throw updateReferenceError;
 const {data:updatedReview,error:updateReviewError}=await supabase.from('proposal_price_reviews').update({applied_to_reference:true,applied_at:appliedAt}).eq('id',review.id).select('id,applied_to_reference,applied_at').single();
 if(updateReviewError)throw new Error('O preço de referência foi atualizado, mas não consegui marcar a análise como aplicada: '+updateReviewError.message);
 return {reference,review:updatedReview};
},
"""
once("async loadProposalReferenceValues(){", api_methods + "async loadProposalReferenceValues(){", "API do assistente de precificação")

runtime = r'''<script>
(function(){
 const api=()=>window.NTEC_SUPABASE;
 const $=id=>document.getElementById(id);
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const norm=v=>String(v||'').toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim();
 const money=v=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(v||0));
 let rows=[],selected=null,lastEstimate=null,lastSavedReview=null,busy=false,initialized=false,activeInput=null,popup=null;
 let compositionProposals=[],activeCompositionProposal=null,compositionDirty=false,compositionBusy=false;
 function msg(t,error){const el=$('ntec-ai-message');if(el){el.textContent=t||'';el.style.color=error?'#b42318':'var(--muted)'}}
 function sourceDate(item){
  const applied=(window.NTEC_PRICE_REVIEW_HISTORY||[]).find(r=>r.applied_to_reference&&r.applied_at);
  if(applied)return new Date(applied.applied_at);
  const created=item.created_at?new Date(item.created_at):null;
  const updated=item.updated_at?new Date(item.updated_at):null;
  const manuallyChanged=created&&updated&&!Number.isNaN(created.getTime())&&!Number.isNaN(updated.getTime())&&(updated.getTime()-created.getTime()>60000);
  const raw=manuallyChanged?item.updated_at:(/RG\s*28/i.test(item.source_reference||'')?'2022-11-27T12:00:00':(item.updated_at||item.created_at));
  const d=raw?new Date(raw):new Date();
  return Number.isNaN(d.getTime())?new Date():d;
 }
 function elapsedYears(from,to=new Date()){
  const ms=Math.max(0,to.getTime()-from.getTime());
  return Math.round((ms/(365.2425*24*60*60*1000))*1000)/1000;
 }
 function ensureAssistant(){
  const panel=$('ntec-ref-price-panel');
  if(!panel)return false;
  if($('ntec-price-ai-panel'))return true;
  const box=document.createElement('div');
  box.id='ntec-price-ai-panel';box.className='panel';box.style.cssText='margin:16px 0;padding:16px;background:var(--surface,#fff)';
  box.innerHTML='<div class="titleline"><div><h3>Assistente inteligente de precificação</h3><p class="sub">Revise os valores antigos, estime um reajuste anual e registre a decisão antes de alterar a tabela oficial.</p></div><span class="ntec-ai-tag">Revisão humana obrigatória</span></div>'+
   '<div class="ntec-ai-disclaimer">A estimativa abaixo aplica o índice escolhido ao preço-base e cria uma faixa de tolerância configurável. É um alerta de atualização de custos, não uma pesquisa automática de cotações concorrentes. Confirme valores reais de fornecedores, mão de obra, deslocamento e equipamentos antes de aprovar.</div>'+
   '<div class="formgrid"><div class="field"><label for="ntec-ai-item">Item da tabela de referência *</label><select id="ntec-ai-item"><option value="">Carregando itens…</option></select></div>'+
   '<div class="field"><label for="ntec-ai-index">Índice anual de reajuste</label><select id="ntec-ai-index"><option value="INCC-M" data-rate="6.75" data-period="out/2026" data-url="https://portal.fgv.br/noticias/incc-m-outubro-2026">INCC-M · 6,75% · out/2026 (FGV)</option><option value="IPCA" data-rate="4.58" data-period="set/2026" data-url="https://www.ibge.gov.br/indicadores/inflacao">IPCA · 4,58% · set/2026 (IBGE)</option><option value="SINAPI" data-rate="6.81" data-period="set/2026" data-url="https://www.ibge.gov.br/indicadores/sinapi">SINAPI · 6,81% · 12 meses até set/2026 (IBGE)</option><option value="personalizado" data-rate="" data-period="informado pelo administrador" data-url="">Personalizado — informar percentual</option></select></div>'+
   '<div class="field"><label for="ntec-ai-rate">Percentual anual (%) *</label><input id="ntec-ai-rate" type="number" min="-20" max="100" step="0.01" value="6.75" required/><small class="muted small">INCC-M é um ponto de partida para custos de construção; avalie se o índice é adequado ao serviço.</small></div>'+
   '<div class="field"><label for="ntec-ai-band">Margem da faixa (%)</label><input id="ntec-ai-band" type="number" min="0" max="50" step="0.5" value="10" required/><small class="muted small">Ex.: 10% abaixo e acima do preço projetado.</small></div></div>'+
   '<div class="ntec-ai-actions"><button class="btn primary" id="ntec-ai-estimate" type="button">Estimar reajuste e comparar</button><button class="btn" id="ntec-ai-real-estimate" type="button">Pesquisar mercado com IA</button><button class="btn" id="ntec-ai-save" type="button" disabled>Salvar revisão anual</button><button class="btn hidden" id="ntec-ai-apply" type="button">Aplicar preço recomendado à tabela</button><span id="ntec-ai-message" role="status" aria-live="polite"></span></div>'+
   '<div id="ntec-ai-result" class="ntec-ai-result"><p>Selecione um item para revisar. A tabela original só será alterada após você salvar e aplicar uma recomendação.</p></div>'+
   '<div class="ntec-ai-history"><h4>Histórico de revisões do item</h4><div id="ntec-ai-history-body" class="muted small">Selecione um item para consultar as revisões anteriores.</div></div>'+
   '<p class="footnote">Índices de partida verificados em 28/10/2026: <a href="https://portal.fgv.br/noticias/incc-m-outubro-2026" target="_blank" rel="noopener">INCC-M FGV — 6,75% acumulado em 12 meses (out/2026)</a> e <a href="https://www.ibge.gov.br/indicadores/inflacao" target="_blank" rel="noopener">IPCA IBGE — 4,58% acumulado em 12 meses (set/2026)</a> e <a href="https://www.ibge.gov.br/indicadores/sinapi" target="_blank" rel="noopener">SINAPI IBGE — custo do m², 6,81% em 12 meses (set/2026)</a>. Atualize o percentual quando sair uma nova divulgação e valide se o índice representa seus custos.</p>';
  const title=panel.querySelector('.titleline');
  panel.insertBefore(box,title?title.nextSibling:panel.firstChild);
  const st=document.createElement('style');st.id='ntec-price-ai-style';
  st.textContent='#ntec-price-ai-panel{border:1px solid var(--line);border-radius:12px}#ntec-price-ai-panel .ntec-ai-tag{font-size:11px;font-weight:700;padding:5px 9px;border-radius:999px;background:#f1f5f9;color:#334155;white-space:nowrap}.ntec-ai-disclaimer{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.5;margin:8px 0 14px}.ntec-ai-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0}.ntec-ai-actions [role=status]{font-size:12px}.ntec-ai-result{border:1px solid var(--line);border-radius:10px;padding:12px;margin-top:12px;line-height:1.55}.ntec-ai-result .metrics{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:8px;margin:10px 0}.ntec-ai-result .metric{border:1px solid var(--line);border-radius:8px;padding:10px}.ntec-ai-result .metric span{display:block;font-size:11px;color:var(--muted)}.ntec-ai-result .metric strong{display:block;font-size:15px;margin-top:3px}.ntec-ai-status{font-weight:700;display:inline-block;padding:5px 9px;border-radius:999px;background:#fef3c7;color:#92400e}.ntec-ai-status.good{background:#dcfce7;color:#166534}.ntec-ai-status.bad{background:#fee2e2;color:#991b1b}.ntec-ai-history{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.ntec-ai-history h4{margin:0 0 8px}.ntec-ai-history table{width:100%;border-collapse:collapse;font-size:12px}.ntec-ai-history th,.ntec-ai-history td{text-align:left;padding:7px;border-bottom:1px solid var(--line);vertical-align:top}.ntec-ai-history th{color:var(--muted);font-weight:600}.ntec-ai-history .muted{color:var(--muted)}.ntec-price-autocomplete{position:fixed;z-index:100000;max-height:320px;overflow:auto;background:#fff;border:1px solid #cbd5e1;border-radius:9px;box-shadow:0 12px 35px #0f172a25;color:#0f172a}.ntec-price-autocomplete button{display:flex;flex-direction:column;gap:3px;width:100%;text-align:left;border:0;border-bottom:1px solid #e2e8f0;background:#fff;padding:10px 12px;cursor:pointer;color:inherit}.ntec-price-autocomplete button:hover,.ntec-price-autocomplete button:focus{background:#f1f5f9}.ntec-price-autocomplete strong{font-size:13px}.ntec-price-autocomplete small{font-size:11px;color:#64748b;white-space:normal;line-height:1.35}.ntec-price-autocomplete .ntec-ref-norm{color:#1e3a5f;background:#eff6ff;border-radius:5px;padding:4px 6px}.ntec-price-autocomplete .ntec-ref-norm b{font-size:10px}.ntec-price-autocomplete .ntec-ref-note{color:#475569}.ntec-price-autocomplete b{font-size:12px}@media(max-width:720px){.ntec-ai-result .metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.ntec-ai-actions>*{max-width:100%}}';
  document.head.appendChild(st);
  $('ntec-ai-index').addEventListener('change',syncIndexRate);
  $('ntec-ai-item').addEventListener('change',()=>selectItem($('ntec-ai-item').value));
  $('ntec-ai-estimate').addEventListener('click',estimate);
  $('ntec-ai-real-estimate').addEventListener('click',requestAiEstimate);
  $('ntec-ai-save').addEventListener('click',saveReview);
  $('ntec-ai-apply').addEventListener('click',applyReview);
  return true;
 }
 function syncIndexRate(){
  const sel=$('ntec-ai-index'),opt=sel?.selectedOptions?.[0];if(!opt)return;
  if(sel.value!=='personalizado')$('ntec-ai-rate').value=opt.dataset.rate||'';
  else $('ntec-ai-rate').value='';
 }
 function renderOptions(keepId){
  const select=$('ntec-ai-item');if(!select)return;
  const active=rows.filter(r=>r.is_active);
  select.innerHTML='<option value="">Selecione um item cadastrado…</option>'+active.map(r=>{
   const codes=extractNormTokens(r.normative_references||'');
   const normLabel=codes.slice(0,3).join(' / ')||'Norma a confirmar conforme escopo';
   return '<option value="'+esc(r.id)+'">'+esc('['+normLabel+'] '+(r.item_code?r.item_code+' · ':'')+r.item_name+' — '+r.category+' ('+r.unit+')'+(r.scope_accreditation_status?' ['+r.scope_accreditation_status+']':'')+(r.price_label?' ['+r.price_label+']':''))+'</option>';
  }).join('');
  if(keepId&&active.some(r=>String(r.id)===String(keepId)))select.value=keepId;
 }
 async function loadRefs(){
  if(!api()?.loadProposalReferenceValues)return;
  try{rows=await api().loadProposalReferenceValues();window.NTEC_PRICE_REFERENCE_CACHE=rows;renderOptions(selected?.id);renderNormBundleOptions();await selectItem($('ntec-ai-item')?.value||'')}
  catch(e){msg('Não foi possível carregar os preços de referência: '+(e?.message||'erro'),true)}
 }
 async function selectItem(id){
  selected=rows.find(r=>String(r.id)===String(id))||null;lastEstimate=null;lastSavedReview=null;
  $('ntec-ai-save').disabled=true;$('ntec-ai-apply').classList.add('hidden');
  if(!selected){$('ntec-ai-result').innerHTML='<p>Selecione um item para revisar. A tabela original só será alterada após você salvar e aplicar uma recomendação.</p>';$('ntec-ai-history-body').textContent='Selecione um item para consultar as revisões anteriores.';return}
  msg('Carregando histórico…');
  try{
   const history=await api().loadProposalPriceReviews(selected.id);window.NTEC_PRICE_REVIEW_HISTORY=history;
   renderHistory(history);msg('');
   const latestApplied=history.find(h=>h.applied_to_reference&&h.applied_at);
   if(latestApplied){
    const d=new Date(latestApplied.applied_at);
    $('ntec-ai-result').innerHTML='<p><strong>Última revisão aplicada:</strong> '+esc(d.toLocaleDateString('pt-BR'))+' · preço aplicado: <strong>'+money(latestApplied.recommended_price)+'</strong>. Gere uma nova estimativa para revisar o próximo ciclo.</p>';
   } else {
    $('ntec-ai-result').innerHTML='<p><strong>Preço cadastrado:</strong> '+money(selected.reference_price)+(selected.price_label?' · rótulo: '+esc(selected.price_label):'')+'.'+(/RG\s*28/i.test(selected.source_reference||'')?' A origem é a planilha RG 28, revisada em 27/11/2022; a estimativa considerará esse marco como base inicial.':' A estimativa usa a data de cadastro/alteração como base inicial.')+'</p>';
   }
  }catch(e){$('ntec-ai-history-body').textContent='Não foi possível carregar o histórico: '+(e?.message||'erro');msg('Histórico indisponível.',true)}
 }
 function renderHistory(history){
  const el=$('ntec-ai-history-body');if(!el)return;
  if(!history?.length){el.innerHTML='<p class="muted small">Ainda não há revisões salvas para este item.</p>';return}
  el.innerHTML='<div class="tablewrap"><table><thead><tr><th>Data</th><th>Índice</th><th>Faixa projetada</th><th>Recomendado</th><th>Comparação</th><th>Status</th></tr></thead><tbody>'+
   history.slice(0,8).map(h=>'<tr><td>'+esc(new Date(h.created_at).toLocaleDateString('pt-BR'))+'</td><td>'+esc(h.index_name)+'<br>'+esc(Number(h.annual_adjustment_percent).toLocaleString('pt-BR')+'%')+' ('+esc(h.index_period)+')</td><td>'+money(h.market_price_min)+' — '+money(h.market_price_max)+'</td><td>'+money(h.recommended_price)+'</td><td>'+esc(({abaixo:'Abaixo da projeção',na_faixa:'Dentro da faixa',acima:'Acima da projeção',sem_preco_numerico:'Sem preço numérico'}[h.assessment]||h.assessment))+'</td><td>'+(h.applied_to_reference?'<strong>Aplicada</strong>':'Pendente de aprovação')+'</td></tr>').join('')+'</tbody></table></div>';
 }
 function estimate(){
  if(!selected){msg('Selecione um item.',true);return}
  const rate=Number($('ntec-ai-rate').value),band=Number($('ntec-ai-band').value);
  if(!Number.isFinite(rate)||rate< -20||rate>100){msg('Informe um percentual anual entre -20% e 100%.',true);return}
  if(!Number.isFinite(band)||band<0||band>50){msg('A margem precisa ficar entre 0% e 50%.',true);return}
  const item=selected,history=window.NTEC_PRICE_REVIEW_HISTORY||[];
  const latestApplied=history.find(h=>h.applied_to_reference&&h.applied_at);
  const from=latestApplied?new Date(latestApplied.applied_at):sourceDate(item);
  const years=elapsedYears(from);
  const base=Number(item.reference_price);
  const indexOpt=$('ntec-ai-index').selectedOptions[0],indexName=$('ntec-ai-index').value;
  const period=indexOpt?.dataset.period||'personalizado';
  if(item.price_label||!Number.isFinite(base)||base<=0){
   lastEstimate=null;
   $('ntec-ai-result').innerHTML='<p><strong>Não é possível estimar automaticamente este item.</strong> O cadastro tem valor textual ('+esc(item.price_label||'sem preço numérico')+') ou preço zero. Edite o item para informar um preço-base numérico antes de continuar. Esse item não poderá receber recomendação de preço zero.</p>';
   $('ntec-ai-save').disabled=true;$('ntec-ai-apply').classList.add('hidden');msg('Estimativa bloqueada: falta preço numérico.',true);
   return;
  }
  const factor=Math.pow(1+rate/100,years);
  const recommended=Math.round(base*factor*100)/100;
  const low=Math.round(recommended*(1-band/100)*100)/100;
  const high=Math.round(recommended*(1+band/100)*100)/100;
  const current=base;
  const assessment=current<low?'abaixo':current>high?'acima':'na_faixa';
  const deltaPct=base>0?(recommended/base-1)*100:0;
  const notes='Projeção paramétrica: preço-base corrigido por taxa anual de '+rate.toFixed(2)+'% por '+years.toFixed(2)+' ano(s), com faixa de tolerância de '+band.toFixed(1)+'%. Não representa cotação de concorrente nem série histórica mensal integral. Confirme mercado, equipe, equipamento, deslocamento, impostos e margem.';
  lastEstimate={reference_value_id:item.id,item_name:item.item_name,item_code:item.item_code,category:item.category,unit:item.unit,base_price:base,recommended_price:recommended,market_price_min:low,market_price_max:high,annual_adjustment_percent:rate,band_percent:band,index_name:indexName,index_period:period,years_elapsed:years,assessment,notes};
  const status=assessment==='na_faixa'?'Dentro da faixa projetada':assessment==='abaixo'?'Preço cadastrado abaixo da faixa projetada':'Preço cadastrado acima da faixa projetada';
  const css=assessment==='na_faixa'?'good':assessment==='abaixo'?'bad':'';
  $('ntec-ai-result').innerHTML='<div><span class="ntec-ai-status '+css+'">'+esc(status)+'</span></div><div class="metrics">'+
   '<div class="metric"><span>Preço atual cadastrado</span><strong>'+money(current)+'</strong></div>'+
   '<div class="metric"><span>Preço recomendado</span><strong>'+money(recommended)+'</strong></div>'+
   '<div class="metric"><span>Faixa projetada</span><strong>'+money(low)+' – '+money(high)+'</strong></div>'+
   '<div class="metric"><span>Variação estimada</span><strong>'+deltaPct.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%</strong></div></div>'+
   '<p><strong>Critério:</strong> '+esc(indexName)+' — '+esc(period)+', aplicado por '+years.toLocaleString('pt-BR',{maximumFractionDigits:2})+' ano(s); margem ±'+band.toLocaleString('pt-BR')+'%.</p><p class="muted small">'+esc(notes)+'</p>';
  $('ntec-ai-save').disabled=false;$('ntec-ai-apply').classList.add('hidden');lastSavedReview=null;
  msg('Estimativa pronta. Revise os pressupostos e salve para manter o histórico.');
 }
 async function requestAiEstimate(){
  if(busy||!selected)return;
  // Pesquisa de mercado é válida mesmo sem preço-base numérico (ex.: item marcado como "Incluso").
  const button=$('ntec-ai-real-estimate');busy=true;button.disabled=true;button.textContent='Pesquisando…';msg('Consultando a IA e pesquisando referências públicas de mercado. Isso pode levar alguns instantes…');
  try{
   const result=await api().requestProposalPriceAI({item_name:selected.item_name,item_code:selected.item_code,category:selected.category,unit:selected.unit,current_price:Number(selected.reference_price||0),price_label:selected.price_label||'',notes:selected.notes||''});
   if(!result||!Number.isFinite(Number(result.recommended_price))||!Number.isFinite(Number(result.market_price_min))||!Number.isFinite(Number(result.market_price_max)))throw new Error('A IA retornou valores inválidos.');
   const min=Number(result.market_price_min),max=Number(result.market_price_max),recommended=Number(result.recommended_price);
   const current=Number(selected.reference_price||0),assessment=(selected.price_label||current<=0)?'sem_preco_numerico':(result.assessment|| (current<min?'abaixo':current>max?'acima':'na_faixa'));
   const sources=Array.isArray(result.sources)?result.sources:[];
   const factors=Array.isArray(result.cost_factors)?result.cost_factors:[];
   const noteLines=['Análise de mercado assistida por IA com pesquisa web.','Data da análise: '+(result.data_as_of||new Date().toISOString().slice(0,10)), 'Preço-base NTEC: '+(selected.price_label||money(current)),'Modelo: '+(result.model||'não informado'),'Confiança: '+(result.confidence||'não informada'),'Racional: '+(result.rationale||'não informado'), 'Fatores de custo: '+(factors.join('; ')||'não informados'), 'Fontes consultadas: '+(sources.map(x=>(x.title||x.url)+' — '+x.url+(x.summary?' — '+x.summary:'')).join(' | ')||'Nenhuma fonte listada pela IA'),'Aviso: estimativa indicativa; confira escopo, unidade, impostos, deslocamento, equipamento, equipe e margem antes de aplicar.'];
   const years=1;
   const band=Math.max(0,Math.min(50,Math.round((Math.max(recommended-min,max-recommended)/Math.max(recommended,1))*1000)/10));
   lastEstimate={reference_value_id:selected.id,item_name:selected.item_name,item_code:selected.item_code,category:selected.category,unit:selected.unit,base_price:current,recommended_price:Math.round(recommended*100)/100,market_price_min:Math.round(min*100)/100,market_price_max:Math.round(max*100)/100,annual_adjustment_percent:Number(result.annual_adjustment_percent),band_percent:band,index_name:'IA OpenAI + pesquisa web',index_period:result.data_as_of||new Date().toISOString().slice(0,10),years_elapsed:years,assessment,notes:noteLines.join('\n')};
   lastSavedReview=null;$('ntec-ai-save').disabled=false;$('ntec-ai-apply').classList.add('hidden');
   const label=assessment==='abaixo'?'Preço atual abaixo da faixa estimada':assessment==='acima'?'Preço atual acima da faixa estimada':assessment==='sem_preco_numerico'?'Sem preço numérico comparável':'Preço atual dentro da faixa estimada';
   const css=assessment==='abaixo'?'bad':assessment==='na_faixa'?'good':'';
   const sourceHtml=sources.length?sources.map(source=>'<li><a href="'+esc(source.url)+'" target="_blank" rel="noopener">'+esc(source.title||source.url)+'</a>'+(source.summary?'<div class="muted small">'+esc(source.summary)+'</div>':'')+'</li>').join(''):'<li>Nenhuma fonte verificável retornada. Use a estimativa apenas como triagem e confira os preços manualmente.</li>';
   $('ntec-ai-result').innerHTML='<div><span class="ntec-ai-status '+css+'">'+esc(label)+'</span> <span class="ntec-ai-tag">Confiança: '+esc(result.confidence||'não informada')+'</span></div><div class="metrics">'+
   '<div class="metric"><span>Preço atual NTEC</span><strong>'+(selected.price_label?esc(selected.price_label)+' <small>(sem preço numérico)</small>':money(current))+'</strong></div>'+
   '<div class="metric"><span>Recomendação da IA</span><strong>'+money(recommended)+'</strong></div>'+
   '<div class="metric"><span>Faixa estimada</span><strong>'+money(min)+' – '+money(max)+'</strong></div>'+
   '<div class="metric"><span>Reajuste anual sugerido</span><strong>'+Number(result.annual_adjustment_percent).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%</strong></div></div>'+
   '<p><strong>Justificativa:</strong> '+esc(result.rationale||'Sem justificativa retornada.')+'</p>'+
   (factors.length?'<p><strong>Fatores de custo a validar:</strong> '+esc(factors.join('; '))+'</p>':'')+
   '<p><strong>Fontes da pesquisa:</strong></p><ul>'+sourceHtml+'</ul>'+
   '<p class="muted small">Estimativa de apoio à decisão, não cotação garantida. O preço oficial só muda após salvar a revisão e clicar em “Aplicar preço recomendado à tabela”.</p>';
   msg('Análise de IA pronta. Revise as fontes e salve a revisão para manter o histórico.');
  }catch(e){
   const reason=e?.message||'erro desconhecido';
   const itemQuery=[selected?.item_name,selected?.category,'preço unitário mercado São Paulo Brasil'].filter(Boolean).join(' ');
   const editalQuery=[selected?.item_name,selected?.category,'preço unitário edital licitação'].filter(Boolean).join(' ');
   const google='https://www.google.com/search?q='+encodeURIComponent(itemQuery);
   const editais='https://www.google.com/search?q='+encodeURIComponent(editalQuery);
   $('ntec-ai-result').innerHTML='<p><strong>A pesquisa automática de mercado não foi concluída.</strong> Não há faixa de preço nem recomendação de mercado salva. Motivo: '+esc(reason)+'</p><p>Você pode abrir pesquisas públicas para este item enquanto a integração da IA é corrigida:</p><ul><li><a href="'+esc(google)+'" target="_blank" rel="noopener">Pesquisar preços do serviço na internet</a></li><li><a href="'+esc(editais)+'" target="_blank" rel="noopener">Pesquisar preços em editais e licitações</a></li></ul>';
   msg('A pesquisa automática falhou; não foi usado reajuste por índice como substituto.',true);
  }
  finally{busy=false;button.disabled=false;button.textContent='Pesquisar mercado com IA'}
 }
 async function saveReview(){
  if(busy||!lastEstimate)return;
  if(lastEstimate.assessment==='sem_preco_numerico'){msg('Esta revisão não pode ser salva como recomendação de preço: falta preço numérico.',true);return}
  busy=true;$('ntec-ai-save').disabled=true;msg('Salvando revisão no Supabase…');
  try{
   lastSavedReview=await api().saveProposalPriceReview(lastEstimate);
   const history=await api().loadProposalPriceReviews(selected.id);window.NTEC_PRICE_REVIEW_HISTORY=history;renderHistory(history);
   $('ntec-ai-apply').classList.remove('hidden');msg('Revisão salva. O preço oficial ainda não foi alterado.');
  }catch(e){msg('Não foi possível salvar a revisão: '+(e?.message||'erro'),true);$('ntec-ai-save').disabled=false}
  finally{busy=false}
 }
 async function applyReview(){
  if(busy||!lastSavedReview?.id)return;
  if(!confirm('Aplicar '+money(lastSavedReview.recommended_price)+' como novo preço de referência de “'+selected.item_name+'”? O histórico será mantido, mas o valor oficial será alterado.'))return;
  busy=true;$('ntec-ai-apply').disabled=true;msg('Aplicando preço…');
  try{
   await api().applyProposalPriceReview(lastSavedReview.id);
   rows=await api().loadProposalReferenceValues();window.NTEC_PRICE_REFERENCE_CACHE=rows;renderOptions(selected.id);
   await selectItem(selected.id);msg('Novo preço de referência aplicado e histórico preservado.');
  }catch(e){msg('Não foi possível aplicar o preço: '+(e?.message||'erro'),true)}
  finally{busy=false;$('ntec-ai-apply').disabled=false}
 }
 function createPopup(){
  if(popup)return popup;
  popup=document.createElement('div');popup.className='ntec-price-autocomplete';popup.style.display='none';document.body.appendChild(popup);return popup;
 }
 function closePopup(){if(popup){popup.style.display='none';popup.innerHTML=''}activeInput=null}
 function descriptionInput(el){
  return el instanceof HTMLInputElement&&(el.matches('[data-line-field="description"],.ntec-line-description')||el.dataset.lineField==='description');
 }
 function matchingRows(query){
  const words=norm(query).split(' ').filter(Boolean);
  if(!words.length)return [];
  return (window.NTEC_PRICE_REFERENCE_CACHE||rows).filter(r=>r.is_active&&words.every(w=>norm([r.item_name,r.item_code,r.section_name,r.category,r.unit,r.notes].join(' ')).includes(w))).slice(0,10);
 }
 function showPopup(input,items){
  const p=createPopup();activeInput=input;
  if(!items.length){closePopup();return}
  p.innerHTML=items.map((r,i)=>'<button type="button" data-ntec-ref-pick="'+i+'"><strong>'+esc(r.item_name)+'</strong><small>'+esc([r.item_code,r.category,r.unit].filter(Boolean).join(' · '))+'</small><small class="ntec-ref-norm"><b>VÍNCULO NORMATIVO:</b> '+esc(r.normative_references||'NBR a definir conforme método e escopo')+'</small>'+(r.normative_note?'<small class="ntec-ref-note">'+esc(r.normative_note)+'</small>':'')+'<b>'+(r.price_label?esc(r.price_label)+' · valor numérico '+money(r.reference_price):money(r.reference_price))+'</b></button>').join('');
  p.style.display='block';
  const rect=input.getBoundingClientRect(),left=Math.max(8,Math.min(rect.left,window.innerWidth-340));
  p.style.left=left+'px';p.style.top=Math.min(rect.bottom+3,window.innerHeight-280)+'px';p.style.width=Math.min(Math.max(rect.width,320),window.innerWidth-left-8)+'px';
  p.querySelectorAll('[data-ntec-ref-pick]').forEach(btn=>btn.addEventListener('click',()=>pickReference(input,items[Number(btn.dataset.ntecRefPick)])));
 }
 function setInput(input,value){
  if(!input)return;
  input.value=value;
  input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new Event('change',{bubbles:true}));
 }
 function pickReference(input,item){
  const row=input.closest('tr');if(!row||!item)return;
  const normPrefix=String(item.normative_references||'').trim();input.dataset.ntecPickingRef='1';setInput(input,(normPrefix?normPrefix+' — ':'')+item.item_name);delete input.dataset.ntecPickingRef;
  const unit=row.querySelector('[data-line-field="unit"],.ntec-line-unit,input[name="unit"]');
  const price=row.querySelector('[data-line-field="unit_price"],input[name="unit_price"],.ntec-line-price,[data-field="unit_price"]');
  if(unit)setInput(unit,item.unit||'serviço');
  if(price)setInput(price,Number(item.reference_price||0).toFixed(2));
  row.dataset.referenceValueId=item.id;
  row.dataset.normativeReferences=String(item.normative_references||'');
  row.dataset.normativeNote=String(item.normative_note||'');
  row.dataset.scopeAccreditationStatus=String(item.scope_accreditation_status||'');
  const normLabel=row.querySelector('[data-line-norm]');if(normLabel)normLabel.textContent=normPrefix?'NORMAS/REFERÊNCIAS: '+normPrefix:'Norma específica a confirmar conforme método e escopo contratado.';
  const normNote=row.querySelector('[data-line-norm-note]');if(normNote)normNote.textContent=String(item.normative_note||'');
  const statusLabel=row.querySelector('[data-line-accreditation]');if(statusLabel)statusLabel.textContent='Status do escopo: '+(item.scope_accreditation_status||'fora da matriz de escopo enviada');
  input.title=(normPrefix?'Referência normativa associada: '+normPrefix+'. ':'')+(item.price_label?'Valor textual na referência: '+item.price_label+'. Confirme antes de enviar a proposta.':'Preço preenchido pela tabela de referência. Confirme quantidade e condições.');
  closePopup();
 }
 function wireAutocomplete(){
  document.addEventListener('input',e=>{
   if(!descriptionInput(e.target))return;
   if(e.target.dataset.ntecPickingRef==='1')return;
   const changedRow=e.target.closest('tr');if(changedRow){delete changedRow.dataset.referenceValueId;delete changedRow.dataset.normativeReferences;delete changedRow.dataset.normativeNote;delete changedRow.dataset.scopeAccreditationStatus;const nl=changedRow.querySelector('[data-line-norm]');if(nl)nl.textContent='Selecione um item do catálogo para associar a norma aplicável.';const nn=changedRow.querySelector('[data-line-norm-note]');if(nn)nn.textContent='';const sa=changedRow.querySelector('[data-line-accreditation]');if(sa)sa.textContent='Status do escopo: não cadastrado';}
   const q=e.target.value.trim();
   if(q.length<2){closePopup();return}
   showPopup(e.target,matchingRows(q));
  });
  document.addEventListener('focusin',e=>{if(descriptionInput(e.target)&&e.target.value.trim().length>=2)showPopup(e.target,matchingRows(e.target.value))});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closePopup()});
  document.addEventListener('pointerdown',e=>{if(popup&&!popup.contains(e.target)&&e.target!==activeInput)closePopup()});
  window.addEventListener('scroll',()=>{if(activeInput)closePopup()},true);
  window.addEventListener('resize',closePopup);
 }
 function findProposalSection(){
  return [...document.querySelectorAll('h1')].find(h=>norm(h.textContent).includes('propostas comerciais'));
 }
 function setCompositionMessage(text,error){
  const el=$('ntec-composition-message');if(el){el.textContent=text||'';el.style.color=error?'#b42318':'var(--muted)'}
 }
 function ensureCompositionPanel(){
  if($('ntec-composition-panel'))return true;
  const heading=findProposalSection();if(!heading)return false;
  const section=heading.closest('section');if(!section)return false;
  const box=document.createElement('div');box.id='ntec-composition-panel';box.className='panel';box.style.cssText='margin:22px 0;padding:16px';
  box.innerHTML='<div class="titleline"><div><h2>Demonstrativo de preços por item</h2><p class="sub">Monte a composição comercial da proposta com a tabela de referência. Ao selecionar um item, a unidade e o preço de referência são preenchidos; você pode ajustar antes de salvar.</p></div><button type="button" class="btn" id="ntec-composition-refresh">Atualizar propostas</button></div>'+
   '<div class="formgrid"><div class="field"><label for="ntec-composition-proposal">Proposta para editar *</label><select id="ntec-composition-proposal"><option value="">Carregando propostas…</option></select><small class="muted small">A composição só pode ser alterada enquanto a proposta estiver em rascunho ou revisão.</small></div><div class="field"><label>Cliente / situação</label><div id="ntec-composition-context" class="ntec-composition-context">Selecione uma proposta.</div></div></div>'+
   '<div id="ntec-norm-bundle" class="panel" style="margin:16px 0;padding:14px;background:var(--surface,#fff);border:1px solid var(--line);border-radius:10px"><div class="titleline"><div><h3>Montar conjunto completo por norma</h3><p class="sub">Selecione uma NBR para carregar todos os serviços associados. Confira e edite a quantidade e o preço de cada linha, marque somente o que deseja contratar e adicione tudo à proposta de uma vez.</p></div></div>'+
   '<div class="formgrid"><div class="field"><label for="ntec-norm-bundle-standard">Norma / procedimento específico *</label><select id="ntec-norm-bundle-standard"><option value="">Carregando normas do catálogo…</option></select></div><div class="field"><label>Resumo do conjunto</label><div id="ntec-norm-bundle-summary" class="ntec-composition-context">Escolha uma norma para ver o conjunto de serviços.</div></div></div>'+
   '<div id="ntec-norm-bundle-items" class="tablewrap" style="margin-top:12px"><p class="muted small">Os itens associados à norma aparecerão aqui.</p></div>'+
   '<div class="ntec-ai-actions"><button class="btn primary" id="ntec-norm-bundle-add" type="button" disabled>Adicionar serviços marcados à proposta</button><span id="ntec-norm-bundle-message" role="status" aria-live="polite"></span></div>'+
   '<p class="footnote">Os preços começam com os valores de referência do catálogo, mas você pode alterá-los individualmente antes de adicionar. Isso altera apenas a composição desta proposta; não modifica automaticamente a tabela oficial de referência. A associação normativa depende do escopo e deve ser conferida antes do envio.</p></div>'+
   '<div id="ntec-norm-package" class="panel" style="margin:16px 0;padding:14px;background:var(--surface,#fff);border:1px solid var(--line);border-radius:10px"><div class="titleline"><div><h3>Modelos de serviço e normas aplicáveis</h3><p class="sub">Escolha o serviço. O portal associa as referências normativas e deixa os itens sugeridos marcados para você revisar antes de adicionar.</p></div></div>'+
   '<div class="formgrid"><div class="field"><label for="ntec-norm-template">Serviço / modelo de proposta</label><select id="ntec-norm-template"><option value="">Selecione o tipo de serviço…</option><option value="concreto_moldagem_axial">Concreto — moldagem + ruptura axial</option><option value="concreto_moldagem">Concreto — somente moldagem</option><option value="concreto_axial">Concreto — somente ruptura axial</option><option value="concreto_diametral">Concreto — ruptura diametral</option><option value="concreto_flexao">Concreto — tração na flexão</option><option value="argamassa_moldagem">Argamassa — moldagem de corpos de prova</option><option value="graute_moldagem_axial">Graute — moldagem + ruptura axial (confirmar método)</option></select></div><div class="field"><label>Normas / referências associadas</label><div id="ntec-norm-refs" class="ntec-composition-context">Selecione um serviço para ver as referências.</div></div></div>'+
   '<div id="ntec-norm-warning" class="ntec-ai-disclaimer" style="margin:10px 0">A norma sugerida é uma referência inicial. Confirme material, geometria do corpo de prova, idade, método de ensaio e escopo contratado antes de emitir a proposta.</div>'+
   '<div id="ntec-norm-items" class="ntec-norm-items"><p class="muted small">Os itens disponíveis serão exibidos aqui.</p></div>'+
   '<div class="ntec-ai-actions"><button class="btn primary" id="ntec-norm-add" type="button" disabled>Adicionar itens marcados à proposta</button><span id="ntec-norm-message" role="status" aria-live="polite"></span></div>'+
   '<p class="footnote">A moldagem de concreto é referenciada à ABNT NBR 5738; o ensaio de resistência à compressão axial de corpos cilíndricos, à ABNT NBR 5739; o ensaio diametral, à NBR 7222; a tração na flexão, à NBR 12142. A NBR 16886 (amostragem do concreto fresco) só é indicada quando a coleta estiver no escopo. Para argamassa/graute, verifique a geometria e a norma exigida pelo projeto antes de confirmar a composição.</p></div>'+
   '<div class="tablewrap"><table class="ntec-pg-table ntec-line-items-table"><thead><tr><th>Descrição do item / serviço</th><th>Qtd.</th><th>Unidade</th><th>Preço unitário (R$)</th><th>Desconto %</th><th>Total do item (R$)</th><th></th></tr></thead><tbody id="ntec-composition-body"><tr><td colspan="7" class="empty">Selecione uma proposta para carregar a composição.</td></tr></tbody></table></div>'+
   '<div class="ntec-ai-actions"><button class="btn" id="ntec-composition-add" type="button">+ Adicionar item</button><button class="btn primary" id="ntec-composition-save" type="button" disabled>Salvar demonstrativo e atualizar total</button><span id="ntec-composition-message" role="status" aria-live="polite"></span></div>'+
   '<div class="ntec-composition-total"><div><span>Subtotal</span><strong id="ntec-composition-subtotal">R$ 0,00</strong></div><div><span>Descontos</span><strong id="ntec-composition-discounts">R$ 0,00</strong></div><div class="grand"><span>Total da proposta</span><strong id="ntec-composition-total">R$ 0,00</strong></div></div>'+
   '<p class="footnote">Os itens são salvos em Supabase ligados à proposta. Se você remover um item e salvar, ele também será removido da composição daquela proposta. O valor total da proposta é recalculado. Itens de propostas aprovadas/enviadas ficam somente para consulta.</p>';
  const style=document.createElement('style');style.id='ntec-composition-style';
  style.textContent='#ntec-composition-panel{border:1px solid var(--line);border-radius:12px}#ntec-composition-panel .ntec-composition-context{padding:10px;border:1px solid var(--line);border-radius:8px;min-height:20px;font-size:13px;line-height:1.5}#ntec-composition-panel .ntec-composition-total{margin:12px 0 0 auto;max-width:360px;border:1px solid var(--line);border-radius:9px;padding:12px 15px;display:grid;gap:9px}#ntec-composition-panel .ntec-composition-total>div{display:flex;justify-content:space-between;gap:18px}#ntec-composition-panel .ntec-composition-total span{color:var(--muted)}#ntec-composition-panel .ntec-composition-total .grand{border-top:1px solid var(--line);padding-top:10px;font-size:16px}#ntec-composition-panel .ntec-composition-total .grand strong{font-size:20px}#ntec-composition-panel .ntec-line-items-table{min-width:900px}#ntec-composition-panel .ntec-line-items-table input{width:100%;min-width:68px;box-sizing:border-box;padding:8px;border:1px solid var(--line);border-radius:6px;font:inherit}#ntec-composition-panel .ntec-line-description{min-width:220px}#ntec-composition-panel .ntec-line-norm,#ntec-composition-panel .ntec-line-norm-note{display:block;font-size:11px;line-height:1.35;white-space:normal;overflow-wrap:anywhere;margin-top:4px;color:var(--muted)}#ntec-composition-panel .ntec-line-norm{color:#1d4f91;font-weight:600}#ntec-composition-panel .ntec-line-norm-note{font-weight:400}#ntec-composition-panel .ntec-line-accreditation{display:inline-block;margin-top:5px;padding:3px 6px;border-radius:5px;background:#f1f5f9;color:#334155;font-weight:700}#ntec-composition-panel .ntec-line-unit{min-width:82px}@media(max-width:700px){#ntec-composition-panel .ntec-composition-total{max-width:none}}';
  document.head.appendChild(style);section.appendChild(box);
  $('ntec-composition-proposal').addEventListener('change',e=>{
   const next=e.target.value;
   if(compositionDirty&&!confirm('Existem alterações não salvas neste demonstrativo. Descartar e carregar outra proposta?')){e.target.value=activeCompositionProposal?.id||'';return}
   loadCompositionList(true,next);
  });
  $('ntec-composition-refresh').addEventListener('click',()=>loadCompositionList(true,activeCompositionProposal?.id||null));
  $('ntec-composition-add').addEventListener('click',()=>addCompositionLine({}));
  $('ntec-composition-save').addEventListener('click',saveComposition);
  $('ntec-norm-template').addEventListener('change',renderNormTemplate);
  $('ntec-norm-add').addEventListener('click',addSelectedNormItems);
  $('ntec-norm-bundle-standard').addEventListener('change',renderNormBundleItems);
  $('ntec-norm-bundle-add').addEventListener('click',addNormBundleItems);
  $('ntec-norm-bundle-items').addEventListener('input',updateNormBundleSummary);
  $('ntec-norm-bundle-items').addEventListener('change',updateNormBundleSummary);
  return true;
 }
 function canonicalNormToken(raw){
  let token=String(raw||'').trim().toUpperCase().replace(/\s+/g,' ');
  token=token.replace(/^NBR\b/,'ABNT NBR');
  token=token.replace(/^ABNT NBR (\d+(?:-\d+)?)\/(\d{4})$/,'ABNT NBR $1:$2');
  token=token.replace(/^DNER\s*[-–]?\s*ME\s+(\d{3})\s*[:\/]\s*(\d{2,4})$/,'DNER-ME $1:$2');
  token=token.replace(/^DNIT\s+(\d+)\s*\/\s*(\d{4})\s*[-–]?\s*ME$/,'DNIT $1/$2-ME');
  token=token.replace(/^DNER-PRO\s+(\d+)\s*\/\s*(\d{4})$/,'DNER-PRO $1/$2');
  return token;
 }
 function extractNormTokens(text){
  const found=String(text||'').match(/(?:ABNT\s+)?NBR\s+\d+(?:-\d+)?(?:[:\/]\d{4})?|DNIT\s+\d+\s*\/\s*\d{4}(?:\s*[-–]?\s*ME)?|DNER\s*[-–]?\s*ME\s+\d{3}\s*[:\/]\s*\d{2,4}|DNER-PRO\s+\d+\s*\/\s*\d{4}/gi)||[];
  return [...new Set(found.map(canonicalNormToken))];
 }
 function renderNormBundleOptions(){
  const select=$('ntec-norm-bundle-standard');if(!select)return;
  const counts=new Map();
  rows.filter(r=>r.is_active).forEach(r=>extractNormTokens(r.normative_references).forEach(token=>counts.set(token,(counts.get(token)||0)+1)));
  const options=[...counts.entries()].sort((a,b)=>a[0].localeCompare(b[0],'pt-BR',{numeric:true}));
  const previous=select.value;
  select.innerHTML='<option value="">Selecione uma norma…</option>'+options.map(([token,count])=>'<option value="'+esc(token)+'">'+esc(token)+' · '+count+' serviço(s) vinculado(s)'+'</option>').join('');
  if(options.some(([token])=>token===previous))select.value=previous;
  else select.value='';
  renderNormBundleItems();
 }
 function renderNormBundleItems(){
  const select=$('ntec-norm-bundle-standard'),box=$('ntec-norm-bundle-items'),button=$('ntec-norm-bundle-add');
  if(!select||!box||!button)return;
  const standard=select.value;
  if(!standard){box.innerHTML='<p class="muted small">Selecione uma norma ou procedimento técnico para carregar o conjunto completo de serviços do catálogo.</p>';box._ntecBundleRows=[];updateNormBundleSummary();return}
  const matched=rows.filter(r=>r.is_active&&extractNormTokens(r.normative_references).includes(standard));
  box._ntecBundleRows=matched;
  if(!matched.length){box.innerHTML='<p class="muted small">Não há serviços ativos vinculados a esta norma. Confira o cadastro de referências normativas.</p>';updateNormBundleSummary();return}
  box.innerHTML='<table style="width:100%;min-width:900px;border-collapse:collapse"><thead><tr><th style="padding:8px;text-align:left">Incluir</th><th style="padding:8px;text-align:left">Código / serviço</th><th style="padding:8px;text-align:left">Status de acreditação no escopo</th><th style="padding:8px;text-align:left">Unidade</th><th style="padding:8px;text-align:right">Preço referência</th><th style="padding:8px;text-align:right">Qtd.</th><th style="padding:8px;text-align:right">Preço proposto (R$)</th><th style="padding:8px;text-align:right">Total (R$)</th></tr></thead><tbody>'+
  matched.map((r,i)=>'<tr data-ntec-bundle-line="'+i+'" style="border-top:1px solid var(--line)"><td style="padding:8px"><input type="checkbox" data-bundle-check checked aria-label="Incluir '+esc(r.item_name)+'"/></td><td style="padding:8px;min-width:240px"><strong>'+esc((r.item_code?r.item_code+' · ':'')+r.item_name)+'</strong><small style="display:block;margin-top:4px;color:var(--muted);font-size:11px;line-height:1.35">Normas: '+esc(r.normative_references||standard)+'</small>'+(r.normative_note?'<small style="display:block;margin-top:3px;color:var(--muted);font-size:11px">'+esc(r.normative_note)+'</small>':'')+'</td><td style="padding:8px;min-width:150px"><span style="display:inline-block;padding:4px 7px;border-radius:6px;font-size:11px;font-weight:700;background:'+(r.scope_accreditation_status==='Acreditado'?'#dcfce7':r.scope_accreditation_status==='Não acreditado'?'#fef3c7':'#e2e8f0')+';color:'+(r.scope_accreditation_status==='Acreditado'?'#166534':r.scope_accreditation_status==='Não acreditado'?'#92400e':'#334155')+'">'+esc(r.scope_accreditation_status||'Fora da matriz de escopo enviada')+'</span></td><td style="padding:8px;white-space:nowrap">'+esc(r.unit||'serviço')+'</td><td style="padding:8px;text-align:right;white-space:nowrap">'+(r.price_label?esc(r.price_label)+' · ':'')+money(r.reference_price||0)+'</td><td style="padding:8px"><input data-bundle-qty type="number" min="0.001" step="0.001" value="1" style="width:90px;box-sizing:border-box;padding:7px;border:1px solid var(--line);border-radius:6px" aria-label="Quantidade para '+esc(r.item_name)+'"/></td><td style="padding:8px"><input data-bundle-price type="number" min="0" step="0.01" value="'+esc(Number(r.reference_price||0).toFixed(2))+'" style="width:130px;box-sizing:border-box;padding:7px;border:1px solid var(--line);border-radius:6px" aria-label="Preço proposto para '+esc(r.item_name)+'"/></td><td data-bundle-total style="padding:8px;text-align:right;white-space:nowrap">'+money(r.reference_price||0)+'</td></tr>').join('')+
  '</tbody></table>';
  updateNormBundleSummary();
 }
 function updateNormBundleSummary(){
  const box=$('ntec-norm-bundle-items'),summary=$('ntec-norm-bundle-summary'),button=$('ntec-norm-bundle-add'),status=$('ntec-norm-bundle-message');
  if(!box||!summary||!button)return;
  let count=0,total=0,invalid=false;
  box.querySelectorAll('tr[data-ntec-bundle-line]').forEach(tr=>{
   const check=tr.querySelector('[data-bundle-check]'),qty=Number(tr.querySelector('[data-bundle-qty]')?.value),price=Number(tr.querySelector('[data-bundle-price]')?.value);
   const good=Number.isFinite(qty)&&qty>0&&Number.isFinite(price)&&price>=0;
   if(check?.checked){count++;if(good)total+=qty*price;else invalid=true}
   const totalCell=tr.querySelector('[data-bundle-total]');
   if(totalCell)totalCell.textContent=good?money(qty*price):'—';
   if(check)check.disabled=!compositionEditable(activeCompositionProposal)||compositionBusy;
  });
  const standard=$('ntec-norm-bundle-standard')?.value||'';
  summary.innerHTML=standard?'<strong>'+esc(standard)+'</strong><br>'+count+' serviço(s) marcado(s) · Total estimado: <strong>'+money(total)+'</strong>'+(invalid?'<br><span style="color:#b42318">Confira quantidade e preço dos itens marcados.</span>':''):'Escolha uma norma para ver o conjunto de serviços.';
  button.disabled=!compositionEditable(activeCompositionProposal)||compositionBusy||!count||invalid;
  if(status&&status.dataset.resetAfterChange==='1'){status.textContent='';delete status.dataset.resetAfterChange}
 }
 function addNormBundleItems(){
  const standard=$('ntec-norm-bundle-standard')?.value,box=$('ntec-norm-bundle-items'),status=$('ntec-norm-bundle-message');
  if(!standard){if(status)status.textContent='Selecione uma norma ou procedimento técnico primeiro.';return}
  if(!compositionEditable(activeCompositionProposal)){if(status)status.textContent='Selecione uma proposta em rascunho ou revisão antes de adicionar os serviços.';return}
  const bundleRows=box?box._ntecBundleRows||[]:[];
  const existing=new Set(readCompositionItems().map(x=>x.reference_value_id).filter(Boolean));
  let added=0,skipped=0;
  for(const tr of box.querySelectorAll('tr[data-ntec-bundle-line]')){
   const check=tr.querySelector('[data-bundle-check]');if(!check?.checked)continue;
   const ref=bundleRows[Number(tr.dataset.ntecBundleLine)];if(!ref)continue;
   if(existing.has(String(ref.id))){skipped++;continue}
   const qty=Number(tr.querySelector('[data-bundle-qty]')?.value),price=Number(tr.querySelector('[data-bundle-price]')?.value);
   if(!Number.isFinite(qty)||qty<=0||!Number.isFinite(price)||price<0){if(status)status.textContent='Revise quantidade e preço de todos os serviços marcados.';return}
   const description=standard+' — '+ref.item_name;
   addCompositionLine({description,quantity:qty,unit:ref.unit||'serviço',unit_price:price,discount_percent:0,reference_value_id:ref.id,normative_references:ref.normative_references||standard,normative_note:ref.normative_note||('Adicionado pelo conjunto da norma '+standard+'. Confirme o escopo antes de enviar.'),scope_accreditation_status:ref.scope_accreditation_status||'Fora da matriz de escopo enviada'});
   existing.add(String(ref.id));added++;
  }
  compositionDirty=compositionDirty||added>0;updateCompositionTotals();updateNormBundleSummary();
  if(status)status.textContent=added?(added+' serviço(s) de '+standard+' adicionado(s) à proposta. Confira a composição e salve quando estiver pronta.'+(skipped?' '+skipped+' repetido(s) ignorado(s).':'')):'Nenhum serviço novo foi adicionado. Marque um item que ainda não esteja na proposta.';
 }
 const normTemplates={
  concreto_moldagem_axial:{
   label:'Concreto — moldagem + ruptura axial',
   norms:[
    {code:'ABNT NBR 5738:2015 (Versão Corrigida 2016)',text:'Moldagem e cura de corpos de prova cilíndricos ou prismáticos de concreto.'},
    {code:'ABNT NBR 5739:2018',text:'Ensaio de compressão de corpos de prova cilíndricos de concreto.'},
    {code:'ABNT NBR 16886:2020',text:'Amostragem de concreto fresco — referência somente se a coleta estiver contratada.'},
    {code:'ABNT NBR 12655:2015 + Emenda 1:2022',text:'Referência geral para preparo, controle, recebimento e aceitação do concreto; confirmar edição aplicável ao contrato.'}
   ],
   rules:[{category:'Ensaios de Concreto',match:'moldagem de corpos de provas (concreto)',checked:true,normCodes:['ABNT NBR 5738:2015 (VC 2016)']},{category:'Ensaios de Concreto',match:'ruptura axial de corpos de provas cilindricos',checked:true,normCodes:['ABNT NBR 5739:2018']}],
   warning:'O catálogo atual marca a moldagem como “Incluso” e preço R$ 0,00. Antes de salvar, decida se o serviço será incluído sem cobrança ou se a tabela de referência deve receber um preço. O item de amostragem não será adicionado automaticamente porque não há item separado identificado para coleta no catálogo.'
  },
  concreto_moldagem:{
   label:'Concreto — somente moldagem',
   norms:[
    {code:'ABNT NBR 5738:2015 (Versão Corrigida 2016)',text:'Moldagem e cura de corpos de prova de concreto.'},
    {code:'ABNT NBR 16886:2020 (condicional)',text:'Amostragem do concreto fresco, apenas quando a coleta fizer parte do escopo.'}
   ],
   rules:[{category:'Ensaios de Concreto',match:'moldagem de corpos de provas (concreto)',checked:true,normCodes:['ABNT NBR 5738:2015 (VC 2016)']}],
   warning:'A tabela atual marca moldagem de concreto como “Incluso” (R$ 0,00). Confira se deve permanecer incluída na proposta ou se será precificada. A coleta/amostragem é uma atividade distinta.'
  },
  concreto_axial:{
   label:'Concreto — ruptura axial',
   norms:[
    {code:'ABNT NBR 5739:2018',text:'Ensaio de compressão de corpos de prova cilíndricos de concreto.'},
    {code:'ABNT NBR 5738:2015 (Versão Corrigida 2016)',text:'Referência associada à moldagem/cura e rastreabilidade dos corpos de prova.'}
   ],
   rules:[{category:'Ensaios de Concreto',match:'ruptura axial de corpos de provas cilindricos',checked:true,normCodes:['ABNT NBR 5739:2018']}],
   warning:'Confirme as dimensões (por exemplo, 10×20 cm ou 15×30 cm), idade de ruptura, identificação e rastreabilidade dos corpos de prova. A moldagem pode ser um item separado ou já estar incluída no contrato.'
  },
  concreto_diametral:{
   label:'Concreto — ruptura diametral',
   norms:[
    {code:'ABNT NBR 7222:2011',text:'Determinação da resistência à tração por compressão diametral de corpos de prova cilíndricos.'},
    {code:'ABNT NBR 5738:2015 (Versão Corrigida 2016)',text:'Moldagem/cura dos corpos de prova, quando fizer parte do procedimento contratado.'}
   ],
   rules:[{category:'Ensaios de Concreto',match:'ruptura diametral de corpos de provas cilindricos',checked:true,normCodes:['ABNT NBR 7222:2011']}],
   warning:'A ruptura diametral não é o mesmo serviço que a ruptura axial por compressão. Confirme que a solicitação do cliente é realmente tração por compressão diametral.'
  },
  concreto_flexao:{
   label:'Concreto — tração na flexão',
   norms:[
    {code:'ABNT NBR 12142:2010',text:'Determinação da resistência à tração na flexão de corpos de prova prismáticos de concreto.'},
    {code:'ABNT NBR 5738:2015 (Versão Corrigida 2016)',text:'Moldagem/cura dos corpos de prova prismáticos, conforme escopo.'}
   ],
   rules:[{category:'Ensaios de Concreto',match:'ruptura tração na flexão',checked:true,normCodes:['ABNT NBR 12142:2010']}],
   warning:'Confirme a geometria do prisma e os pontos de carregamento previstos pelo método normativo e pelo laboratório.'
  },
  argamassa_moldagem:{
   label:'Argamassa — moldagem de corpos de prova',
   norms:[
    {code:'ABNT NBR 13279:2005',text:'Resistência à tração na flexão e à compressão de argamassa endurecida em corpos de prova prismáticos.'}
   ],
   rules:[{category:'Ensaios de Argamassa',match:'moldagem de corpos de provas (argamassa)',checked:true,normCodes:['Referência a confirmar: ABNT NBR 13279:2005']}],
   warning:'A NBR 13279 trata de ensaios em corpos de prova prismáticos, tipicamente 4×4×16 cm. O item de ruptura axial cilíndrica 5×10 cm existente no catálogo não deve ser associado automaticamente a essa norma sem confirmação do método e da especificação do cliente.'
  },
  graute_moldagem_axial:{
   label:'Graute — moldagem + ruptura axial',
   norms:[
    {code:'Referência técnica a confirmar pelo projeto / especificação do graute',text:'O método de moldagem, cura e resistência deve ser definido pelo tipo de graute, geometria do corpo de prova e norma contratual.'},
    {code:'ABNT NBR 5738 / NBR 5739 — somente se explicitamente aplicáveis ao método contratado',text:'Não assumir automaticamente que o procedimento de concreto é aplicável ao graute sem validar a especificação técnica.'}
   ],
   rules:[{category:'Ensaios de Graute',match:'moldagem de corpos de provas (graute)',checked:true,normCodes:['Confirmar norma e geometria no projeto/especificação']},{category:'Ensaios de Graute',match:'ruptura axial de corpos de provas cilindricos',checked:true,normCodes:['Confirmar norma e geometria no projeto/especificação']}],
   warning:'Para graute, valide no projeto/especificação o corpo de prova, método de moldagem/cura, idade e ensaio de resistência. O portal deixará esses itens como sugestões para revisão, não como definição normativa automática.'
  }
 };
 function renderNormTemplate(){
  const key=$('ntec-norm-template')?.value,template=normTemplates[key];
  const refs=$('ntec-norm-refs'),items=$('ntec-norm-items'),add=$('ntec-norm-add'),warning=$('ntec-norm-warning');
  if(!refs||!items||!add||!warning)return;
  if(!template){refs.textContent='Selecione um serviço para ver as referências.';items.innerHTML='<p class="muted small">Os itens disponíveis serão exibidos aqui.</p>';warning.textContent='A norma sugerida é uma referência inicial. Confirme material, geometria do corpo de prova, idade, método de ensaio e escopo contratado antes de emitir a proposta.';add.disabled=true;return}
  refs.innerHTML='<ul style="margin:4px 0;padding-left:18px">'+template.norms.map(n=>'<li style="margin:5px 0"><strong>'+esc(n.code)+'</strong><div class="muted small">'+esc(n.text)+'</div></li>').join('')+'</ul>';
  warning.textContent=template.warning;
  const found=template.rules.map((rule,index)=>{
   const row=rows.find(r=>norm(r.category)===norm(rule.category)&&norm(r.item_name).includes(norm(rule.match)));
   return row?{rule,index,row}:null;
  }).filter(Boolean);
  if(!found.length){items.innerHTML='<p class="muted small">Não localizei os itens correspondentes na tabela de referência. Você ainda pode usar a lista de normas, mas deverá cadastrar/selecionar o serviço manualmente.</p>';add.disabled=true;return}
  items._ntecNormRows=[];found.forEach(({index,row})=>{items._ntecNormRows[index]=row});
  items.innerHTML=found.map(({rule,index,row})=>{
   const value=String(row.price_label||'').trim()||money(row.reference_price);
   return '<label style="display:flex;align-items:flex-start;gap:9px;padding:9px 0;border-bottom:1px solid var(--line);cursor:pointer"><input type="checkbox" data-ntec-norm-row="'+index+'" '+(rule.checked?'checked':'')+' style="margin-top:4px"/><span><strong>'+esc(row.item_name)+'</strong><br/><span class="muted small">'+esc(row.category)+' · '+esc(row.unit)+' · Referência: '+esc(value)+'</span></span></label>';
  }).join('')+'<p class="muted small">Os valores são os que estão cadastrados agora na tabela de referência. Confira-os, sobretudo quando aparecer “Incluso”/R$ 0,00.</p>';
  add.disabled=false;
 }
 function addSelectedNormItems(){
  const key=$('ntec-norm-template')?.value,template=normTemplates[key];
  const status=$('ntec-norm-message');
  if(!template){if(status)status.textContent='Selecione primeiro um modelo.';return}
  if(!compositionEditable(activeCompositionProposal)){if(status)status.textContent='Selecione uma proposta em rascunho ou revisão.';return}
  const items=$('ntec-norm-items'),refRows=items?items._ntecNormRows||[]:[];
  const normText=template.norms.map(n=>n.code).join('; ');
  const existing=new Set(readCompositionItems().map(x=>x.reference_value_id).filter(Boolean));
  let added=0,skipped=0;
  for(const checkbox of items.querySelectorAll('input[data-ntec-norm-row]:checked')){
   const ref=refRows[Number(checkbox.dataset.ntecNormRow)];if(!ref)continue;
   if(existing.has(String(ref.id))){skipped++;continue}
   const priceLabel=String(ref.price_label||'').trim();
   const rule=template.rules.find(rule=>norm(rule.category)===norm(ref.category)&&norm(ref.item_name).includes(norm(rule.match)));
   const normList=Array.isArray(rule?.normCodes)?rule.normCodes:(ref.normative_references?[ref.normative_references]:[normText]);
   const lineNormText=normList.join('; ');
   const description=lineNormText+' — '+ref.item_name;
   addCompositionLine({description,quantity:1,unit:(priceLabel.toLowerCase()==='incluso'?'serviço':ref.unit||'serviço'),unit_price:Number(ref.reference_price||0),discount_percent:0,reference_value_id:ref.id,normative_references:lineNormText,normative_note:template.warning,scope_accreditation_status:ref.scope_accreditation_status||'Fora da matriz de escopo enviada'});
   existing.add(String(ref.id));added++;
  }
  compositionDirty=compositionDirty||added>0;updateCompositionTotals();
  if(status)status.textContent=added?(added+' item(ns) adicionado(s) à proposta. Revise quantidades, preços e normas antes de salvar.'+(skipped?' '+skipped+' item(ns) repetido(s) ignorado(s).':'')):'Nenhum item novo adicionado. Marque pelo menos um item ou confira se já está na composição.';
 }
 function compositionEditable(p){return Boolean(p&&['rascunho','em_revisao'].includes(p.status))}
 function fmtQty(v){return Number(v||0).toLocaleString('pt-BR',{maximumFractionDigits:3})}
 function compositionLineHtml(item){
  const qty=item.quantity==null?1:item.quantity,discount=item.discount_percent==null?0:item.discount_percent,unitPrice=item.unit_price==null?'':item.unit_price;
  const normative=String(item.normative_references||'').trim(),normNote=String(item.normative_note||'').trim(),accreditation=String(item.scope_accreditation_status||'').trim();
  return '<tr data-composition-line="1"><td><div class="ntec-composition-description"><input class="ntec-line-description" data-line-field="description" aria-label="Descrição do item" maxlength="500" value="'+esc(item.description||'')+'" placeholder="Digite para buscar na referência" required/><small class="ntec-line-norm" data-line-norm>'+(normative?'NORMAS/REFERÊNCIAS: '+esc(normative):'Selecione um item do catálogo para associar a norma aplicável.')+'</small><small class="ntec-line-norm-note" data-line-norm-note>'+esc(normNote)+'</small><small class="ntec-line-accreditation" data-line-accreditation>Status do escopo: '+esc(accreditation||'fora da matriz de escopo enviada')+'</small></div></td>'+
   '<td><input data-line-field="quantity" aria-label="Quantidade" type="number" min="0.001" step="0.001" value="'+esc(qty)+'" required/></td>'+
   '<td><input class="ntec-line-unit" data-line-field="unit" aria-label="Unidade" maxlength="40" value="'+esc(item.unit||'serviço')+'" required/></td>'+
   '<td><input data-line-field="unit_price" aria-label="Preço unitário" type="number" min="0" step="0.01" value="'+esc(unitPrice)+'" required/></td>'+
   '<td><input data-line-field="discount_percent" aria-label="Desconto percentual" type="number" min="0" max="100" step="0.01" value="'+esc(discount)+'" required/></td>'+
   '<td class="ntec-line-total" data-composition-line-total>R$ 0,00</td><td><button type="button" class="ntec-line-remove" aria-label="Remover item">×</button></td></tr>';
 }
 function addCompositionLine(item){
  const body=$('ntec-composition-body');if(!body||!compositionEditable(activeCompositionProposal)||compositionBusy)return;
  const empty=body.querySelector('[data-composition-empty]');if(empty)body.innerHTML='';
  body.insertAdjacentHTML('beforeend',compositionLineHtml(item||{}));
  const row=body.lastElementChild;
  if(item?.id)row.dataset.lineId=item.id;
  if(item?.reference_value_id)row.dataset.referenceValueId=item.reference_value_id;
  if(item?.normative_references)row.dataset.normativeReferences=item.normative_references;
  if(item?.normative_note)row.dataset.normativeNote=item.normative_note;
  if(item?.scope_accreditation_status)row.dataset.scopeAccreditationStatus=item.scope_accreditation_status;
  row.querySelectorAll('[data-line-field]').forEach(el=>el.addEventListener('input',()=>{compositionDirty=true;updateCompositionTotals()}));
  row.querySelector('.ntec-line-remove').addEventListener('click',()=>{row.remove();compositionDirty=true;updateCompositionTotals()});
  updateCompositionTotals();updateCompositionControls();
 }
 function readCompositionItems(){
  return [...document.querySelectorAll('#ntec-composition-body [data-composition-line]')].map(row=>{
   const v={};row.querySelectorAll('[data-line-field]').forEach(el=>v[el.dataset.lineField]=el.value);
   return {id:row.dataset.lineId||undefined,reference_value_id:row.dataset.referenceValueId||null,normative_references:String(row.dataset.normativeReferences||''),normative_note:String(row.dataset.normativeNote||''),scope_accreditation_status:String(row.dataset.scopeAccreditationStatus||''),description:String(v.description||'').trim(),quantity:Number(v.quantity),unit:String(v.unit||'').trim(),unit_price:Number(v.unit_price),discount_percent:Number(v.discount_percent||0)};
  });
 }
 function updateCompositionTotals(){
  const body=$('ntec-composition-body');if(!body)return;
  let subtotal=0,discount=0,total=0;
  [...body.querySelectorAll('[data-composition-line]')].forEach(row=>{
   const v={};row.querySelectorAll('[data-line-field]').forEach(el=>v[el.dataset.lineField]=el.value);
   const gross=Math.round(Number(v.quantity||0)*Number(v.unit_price||0)*100)/100;
   const disc=Math.round(gross*Number(v.discount_percent||0))/100;
   const line=Math.round(gross*(1-Number(v.discount_percent||0)/100)*100)/100;
   subtotal+=gross;discount+=disc;total+=line;
   const cell=row.querySelector('[data-composition-line-total]');if(cell)cell.textContent=money(line);
  });
  $('ntec-composition-subtotal').textContent=money(Math.round(subtotal*100)/100);
  $('ntec-composition-discounts').textContent=money(Math.round(discount*100)/100);
  $('ntec-composition-total').textContent=money(Math.round(total*100)/100);
  updateCompositionControls();
 }
 function updateCompositionControls(){
  const editable=compositionEditable(activeCompositionProposal);
  const totalRows=[...document.querySelectorAll('#ntec-composition-body [data-composition-line]')].length;
  const save=$('ntec-composition-save'),add=$('ntec-composition-add');
  if(save)save.disabled=!editable||compositionBusy||!compositionDirty||!totalRows;
  if(add)add.disabled=!editable||compositionBusy;
  document.querySelectorAll('#ntec-composition-body [data-line-field],#ntec-composition-body .ntec-line-remove').forEach(el=>{el.disabled=!editable||compositionBusy});
 }
 function renderComposition(){
  const body=$('ntec-composition-body');if(!body)return;
  const p=activeCompositionProposal,editable=compositionEditable(p);
  $('ntec-composition-context').innerHTML=p?'<strong>'+esc(p.clients?.company_name||'Cliente não informado')+'</strong><br>'+esc(p.proposal_number||'Proposta sem número')+' · '+esc(p.status)+' · Total salvo: <strong>'+money(p.amount||0)+'</strong>':'Selecione uma proposta.';
  if(!p){body.innerHTML='<tr data-composition-empty="1"><td colspan="7" class="empty">Selecione uma proposta para carregar a composição.</td></tr>'}
  else if(!p.items?.length){body.innerHTML='<tr data-composition-empty="1"><td colspan="7" class="empty">Nenhum item cadastrado nesta proposta. Clique em “Adicionar item”.</td></tr>'}
  else{body.innerHTML='';p.items.forEach(item=>addCompositionLine(item))}
  compositionDirty=false;updateCompositionTotals();updateCompositionControls();
  setCompositionMessage(p?(editable?'Rascunho carregado. Adicione ou ajuste os itens e salve.':'Proposta em modo de consulta. A composição está bloqueada.'):'Nenhuma proposta disponível.',false);
 }
 async function loadCompositionList(force=false,desiredId=null){
  if(!ensureCompositionPanel())return;
  if(!api()?.loadProposalPricing){setCompositionMessage('A lista está aguardando a conexão administrativa. Entre como administrador e atualize.',true);return}
  setCompositionMessage('Carregando propostas e composições…');
  try{
   const previous=desiredId||activeCompositionProposal?.id||$('ntec-composition-proposal')?.value||'';
   compositionProposals=await api().loadProposalPricing();
   if(api()?.loadProposalReferenceValues){window.NTEC_PRICE_REFERENCE_CACHE=await api().loadProposalReferenceValues();rows=window.NTEC_PRICE_REFERENCE_CACHE;renderOptions(selected?.id);renderNormBundleOptions()}
   const select=$('ntec-composition-proposal');
   select.innerHTML=compositionProposals.length?compositionProposals.map(p=>'<option value="'+esc(p.id)+'" '+(compositionEditable(p)?'':'disabled')+'>'+esc(p.proposal_number||'Proposta')+' · '+esc(p.clients?.company_name||'Cliente')+' · '+esc(p.status)+'</option>').join(''):'<option value="">Nenhuma proposta cadastrada</option>';
   let choice=compositionProposals.find(p=>String(p.id)===String(previous))||compositionProposals.find(compositionEditable)||compositionProposals[0]||null;
   activeCompositionProposal=choice;select.value=choice?.id||'';
   renderComposition();
   updateNormBundleSummary();
  }catch(e){setCompositionMessage('Não foi possível carregar as propostas: '+(e?.message||'erro desconhecido'),true)}
 }
 async function saveComposition(){
  if(compositionBusy)return;
  if(!activeCompositionProposal||!compositionEditable(activeCompositionProposal)){setCompositionMessage('Selecione uma proposta em rascunho ou revisão.',true);return}
  const items=readCompositionItems();
  if(!items.length){setCompositionMessage('Adicione ao menos um item antes de salvar.',true);return}
  for(let i=0;i<items.length;i++){
   const item=items[i];
   if(!item.description||!item.unit||!Number.isFinite(item.quantity)||item.quantity<=0||!Number.isFinite(item.unit_price)||item.unit_price<0||!Number.isFinite(item.discount_percent)||item.discount_percent<0||item.discount_percent>100){setCompositionMessage('Confira descrição, quantidade, unidade, preço e desconto no item '+(i+1)+'.',true);return}
  }
  if(!confirm('Salvar a composição de preços e atualizar o total da proposta '+(activeCompositionProposal.proposal_number||'selecionada')+'?'))return;
  compositionBusy=true;updateCompositionControls();setCompositionMessage('Salvando demonstrativo…');
  try{
   const saved=await api().saveProposalPricing({proposal_id:activeCompositionProposal.id,items});
   await loadCompositionList(true,activeCompositionProposal.id);
   setCompositionMessage('Demonstrativo salvo. Total atualizado para '+money(saved.total)+'.');
  }catch(e){setCompositionMessage('Não foi possível salvar o demonstrativo: '+(e?.message||'erro'),true)}
  finally{compositionBusy=false;updateCompositionControls()}
 }

 function init(){
  if(initialized)return;
  if(!ensureAssistant()||!ensureCompositionPanel()){const observer=new MutationObserver(()=>{if(ensureAssistant()&&ensureCompositionPanel()){observer.disconnect();bind()}});observer.observe(document.body,{childList:true,subtree:true});return}
  bind();
 }
 function bind(){
  if(initialized)return;initialized=true;wireAutocomplete();
  const ready=()=>api()?.loadProposalReferenceValues&&api()?.loadProposalPriceReviews&&api()?.loadProposalPricing&&api()?.saveProposalPricing;
  const retry=setInterval(()=>{if(ready()){clearInterval(retry);loadRefs();loadCompositionList(true)}},400);
  if(ready()){clearInterval(retry);loadRefs();loadCompositionList(true)}
  document.querySelectorAll('#nav button').forEach(b=>b.addEventListener('click',()=>{if($('ntec-ref-price-panel'))loadRefs();if(findProposalSection())loadCompositionList(true)}));
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
</script>'''
closing = re.search(r'</body>\s*</html>\s*$', s, flags=re.I)
if not closing:
    raise SystemExit("assistente de preços: final do documento não encontrado")
s = s[:closing.start()] + runtime + "\n" + s[closing.start():]
for token in ["loadProposalPriceReviews","saveProposalPriceReview","applyProposalPriceReview","ntec-price-ai-panel","ntec-price-autocomplete","proposal_price_reviews"]:
    if token not in s:
        raise SystemExit("Validação do assistente de preços falhou: " + token)
path.write_text(s, encoding="utf-8")
print("Applied NTEC price assistant and reference autocomplete to", path)
