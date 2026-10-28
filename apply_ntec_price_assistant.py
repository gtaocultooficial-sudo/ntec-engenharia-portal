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
 if(error)throw new Error(error.message||'Falha ao chamar a IA de precificação.');
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
  st.textContent='#ntec-price-ai-panel{border:1px solid var(--line);border-radius:12px}#ntec-price-ai-panel .ntec-ai-tag{font-size:11px;font-weight:700;padding:5px 9px;border-radius:999px;background:#f1f5f9;color:#334155;white-space:nowrap}.ntec-ai-disclaimer{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.5;margin:8px 0 14px}.ntec-ai-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0}.ntec-ai-actions [role=status]{font-size:12px}.ntec-ai-result{border:1px solid var(--line);border-radius:10px;padding:12px;margin-top:12px;line-height:1.55}.ntec-ai-result .metrics{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:8px;margin:10px 0}.ntec-ai-result .metric{border:1px solid var(--line);border-radius:8px;padding:10px}.ntec-ai-result .metric span{display:block;font-size:11px;color:var(--muted)}.ntec-ai-result .metric strong{display:block;font-size:15px;margin-top:3px}.ntec-ai-status{font-weight:700;display:inline-block;padding:5px 9px;border-radius:999px;background:#fef3c7;color:#92400e}.ntec-ai-status.good{background:#dcfce7;color:#166534}.ntec-ai-status.bad{background:#fee2e2;color:#991b1b}.ntec-ai-history{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.ntec-ai-history h4{margin:0 0 8px}.ntec-ai-history table{width:100%;border-collapse:collapse;font-size:12px}.ntec-ai-history th,.ntec-ai-history td{text-align:left;padding:7px;border-bottom:1px solid var(--line);vertical-align:top}.ntec-ai-history th{color:var(--muted);font-weight:600}.ntec-ai-history .muted{color:var(--muted)}.ntec-price-autocomplete{position:fixed;z-index:100000;max-height:320px;overflow:auto;background:#fff;border:1px solid #cbd5e1;border-radius:9px;box-shadow:0 12px 35px #0f172a25;color:#0f172a}.ntec-price-autocomplete button{display:flex;flex-direction:column;gap:3px;width:100%;text-align:left;border:0;border-bottom:1px solid #e2e8f0;background:#fff;padding:10px 12px;cursor:pointer;color:inherit}.ntec-price-autocomplete button:hover,.ntec-price-autocomplete button:focus{background:#f1f5f9}.ntec-price-autocomplete strong{font-size:13px}.ntec-price-autocomplete small{font-size:11px;color:#64748b}.ntec-price-autocomplete b{font-size:12px}@media(max-width:720px){.ntec-ai-result .metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.ntec-ai-actions>*{max-width:100%}}';
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
  select.innerHTML='<option value="">Selecione um item cadastrado…</option>'+active.map(r=>'<option value="'+esc(r.id)+'">'+esc((r.item_code?r.item_code+' · ':'')+r.item_name+' — '+r.category+' ('+r.unit+')'+(r.price_label?' ['+r.price_label+']':''))+'</option>').join('');
  if(keepId&&active.some(r=>String(r.id)===String(keepId)))select.value=keepId;
 }
 async function loadRefs(){
  if(!api()?.loadProposalReferenceValues)return;
  try{rows=await api().loadProposalReferenceValues();window.NTEC_PRICE_REFERENCE_CACHE=rows;renderOptions(selected?.id);await selectItem($('ntec-ai-item')?.value||'')}
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
  const button=$('ntec-ai-real-estimate');busy=true;button.disabled=true;button.textContent='Pesquisando…';msg('Consultando a IA e pesquisando referências públicas de mercado. Isso pode levar alguns instantes…');
  try{
   const result=await api().requestProposalPriceAI({item_name:selected.item_name,item_code:selected.item_code,category:selected.category,unit:selected.unit,current_price:Number(selected.reference_price||0),price_label:selected.price_label||'',notes:selected.notes||''});
   if(!result||!Number.isFinite(Number(result.recommended_price))||!Number.isFinite(Number(result.market_price_min))||!Number.isFinite(Number(result.market_price_max)))throw new Error('A IA retornou valores inválidos.');
   const min=Number(result.market_price_min),max=Number(result.market_price_max),recommended=Number(result.recommended_price);
   const current=Number(selected.reference_price||0),assessment=result.assessment|| (current<min?'abaixo':current>max?'acima':'na_faixa');
   const sources=Array.isArray(result.sources)?result.sources:[];
   const factors=Array.isArray(result.cost_factors)?result.cost_factors:[];
   const noteLines=['Análise de mercado assistida por IA com pesquisa web.','Data da análise: '+(result.data_as_of||new Date().toISOString().slice(0,10)), 'Modelo: '+(result.model||'não informado'),'Confiança: '+(result.confidence||'não informada'),'Racional: '+(result.rationale||'não informado'), 'Fatores de custo: '+(factors.join('; ')||'não informados'), 'Fontes consultadas: '+(sources.map(x=>(x.title||x.url)+' — '+x.url+(x.summary?' — '+x.summary:'')).join(' | ')||'Nenhuma fonte listada pela IA'),'Aviso: estimativa indicativa; confira escopo, unidade, impostos, deslocamento, equipamento, equipe e margem antes de aplicar.'];
   const years=1;
   const band=Math.max(0,Math.min(50,Math.round((Math.max(recommended-min,max-recommended)/Math.max(recommended,1))*1000)/10));
   lastEstimate={reference_value_id:selected.id,item_name:selected.item_name,item_code:selected.item_code,category:selected.category,unit:selected.unit,base_price:current,recommended_price:Math.round(recommended*100)/100,market_price_min:Math.round(min*100)/100,market_price_max:Math.round(max*100)/100,annual_adjustment_percent:Number(result.annual_adjustment_percent),band_percent:band,index_name:'IA OpenAI + pesquisa web',index_period:result.data_as_of||new Date().toISOString().slice(0,10),years_elapsed:years,assessment,notes:noteLines.join('\n')};
   lastSavedReview=null;$('ntec-ai-save').disabled=false;$('ntec-ai-apply').classList.add('hidden');
   const label=assessment==='abaixo'?'Preço atual abaixo da faixa estimada':assessment==='acima'?'Preço atual acima da faixa estimada':assessment==='sem_preco_numerico'?'Sem preço numérico comparável':'Preço atual dentro da faixa estimada';
   const css=assessment==='abaixo'?'bad':assessment==='na_faixa'?'good':'';
   const sourceHtml=sources.length?sources.map(source=>'<li><a href="'+esc(source.url)+'" target="_blank" rel="noopener">'+esc(source.title||source.url)+'</a>'+(source.summary?'<div class="muted small">'+esc(source.summary)+'</div>':'')+'</li>').join(''):'<li>Nenhuma fonte verificável retornada. Use a estimativa apenas como triagem e confira os preços manualmente.</li>';
   $('ntec-ai-result').innerHTML='<div><span class="ntec-ai-status '+css+'">'+esc(label)+'</span> <span class="ntec-ai-tag">Confiança: '+esc(result.confidence||'não informada')+'</span></div><div class="metrics">'+
   '<div class="metric"><span>Preço atual NTEC</span><strong>'+money(current)+'</strong></div>'+
   '<div class="metric"><span>Recomendação da IA</span><strong>'+money(recommended)+'</strong></div>'+
   '<div class="metric"><span>Faixa estimada</span><strong>'+money(min)+' – '+money(max)+'</strong></div>'+
   '<div class="metric"><span>Reajuste anual sugerido</span><strong>'+Number(result.annual_adjustment_percent).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%</strong></div></div>'+
   '<p><strong>Justificativa:</strong> '+esc(result.rationale||'Sem justificativa retornada.')+'</p>'+
   (factors.length?'<p><strong>Fatores de custo a validar:</strong> '+esc(factors.join('; '))+'</p>':'')+
   '<p><strong>Fontes da pesquisa:</strong></p><ul>'+sourceHtml+'</ul>'+
   '<p class="muted small">Estimativa de apoio à decisão, não cotação garantida. O preço oficial só muda após salvar a revisão e clicar em “Aplicar preço recomendado à tabela”.</p>';
   msg('Análise de IA pronta. Revise as fontes e salve a revisão para manter o histórico.');
  }catch(e){msg('Não foi possível obter a análise da IA: '+(e?.message||'erro desconhecido'),true)}
  finally{busy=false;button.disabled=false;button.textContent='Pesquisar mercado com IA'}
 }
 async function saveReview(){
  if(busy||!lastEstimate)return;
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
  p.innerHTML=items.map((r,i)=>'<button type="button" data-ntec-ref-pick="'+i+'"><strong>'+esc(r.item_name)+'</strong><small>'+esc([r.item_code,r.category,r.unit].filter(Boolean).join(' · '))+'</small><b>'+(r.price_label?esc(r.price_label)+' · valor numérico '+money(r.reference_price):money(r.reference_price))+'</b></button>').join('');
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
  input.dataset.ntecPickingRef='1';setInput(input,item.item_name);delete input.dataset.ntecPickingRef;
  const unit=row.querySelector('[data-line-field="unit"],.ntec-line-unit,input[name="unit"]');
  const price=row.querySelector('[data-line-field="unit_price"],input[name="unit_price"],.ntec-line-price,[data-field="unit_price"]');
  if(unit)setInput(unit,item.unit||'serviço');
  if(price)setInput(price,Number(item.reference_price||0).toFixed(2));
  row.dataset.referenceValueId=item.id;
  input.title=item.price_label?'Valor textual na referência: '+item.price_label+'. Confirme antes de enviar a proposta.':'Preço preenchido pela tabela de referência. Confirme quantidade e condições.';
  closePopup();
 }
 function wireAutocomplete(){
  document.addEventListener('input',e=>{
   if(!descriptionInput(e.target))return;
   if(e.target.dataset.ntecPickingRef==='1')return;
   const changedRow=e.target.closest('tr');if(changedRow)delete changedRow.dataset.referenceValueId;
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
 function init(){
  if(initialized)return;
  if(!ensureAssistant()){const observer=new MutationObserver(()=>{if(ensureAssistant()){observer.disconnect();bind()}});observer.observe(document.body,{childList:true,subtree:true});return}
  bind();
 }
 function bind(){
  if(initialized)return;initialized=true;wireAutocomplete();
  const retry=setInterval(()=>{if(api()?.loadProposalReferenceValues&&api()?.loadProposalPriceReviews){clearInterval(retry);loadRefs()}},400);
  if(api()?.loadProposalReferenceValues&&api()?.loadProposalPriceReviews){clearInterval(retry);loadRefs()}
  document.querySelectorAll('#nav button').forEach(b=>b.addEventListener('click',()=>{if($('ntec-ref-price-panel'))loadRefs()}));
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
