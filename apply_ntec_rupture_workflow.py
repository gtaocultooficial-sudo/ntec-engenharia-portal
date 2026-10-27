#!/usr/bin/env python3
from pathlib import Path
import re, sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/admin/index.html")
s = path.read_text(encoding="utf-8")
s = s.replace("Portal NTEC · v17", "Portal NTEC · v18")

def once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: esperado 1 trecho, encontrados {count}")
    s = s.replace(old, new, 1)

def rx(pattern, replacement, label):
    global s
    result, count = re.subn(pattern, lambda _m: replacement, s, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: bloco não encontrado")
    s = result

# Save report first, then use the dedicated modal to enter actual rupture results later.
once(
 "status:'rascunho'}).select('id,report_number').single(); if(error) throw error; return {id:data.id,reportNumber:data.report_number}; },",
 "status:r.status||'rascunho'}).select('id,report_number').single(); if(error) throw error; return {id:data.id,reportNumber:data.report_number}; }, async updateReportResults(id,payload){ if(!currentSession || currentProfile?.role!=='admin') throw new Error('Acesso administrativo necessário.'); const {error}=await supabase.from('reports').update({structured_data:payload.structuredData,results:payload.results,status:payload.status}).eq('id',id); if(error) throw error; return true; },",
 "API de atualização de resultados")

rx(r"async function addReport\(\)\{.*?\}\s*function renderReports",
"""async function addReport(){
 ntecGenerateNarrative(false);
 const projectId=document.getElementById('reportproject').value;
 const title=document.getElementById('reporttitle').value.trim();
 const type=document.getElementById('reporttype').value;
 const tpl=REPORT_TEMPLATES[type]||REPORT_TEMPLATES.outro;
 if(!projectId||!title)return alert('Selecione a obra e confira o título do relatório.');
 for(const f of (tpl.fields||[])){
  const el=document.querySelector('#reporttemplatefields [data-report-field="'+f.name+'"]');
  if(f.required&&el&&!String(el.value||'').trim()){el.focus();return alert('Preencha o campo obrigatório: '+f.label)}
 }
 const ruptureReport=type==='ruptura_concreto';
 if(!ruptureReport&&tpl.matrix?.required&&!reportMatrixHasData('primary'))return alert('Preencha pelo menos uma linha em: '+tpl.matrix.label);
 if(tpl.extraMatrix?.required&&!reportMatrixHasData(tpl.extraMatrix.name))return alert('Preencha pelo menos uma linha em: '+tpl.extraMatrix.label);
 const btn=document.querySelector('#reportform button.btn.primary');
 if(btn){btn.disabled=true;btn.textContent='Salvando…'}
 try{
  const saved=await window.NTEC_SUPABASE.saveReport({
   projectId,title,type,date:document.getElementById('reportdate').value,
   content:document.getElementById('reportcontent').value,
   methodology:document.getElementById('reportmethod').value,
   results:ruptureReport?'Aguardando os ensaios de ruptura. Os resultados serão lançados depois que cada CP for rompido.':document.getElementById('reportresults').value,
   observations:document.getElementById('reportobservations').value,
   technicalResponsible:document.getElementById('reportresponsible').value,
   professionalRegistration:document.getElementById('reportregistration').value,
   normativeReferences:document.getElementById('reportnormativerefs').value,
   structuredData:collectReportStructuredData(),
   status:ruptureReport?'aguardando_ruptura':'rascunho'
  });
  const exact=saved?.reportNumber||'';
  reports=await window.NTEC_SUPABASE.loadReports();
  renderReports();clearReportForm();closeForm('reportform');
  alert(ruptureReport?'Relatório '+exact+' criado e ficou aguardando os resultados de ruptura. Use “Lançar ruptura” quando tiver a leitura da prensa.':'Relatório '+exact+' salvo como rascunho. Confira os cálculos antes de emitir.');
 }catch(err){alert('Não foi possível salvar o relatório: '+(err?.message||'erro desconhecido'))}
 finally{if(btn){btn.disabled=false;btn.textContent='Salvar relatório no banco'}}
}
function renderReports""",'salvar relatório antes da ruptura')

staged_js = r'''
function ntecReportMatrixColumns(){
 const tpl=REPORT_TEMPLATES['ruptura_concreto']||{};
 return (tpl.matrix?.columns||[]).map(col=>String(col).replace(/\(kN\)/ig,'(tf)'));
}
function ntecRuptureHeaderIndex(columns,kind){
 const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 const h=columns.map(norm);
 const exact={cp:['cp nº','cp n°','cp','amostra nº','amostra n°','amostra'],age:['idade (dias)','idade dias','idade'],date:['data de ruptura','dt. ruptura','dt ruptura','ruptura'],load:['carga (tf)','carga de ruptura (tf)','carga'],resistance:['resistência (mpa)','resistencia (mpa)','resist. a compressão','resistência à compressão']};
 for(const candidate of exact[kind]||[]){const idx=h.findIndex(x=>x===norm(candidate));if(idx>=0)return idx;}
 return h.findIndex(x=>{
  if(kind==='cp')return (x.includes('cp')||x.includes('amostra'))&&!x.includes('dim');
  if(kind==='age')return x.includes('idade');
  if(kind==='date')return (x.includes('ruptura')&&x.includes('data'))||(x.includes('dt.')&&x.includes('ruptura'));
  if(kind==='load')return x.includes('carga');
  if(kind==='resistance')return x.includes('resist')&&x.includes('mpa');
  return false;
 });
}
function ntecRuptureParseNumber(value){
 let s=String(value??'').trim().replace(/\s/g,'');
 if(!s)return NaN;
 if(s.includes(',')&&s.includes('.'))s=s.replace(/\./g,'').replace(',','.');
 else s=s.replace(',','.');
 const n=Number(s);return Number.isFinite(n)?n:NaN;
}
function ntecRuptureFormat(n,d=2){return Number.isFinite(n)?n.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d}):''}
function ntecRuptureFormatDateFromAge(castingDate,age){
 const n=ntecRuptureParseNumber(age);
 if(!/^\d{4}-\d{2}-\d{2}$/.test(String(castingDate||''))||!Number.isFinite(n)||n<0)return '';
 const dt=new Date(castingDate+'T12:00:00');if(Number.isNaN(dt.getTime()))return '';
 dt.setDate(dt.getDate()+Math.round(n));
 return String(dt.getDate()).padStart(2,'0')+'/'+String(dt.getMonth()+1).padStart(2,'0')+'/'+dt.getFullYear();
}
function ntecRuptureCalculateResistance(tf,fields){
 const load=ntecRuptureParseNumber(tf);
 const dimText=String(fields?.specimen_dimensions||fields?.dimensions||'');
 const dims=dimText.match(/\d+(?:[.,]\d+)?/g)?.map(x=>Number(x.replace(',','.')))||[];
 const diameter=dims[0],height=dims.length>1?dims[1]:NaN;
 if(!Number.isFinite(load)||load<0||!Number.isFinite(diameter)||diameter<=0)return '';
 let correction=1;
 if(Number.isFinite(height)&&height>0){
  const ratio=height/diameter,table=[[1,.87],[1.25,.93],[1.5,.96],[1.75,.98],[2,1]];
  if(ratio<1)return '';
  if(ratio<2){
   let found=false;
   for(let i=1;i<table.length;i++)if(ratio>=table[i-1][0]&&ratio<=table[i][0]){
    correction=table[i-1][1]+(ratio-table[i-1][0])*(table[i][1]-table[i-1][1])/(table[i][0]-table[i-1][0]);found=true;break;
   }
   if(!found)return '';
  }
 }
 return ntecRuptureFormat(load*9806.65/(Math.PI*diameter*diameter/4)*correction,2);
}
function ntecRuptureRows(report){
 const cols=ntecReportMatrixColumns(),raw=String(report?.structured_data?.matrix?.primary||'').trim();
 return raw?raw.split(/\r?\n/).filter(Boolean).map(line=>{const row=line.split('|').map(x=>x.trim());while(row.length<cols.length)row.push('');return row.slice(0,cols.length)}):[];
}
function ntecRuptureMeasurementCount(report){
 const rows=ntecRuptureRows(report),cols=ntecReportMatrixColumns(),ri=ntecRuptureHeaderIndex(cols,'resistance'),li=ntecRuptureHeaderIndex(cols,'load');
 return rows.filter(row=>ntecRuptureParseNumber(row[ri])>0&&ntecRuptureParseNumber(row[li])>0).length;
}
function ntecRuptureSummary(rows,cols){
 const ai=ntecRuptureHeaderIndex(cols,'age'),ri=ntecRuptureHeaderIndex(cols,'resistance'),li=ntecRuptureHeaderIndex(cols,'load');
 const measured=rows.filter(row=>ntecRuptureParseNumber(row[ai])>=0&&ntecRuptureParseNumber(row[li])>0&&ntecRuptureParseNumber(row[ri])>0);
 if(!measured.length)return 'Aguardando os ensaios de ruptura. Nenhuma leitura de prensa foi registrada.';
 const vals=measured.map(row=>ntecRuptureParseNumber(row[ri])),avg=vals.reduce((a,b)=>a+b,0)/vals.length,groups={};
 measured.forEach(row=>{const age=ntecRuptureParseNumber(row[ai]);(groups[age]||(groups[age]=[])).push(ntecRuptureParseNumber(row[ri]));});
 const byAge=Object.keys(groups).map(age=>age+' dias: média '+ntecRuptureFormat(groups[age].reduce((a,b)=>a+b,0)/groups[age].length)+' MPa').join('; ');
 return 'Resultados de ruptura lançados: '+measured.length+' corpo(s) de prova. Média geral: '+ntecRuptureFormat(avg)+' MPa; mínimo: '+ntecRuptureFormat(Math.min(...vals))+' MPa; máximo: '+ntecRuptureFormat(Math.max(...vals))+' MPa. Médias por idade: '+byAge+'.';
}
function ntecRuptureModalRow(values,columns,index){
 const ix={cp:ntecRuptureHeaderIndex(columns,'cp'),age:ntecRuptureHeaderIndex(columns,'age'),date:ntecRuptureHeaderIndex(columns,'date'),load:ntecRuptureHeaderIndex(columns,'load'),resistance:ntecRuptureHeaderIndex(columns,'resistance')};
 const cp=ix.cp>=0?values[ix.cp]:(index+1),age=ix.age>=0?values[ix.age]:'',load=ix.load>=0?values[ix.load]:'';
 return '<tr data-ntec-rupture-row><td><input data-rp="cp" aria-label="Identificação do corpo de prova" value="'+esc(cp||'')+'" placeholder="CP '+(index+1)+'"></td><td><input data-rp="age" aria-label="Idade em dias" type="number" min="0" step="1" value="'+esc(age||'')+'" placeholder="7 / 28"></td><td><input data-rp="date" aria-label="Data de ruptura (pode ser ajustada manualmente)" placeholder="dd/mm/aaaa" value="'+esc(ix.date>=0?values[ix.date]:'')+'"></td><td><input data-rp="load" aria-label="Carga da prensa em tf" inputmode="decimal" value="'+esc(load||'')+'" placeholder="Leitura em tf"></td><td><input data-rp="resistance" aria-label="Resistência MPa calculada" readonly value="'+esc(ix.resistance>=0?values[ix.resistance]:'')+'"></td><td><button type="button" data-rp-remove title="Remover linha">×</button></td></tr>';
}
function openRuptureEntry(reportId){
 const report=reports.find(r=>String(r.id)===String(reportId));
 if(!report||report.report_type!=='ruptura_concreto')return alert('O lançamento posterior está disponível para relatórios de ruptura de concreto.');
 const cols=ntecReportMatrixColumns(),indices={cp:ntecRuptureHeaderIndex(cols,'cp'),age:ntecRuptureHeaderIndex(cols,'age'),date:ntecRuptureHeaderIndex(cols,'date'),load:ntecRuptureHeaderIndex(cols,'load'),resistance:ntecRuptureHeaderIndex(cols,'resistance')};
 for(const k of ['age','date','load','resistance'])if(indices[k]<0)return alert('A tabela de ruptura não contém a coluna necessária ('+k+'). Verifique o modelo.');
 const fields=report.structured_data?.fields||{},castingDate=String(fields.casting_date||'');
 document.getElementById('ntec-rupture-modal')?.remove();
 const overlay=document.createElement('div');overlay.id='ntec-rupture-modal';
 overlay.innerHTML='<div class="ntec-rp-card" role="dialog" aria-modal="true" aria-labelledby="ntec-rp-title"><div class="ntec-rp-head"><div><h2 id="ntec-rp-title">Lançamento de ruptura</h2><p>'+esc(report.report_number||'')+' — '+esc(report.title||'Ruptura de concreto')+'</p></div><button type="button" data-rp-close aria-label="Fechar">×</button></div><div class="ntec-rp-info"><b>Obra:</b> '+esc(report.project||'')+' &nbsp; <b>Série:</b> '+esc(fields.series||'—')+' &nbsp; <b>Moldagem:</b> '+esc(castingDate||'não informada')+'<br>Informe os CPs e as leituras reais quando o ensaio for realizado. A data de ruptura é prevista pela data de moldagem + idade; a resistência usa a carga em tf e as dimensões cadastradas.</div><div class="ntec-rp-tablewrap"><table class="ntec-rp-table"><thead><tr><th>CP</th><th>Idade (dias)</th><th>Data de ruptura prevista</th><th>Carga (tf)</th><th>Resistência (MPa)</th><th></th></tr></thead><tbody id="ntec-rp-rows"></tbody></table></div><div class="ntec-rp-actions"><button type="button" class="btn" id="ntec-rp-add">+ Adicionar CP</button><span class="ntec-rp-spacer"></span><button type="button" class="btn" data-rp-close>Cancelar</button><button type="button" class="btn primary" id="ntec-rp-save">Salvar resultados parciais</button><button type="button" class="btn primary" id="ntec-rp-finish">Salvar e concluir</button></div><div class="ntec-rp-status" id="ntec-rp-status" role="status"></div></div>';
 const style=document.createElement('style');style.textContent='#ntec-rupture-modal{position:fixed;z-index:99999;inset:0;background:#10263f88;display:flex;align-items:center;justify-content:center;padding:16px}#ntec-rupture-modal .ntec-rp-card{width:min(1100px,98vw);max-height:92vh;overflow:auto;background:#fff;border-radius:12px;padding:20px;box-shadow:0 18px 60px #0003;color:#172536}#ntec-rupture-modal .ntec-rp-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;border-bottom:1px solid #dce3ea;padding-bottom:10px;margin-bottom:12px}#ntec-rupture-modal h2{font-size:20px;margin:0 0 5px}#ntec-rupture-modal p{margin:0;color:#607083;font-size:13px}#ntec-rupture-modal .ntec-rp-head button{font-size:22px;border:0;background:#f0f3f6;border-radius:6px;width:34px;height:34px;cursor:pointer}#ntec-rupture-modal .ntec-rp-info{font-size:13px;line-height:1.6;background:#f3f6f9;border:1px solid #dfe5eb;padding:10px;border-radius:7px;margin-bottom:12px}#ntec-rupture-modal .ntec-rp-tablewrap{overflow-x:auto}#ntec-rupture-modal .ntec-rp-table{width:100%;border-collapse:collapse;min-width:660px}#ntec-rupture-modal .ntec-rp-table th,#ntec-rupture-modal .ntec-rp-table td{border:1px solid #d2dbe4;padding:7px;text-align:left;font-size:12px}#ntec-rupture-modal .ntec-rp-table th{background:#edf2f6}#ntec-rupture-modal .ntec-rp-table input{width:100%;min-width:75px;padding:8px 7px;border:1px solid #cbd6e1;border-radius:5px;font:inherit}#ntec-rupture-modal .ntec-rp-table input[readonly]{background:#eef4fa;color:#163b59;font-weight:700}#ntec-rupture-modal .ntec-rp-actions{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:14px}#ntec-rupture-modal .ntec-rp-spacer{flex:1}#ntec-rupture-modal .ntec-rp-status{margin-top:10px;font-size:13px;white-space:pre-wrap}#ntec-rupture-modal button:disabled{opacity:.6}@media(max-width:650px){#ntec-rupture-modal{padding:6px}#ntec-rupture-modal .ntec-rp-card{padding:12px;max-height:96vh}#ntec-rupture-modal .ntec-rp-actions .ntec-rp-spacer{display:none}}';
 overlay.appendChild(style);document.body.appendChild(overlay);
 const body=overlay.querySelector('#ntec-rp-rows'),stored=ntecRuptureRows(report);
 if(stored.length)stored.forEach((row,i)=>body.insertAdjacentHTML('beforeend',ntecRuptureModalRow(row,cols,i)));
 else body.insertAdjacentHTML('beforeend',ntecRuptureModalRow(Array(cols.length).fill(''),cols,0));
 const syncRow=row=>{
  const age=row.querySelector('[data-rp="age"]')?.value||'',load=row.querySelector('[data-rp="load"]')?.value||'';
  const date=row.querySelector('[data-rp="date"]'),res=row.querySelector('[data-rp="resistance"]');
  if(date&&!date.dataset.manual){const predicted=ntecRuptureFormatDateFromAge(castingDate,age);if(predicted)date.value=predicted;}
  if(res)res.value=load.trim()?ntecRuptureCalculateResistance(load,fields):'';
 };
 const wireRow=row=>{
  const dateInput=row.querySelector('[data-rp="date"]');if(dateInput&&dateInput.value.trim())dateInput.dataset.manual='true';dateInput?.addEventListener('input',()=>{dateInput.dataset.manual='true';});row.querySelector('[data-rp="age"]')?.addEventListener('input',()=>syncRow(row));
  row.querySelector('[data-rp="load"]')?.addEventListener('input',()=>syncRow(row));
  row.querySelector('[data-rp-remove]')?.addEventListener('click',()=>{if(body.querySelectorAll('[data-ntec-rupture-row]').length>1)row.remove();else row.querySelectorAll('input').forEach(input=>input.value='');});
  syncRow(row);
 };
 body.querySelectorAll('[data-ntec-rupture-row]').forEach(wireRow);
 overlay.querySelector('#ntec-rp-add').addEventListener('click',()=>{
  const vals=Array(cols.length).fill(''),count=body.querySelectorAll('[data-ntec-rupture-row]').length;
  if(indices.cp>=0)vals[indices.cp]=String(count+1);
  body.insertAdjacentHTML('beforeend',ntecRuptureModalRow(vals,cols,count));
  wireRow(body.lastElementChild);
 });
 const close=()=>overlay.remove();
 overlay.querySelectorAll('[data-rp-close]').forEach(btn=>btn.addEventListener('click',close));
 overlay.addEventListener('click',e=>{if(e.target===overlay)close()});
 const save=async finish=>{
  const status=overlay.querySelector('#ntec-rp-status'),saveBtn=overlay.querySelector('#ntec-rp-save'),finishBtn=overlay.querySelector('#ntec-rp-finish');
  const entries=[...body.querySelectorAll('[data-ntec-rupture-row]')].map(row=>({
   cp:row.querySelector('[data-rp="cp"]')?.value.trim()||'',
   age:row.querySelector('[data-rp="age"]')?.value.trim()||'',
   date:row.querySelector('[data-rp="date"]')?.value.trim()||'',
   load:row.querySelector('[data-rp="load"]')?.value.trim()||'',
   resistance:row.querySelector('[data-rp="resistance"]')?.value.trim()||''
  })).filter(row=>row.cp||row.age||row.load);
  if(finish&&(!entries.length||entries.some(row=>!row.age||!row.load||!row.resistance))){
   status.textContent='Para concluir, todos os CPs lançados precisam ter idade, carga da prensa em tf e resistência calculada. Para continuar depois, use “Salvar resultados parciais”.';return;
  }
  const dataRows=[];
  for(const e of entries){
   const cells=Array(cols.length).fill('');
   if(indices.cp>=0)cells[indices.cp]=e.cp;
   cells[indices.age]=e.age;cells[indices.date]=e.date;cells[indices.load]=e.load;cells[indices.resistance]=e.resistance;
   dataRows.push(cells.join(' | '));
  }
  const updated=JSON.parse(JSON.stringify(report.structured_data||{}));
  updated.fields=updated.fields||{};updated.matrix=updated.matrix||{};
  updated.matrix.primary=dataRows.join(String.fromCharCode(10));
  const updatedRows=dataRows.map(line=>line.split('|').map(v=>v.trim()));
  const resultText=ntecRuptureSummary(updatedRows,cols);
  const measured=updatedRows.filter(row=>ntecRuptureParseNumber(row[indices.age])>=0&&ntecRuptureParseNumber(row[indices.load])>0&&ntecRuptureParseNumber(row[indices.resistance])>0).length;
  const nextStatus=finish?'concluido':measured?'em_andamento':'aguardando_ruptura';
  saveBtn.disabled=true;finishBtn.disabled=true;status.textContent='Salvando os resultados…';
  try{
   await window.NTEC_SUPABASE.updateReportResults(report.id,{structuredData:updated,results:resultText,status:nextStatus});
   reports=await window.NTEC_SUPABASE.loadReports();renderReports();
   status.textContent='Resultados salvos. '+resultText;setTimeout(close,700);
  }catch(err){status.textContent='Não foi possível salvar: '+(err?.message||'erro desconhecido');}
  finally{saveBtn.disabled=false;finishBtn.disabled=false;}
 };
 overlay.querySelector('#ntec-rp-save').addEventListener('click',()=>save(false));
 overlay.querySelector('#ntec-rp-finish').addEventListener('click',()=>save(true));
}
function ntecReportStatusText(report){
 const status=String(report.status||'').toLowerCase();
 if(status==='aguardando_ruptura')return 'Aguardando ruptura';
 if(status==='em_andamento')return 'Resultados parciais';
 if(status==='concluido')return 'Concluído';
 return report.statusLabel||report.status||'Rascunho';
}
'''

rx(r"function renderReports\(\)\{.*?\}\s*function matrixHtml",
"""function ntecRenderRuptureAlerts(){
 const tableBody=document.getElementById('reportsbody');if(!tableBody)return;
 const table=tableBody.closest('table');if(!table)return;
 let panel=document.getElementById('ntec-rupture-alerts');
 if(!panel){panel=document.createElement('section');panel.id='ntec-rupture-alerts';panel.style.cssText='display:none;margin:0 0 14px;padding:14px 16px;border:1px solid #e6b85c;border-radius:10px;background:#fff8e7;color:#573b08';table.parentNode.insertBefore(panel,table);}
 const today=new Date();today.setHours(0,0,0,0);
 const due=[];
 for(const report of reports){
  if(report.report_type!=='ruptura_concreto')continue;
  const fields=report.structured_data?.fields||{},castingDate=String(fields.casting_date||'');
  const cols=ntecReportMatrixColumns(),rows=ntecRuptureRows(report);
  const ai=ntecRuptureHeaderIndex(cols,'age'),di=ntecRuptureHeaderIndex(cols,'date'),li=ntecRuptureHeaderIndex(cols,'load');
  if(ai<0||li<0)continue;
  rows.forEach((row,i)=>{
   const age=ntecRuptureParseNumber(row[ai]),load=ntecRuptureParseNumber(row[li]);
   if(!Number.isFinite(age)||age<0||load>0)return;
   const rawDate=di>=0?String(row[di]||'').trim():'';
   let date=null,m=rawDate.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
   if(m)date=new Date(Number(m[3]),Number(m[2])-1,Number(m[1]));
   if(!date&&/^\d{4}-\d{2}-\d{2}$/.test(castingDate)){date=new Date(castingDate+'T12:00:00');date.setDate(date.getDate()+Math.round(age));}
   if(!date||Number.isNaN(date.getTime()))return;
   date.setHours(0,0,0,0);const days=Math.round((date-today)/86400000);
   if(days<=3)due.push({report,cp:row[ntecRuptureHeaderIndex(cols,'cp')]||String(i+1),date,days});
  });
 }
 due.sort((a,b)=>a.days-b.days);
 if(!due.length){panel.style.display='none';panel.innerHTML='';return;}
 panel.style.display='block';
 const rows=due.map(item=>{
  const label=item.days<0?'ATRASADA há '+Math.abs(item.days)+' dia(s)':item.days===0?'PREVISTA PARA HOJE':'Prevista em '+item.days+' dia(s)';
  const color=item.days<=0?'#a12b20':'#805b09';
  return '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #ead9b4"><strong style="color:'+color+'">'+label+'</strong><span>'+esc(item.date.toLocaleDateString('pt-BR'))+'</span><span>CP '+esc(item.cp)+'</span><span>'+esc(item.report.report_number||item.report.title||'Relatório')+'</span><span>'+esc(item.report.project||'')+'</span><button type="button" class="btn secondary" data-rp-report="'+esc(item.report.id)+'">Lançar ruptura</button></div>';
 }).join('');
 panel.innerHTML='<strong>⚠️ Atenção: rupturas pendentes</strong><div style="font-size:13px;margin-top:5px">Os CPs abaixo atingiram ou estão próximos da idade prevista e ainda não têm carga de prensa registrada. A data é uma previsão; se o ensaio não foi realizado, mantenha o lançamento pendente e atualize quando ocorrer.</div>'+rows;
 panel.querySelectorAll('[data-rp-report]').forEach(button=>button.addEventListener('click',()=>openRuptureEntry(button.dataset.rpReport)));
}
function ntecRuptureRevisionProgress(report){
 const columns=ntecReportMatrixColumns(),rows=ntecRuptureRows(report);
 const ageIndex=ntecRuptureHeaderIndex(columns,'age'),loadIndex=ntecRuptureHeaderIndex(columns,'load'),resIndex=ntecRuptureHeaderIndex(columns,'resistance');
 if(ageIndex<0||loadIndex<0||resIndex<0)return {total:0,missing:0,ready:false};
 const target=rows.filter(row=>[7,28].includes(ntecRuptureParseNumber(row[ageIndex])));
 const has7=target.some(row=>ntecRuptureParseNumber(row[ageIndex])===7),has28=target.some(row=>ntecRuptureParseNumber(row[ageIndex])===28);
 const missing=target.filter(row=>!(ntecRuptureParseNumber(row[loadIndex])>0&&ntecRuptureParseNumber(row[resIndex])>0)).length;
 return {total:target.length,missing,has7,has28,ready:target.length>0&&has7&&has28&&missing===0};
}
function ntecReportDisplayNumber(report){
 const revision=report?.structured_data?.revision||{};
 const number=Math.max(0,Number(revision.number||report?.structured_data?.fields?.report_revision_number||0)||0);
 if(number>0)return String(revision.display_number||('RV'+String(number).padStart(2,'0')+' - '+(revision.parent_report_number||report?.structured_data?.fields?.report_revision_of_number||report?.report_number||'Relatório')));
 return String(report?.report_number||'Número pendente');
}
function ntecExistingRevisionFor(report){
 return reports.find(item=>{
   const revision=item.structured_data?.revision||{};
   return String(revision.parent_report_id||'')===String(report.id)&&Number(revision.number||0)===1;
 });
}
async function createRuptureRevision(reportId){
 const report=reports.find(item=>String(item.id)===String(reportId));
 if(!report)return alert('Relatório não encontrado.');
 if(Number(report.structured_data?.revision?.number||report.structured_data?.fields?.report_revision_number||0)>0)return alert('Para preservar o histórico, crie a próxima revisão a partir do relatório original.');
 const reason=prompt('Motivo da revisão do relatório '+(report.report_number||'')+':');
 if(reason===null)return;
 if(!reason.trim())return alert('Informe o motivo da revisão.');
 const prior=reports.filter(item=>String(item.structured_data?.revision?.parent_report_id||'')===String(report.id));
 const nextNumber=prior.reduce((n,item)=>Math.max(n,Number(item.structured_data?.revision?.number||0)),0)+1;
 if(!confirm('Criar revisão '+String(nextNumber).padStart(2,'0')+'? O original e as revisões anteriores serão preservados. A nova revisão ficará como rascunho para conferência e autorização antes da emissão.'))return;
 const button=[...document.querySelectorAll('[data-rp-revision]')].find(el=>String(el.dataset.rpRevision)===String(report.id));
 if(button){button.disabled=true;button.textContent='Criando revisão…';}
 try{
  const data=JSON.parse(JSON.stringify(report.structured_data||{}));
  data.fields=data.fields||{};
  data.revision={number:nextNumber,display_number:'RV'+String(nextNumber).padStart(2,'0')+' - '+(report.report_number||'Relatório'),parent_report_id:report.id,parent_report_number:report.report_number||'',issued_at:new Date().toISOString(),reason:reason.trim(),status:'rascunho',source_status:report.status||''};
  data.fields.report_revision_number=nextNumber; data.fields.report_revision_of_number=report.report_number||''; data.fields.report_revision_of_id=report.id;
  const note='REVISÃO '+String(nextNumber).padStart(2,'0')+' — motivo: '+reason.trim()+'. Documento de origem: '+(report.report_number||'relatório original')+'. Revisão criada como rascunho; requer conferência e autorização antes da emissão. O original permanece preservado.';
  const observations=String(report.observations||'').trim();
  const saved=await window.NTEC_SUPABASE.saveReport({projectId:report.project_id,title:report.title||'Relatório técnico',type:report.report_type,date:new Date().toISOString().slice(0,10),content:report.content||'',methodology:report.methodology||'',results:report.results||'',observations:(observations?observations+String.fromCharCode(10)+String.fromCharCode(10):'')+note,technicalResponsible:report.technical_responsible||'',professionalRegistration:report.professional_registration||'',normativeReferences:report.normative_references||'',structuredData:data,status:'rascunho'});
  reports=await window.NTEC_SUPABASE.loadReports();renderReports();
  const created=reports.find(item=>String(item.id)===String(saved?.id||'')||(String(item.structured_data?.revision?.parent_report_id||'')===String(report.id)&&Number(item.structured_data?.revision?.number||0)===nextNumber));
  alert('Revisão '+String(nextNumber).padStart(2,'0')+' criada como rascunho: '+(created?ntecReportDisplayNumber(created):'aguardando atualização da lista')+'. Confira os dados e autorize antes de emitir.');
 }catch(err){alert('Não foi possível criar a revisão: '+(err?.message||'erro desconhecido'));if(button){button.disabled=false;button.textContent='Criar revisão';}}
}
function ntecReportIsCompleted(report){
 const status=String(report?.status||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[ -]+/g,'_');
 return ['emitido','concluido','finalizado','aprovado','issued','completed','final'].includes(status);
}
function ntecEnsureReportSections(){
 const body=document.getElementById('reportsbody');if(!body)return;
 const table=body.closest('table');if(!table)return;
 let nav=document.getElementById('ntec-report-sections');
 if(!nav){
  nav=document.createElement('div');nav.id='ntec-report-sections';
  nav.style.cssText='display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px;padding:10px;background:#f3f6fa;border:1px solid #dce4ed;border-radius:10px';
  nav.innerHTML='<button type="button" data-report-view="active" class="btn primary">Em andamento</button><button type="button" data-report-view="completed" class="btn">Concluídos / emitidos</button><span id="ntec-report-view-counts" style="align-self:center;margin-left:auto;color:#64748b;font-size:12px"></span>';
  table.parentNode.insertBefore(nav,table);
  nav.querySelectorAll('[data-report-view]').forEach(button=>button.addEventListener('click',()=>{
   window.ntecReportsView=button.dataset.reportView;
   nav.querySelectorAll('[data-report-view]').forEach(b=>{b.classList.toggle('primary',b===button);});
   renderReports();
  }));
 }
 const active=reports.filter(r=>!ntecReportIsCompleted(r)).length,completed=reports.length-active;
 const counts=nav.querySelector('#ntec-report-view-counts');if(counts)counts.textContent=active+' em andamento · '+completed+' concluídos/emitidos';
 const view=window.ntecReportsView||'active';
 nav.querySelectorAll('[data-report-view]').forEach(b=>b.classList.toggle('primary',b.dataset.reportView===view));
}
function renderReports(){
 ntecEnsureReportSections();
 const body=document.getElementById('reportsbody');
 const view=window.ntecReportsView||'active';
 const visibleReports=reports.filter(r=>view==='completed'?ntecReportIsCompleted(r):!ntecReportIsCompleted(r));
 body.innerHTML=visibleReports.length?visibleReports.map(r=>{
  const ruptureButton=r.report_type==='ruptura_concreto'?'<button class="btn secondary" data-rp-report="'+esc(r.id)+'">'+(ntecRuptureMeasurementCount(r)?'Atualizar rupturas':'Lançar ruptura')+'</button> ':'';
  const revisionNumber=Number(r.structured_data?.revision?.number||r.structured_data?.fields?.report_revision_number||0);
  const priorRevision=revisionNumber===0?ntecExistingRevisionFor(r):null;
  const revisionButton=revisionNumber>0?'<span class="muted small">Revisão '+String(revisionNumber).padStart(2,'0')+'</span> ':priorRevision?'<span class="muted small">Revisão já criada</span> ':'<button class="btn secondary" data-rp-revision="'+esc(r.id)+'">Criar revisão</button> ';
  const displayType=r.report_type==='ruptura_concreto'?'Relatório de moldagem':(r.typeLabel||r.report_type);return '<tr><td><strong>'+esc(ntecReportDisplayNumber(r))+'</strong><div>'+esc(r.title)+'</div>'+'<div class="muted small">'+esc(r.normative_references?'Referências registradas':'Referências pendentes')+'</div></td><td>'+esc(r.client)+'<div class="muted small">'+esc(r.project)+'</div></td><td>'+esc(displayType)+'</td><td>'+esc(r.report_date||'—')+'</td><td>'+badge(ntecReportStatusText(r))+'</td><td>'+ruptureButton+revisionButton+'<button class="btn" data-rp-edit="'+esc(r.id)+'">Editar</button> <button class="btn" data-rp-pdf="'+esc(r.id)+'">PDF</button></td></tr>';
  }).join(''):'<tr><td colspan="6" class="empty">'+(view==='completed'?'Nenhum relatório concluído ou emitido nesta seção.':'Nenhum relatório em andamento nesta seção.')+'</td></tr>';
 body.querySelectorAll('[data-rp-report]').forEach(button=>button.addEventListener('click',()=>openRuptureEntry(button.dataset.rpReport)));
 body.querySelectorAll('[data-rp-revision]').forEach(button=>button.addEventListener('click',()=>createRuptureRevision(button.dataset.rpRevision)));
 body.querySelectorAll('[data-rp-edit]').forEach(button=>button.addEventListener('click',()=>editReport(button.dataset.rpEdit)));
 body.querySelectorAll('[data-rp-pdf]').forEach(button=>button.addEventListener('click',()=>printNtecReport(button.dataset.rpPdf)));
 ntecRenderRuptureAlerts();
}
function matrixHtml""",'botão de lançamento de ruptura')
once("function matrixHtml",staged_js+"\nfunction matrixHtml",'funções de lançamento posterior')

for token in ['async updateReportResults','openRuptureEntry','ntecRuptureCalculateResistance','Aguardando ruptura','Salvar resultados parciais']:
    if token not in s:
        raise SystemExit('Validação da etapa de ruptura falhou: '+token)
path.write_text(s, encoding="utf-8")
print("Applied staged rupture workflow to", path)
