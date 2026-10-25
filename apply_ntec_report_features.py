#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "_site/admin/index.html")
s=p.read_text(encoding="utf-8")
# The table header is also present as static HTML in this portal build.
# Replace the displayed load label so the unit matches the physical press.
_tf_labels = ("Carga (kN)", "Carga (KN)", "Carga (kn)", "Carga de ruptura (kN)", "Carga de ruptura (KN)")
_tf_replaced = 0
for _label in _tf_labels:
    _tf_replaced += s.count(_label)
    s = s.replace(_label, _label.replace("kN", "tf").replace("KN", "tf").replace("kn", "tf"))
if _tf_replaced == 0:
    raise SystemExit("Não encontrei o cabeçalho Carga (kN) no portal para substituir por tf")
def once(a,b,label):
 global s
 if s.count(a)!=1: raise SystemExit(label+" não encontrado unicamente: "+str(s.count(a)))
 s=s.replace(a,b,1)
def rx(a,b,label):
 global s
 s,n=re.subn(a,b,s,count=1,flags=re.S)
 if n!=1: raise SystemExit(label+" não encontrado")
once(".select('id,name,client_id,clients(company_name)').order('created_at'",".select('id,name,client_id,work_number,clients(company_name)').order('created_at'",'consulta de obras')
once(".select('id,project_id,title,report_type,report_date,content,methodology,results,observations,technical_responsible,professional_registration,structured_data,normative_references,status,created_at,projects(name,clients(company_name))')",".select('id,project_id,report_number,title,report_type,report_date,content,methodology,results,observations,technical_responsible,professional_registration,structured_data,normative_references,status,created_at,projects(name,work_number,clients(company_name))')",'consulta de relatórios')
once("async saveReport(r){ if(!currentSession || currentProfile?.role!=='admin') throw new Error('Acesso administrativo necessário.'); if(!r.projectId) throw new Error('Selecione uma obra cadastrada.'); const {error}=await supabase.from('reports').insert({project_id:r.projectId,title:r.title,report_type:r.type,report_date:r.date||new Date().toISOString().slice(0,10),content:r.content||'',methodology:r.methodology||'',results:r.results||'',observations:r.observations||'',technical_responsible:r.technicalResponsible||'',professional_registration:r.professionalRegistration||'',structured_data:r.structuredData||{},normative_references:r.normativeReferences||'',status:'rascunho'}); if(error) throw error; return true; },","async saveReport(r){ if(!currentSession || currentProfile?.role!=='admin') throw new Error('Acesso administrativo necessário.'); if(!r.projectId) throw new Error('Selecione uma obra cadastrada.'); const {data,error}=await supabase.from('reports').insert({project_id:r.projectId,title:r.title,report_type:r.type,report_date:r.date||new Date().toISOString().slice(0,10),content:r.content||'',methodology:r.methodology||'',results:r.results||'',observations:r.observations||'',technical_responsible:r.technicalResponsible||'',professional_registration:r.professionalRegistration||'',structured_data:r.structuredData||{},normative_references:r.normativeReferences||'',status:'rascunho'}).select('id,report_number').single(); if(error) throw error; return {id:data.id,reportNumber:data.report_number}; },",'salvar relatório')
once('<div class="field"><label>Título do relatório</label><input id="reporttitle" placeholder="Ex.: Ruptura de corpos de prova — concreto" required></div><div class="field"><label>Data do relatório</label><input id="reportdate" type="date"></div>','<div class="field"><label>Número do relatório (automático)</label><input id="reportnumber" readonly placeholder="Gerado ao salvar"><small class="muted small">O código definitivo vem do banco ao salvar.</small></div><div class="field"><label>Título do relatório (automático pelo modelo)</label><input id="reporttitle" placeholder="Será preenchido pelo modelo e pela obra" required></div><div class="field"><label>Data do relatório</label><input id="reportdate" type="date"></div>','campos do cabeçalho')
once('<div class="field"><label>Referências normativas / procedimento aplicado</label><textarea id="reportnormativerefs" rows="3" placeholder="Confirme as edições vigentes e registre apenas os procedimentos efetivamente aplicados."></textarea></div><div class="field"><label>Objeto / descrição do serviço</label><textarea id="reportcontent" placeholder="Objetivo, escopo, local, elemento ensaiado e condições observadas."></textarea></div><div class="field"><label>Metodologia / procedimento realizado</label><textarea id="reportmethod" placeholder="Descreva o procedimento realmente executado, amostragem, preparo, equipamentos e eventuais desvios."></textarea></div><div class="field"><label>Resultados verificados / análise técnica</label><textarea id="reportresults" placeholder="Registre resultados conferidos. Não invente valores nem conclua conformidade sem critérios aplicáveis."></textarea></div><div class="field"><label>Observações / conclusão técnica</label><textarea id="reportobservations" placeholder="Limitações, não conformidades, recomendações e conclusão validada pelo responsável técnico."></textarea></div><div class="formgrid"><div class="field"><label>Responsável técnico</label><input id="reportresponsible" placeholder="Nome do profissional habilitado"></div><div class="field"><label>Registro profissional</label><input id="reportregistration" placeholder="CREA/CAU e UF, se aplicável"></div></div>','<div class="field"><label>Referências normativas sugeridas</label><textarea id="reportnormativerefs" rows="2" placeholder="Preenchidas pelo modelo; revise conforme o procedimento executado."></textarea></div><details class="report-advanced"><summary>Complementos opcionais — descrição, método, observações e responsável técnico</summary><div class="report-advanced-body"><div class="field"><label>Objeto / descrição do serviço</label><textarea id="reportcontent" placeholder="Opcional"></textarea></div><div class="field"><label>Metodologia / procedimento realizado</label><textarea id="reportmethod" placeholder="Opcional: procedimento específico ou desvio."></textarea></div><div class="field"><label>Resultados / análise adicional</label><textarea id="reportresults" placeholder="Opcional: informação além da tabela calculada."></textarea></div><div class="field"><label>Observações / conclusão técnica</label><textarea id="reportobservations" placeholder="A conclusão deve ser revisada pelo responsável técnico."></textarea></div><div class="formgrid"><div class="field"><label>Responsável técnico</label><input id="reportresponsible" placeholder="Nome do profissional habilitado"></div><div class="field"><label>Registro profissional</label><input id="reportregistration" placeholder="CREA/CAU e UF, se aplicável"></div></div></div></details>','campos avançados')
s=s.replace('</style>','.report-advanced{border:1px solid var(--line);border-radius:9px;padding:12px;margin:10px 0 14px;background:#f8fafc}.report-advanced summary{cursor:pointer;font-weight:750;color:var(--navy)}.report-advanced-body{padding-top:12px}.field input[readonly],.report-entry-table input[readonly]{background:#eef3f7;color:#173c5a;font-weight:700}.report-entry-table input[data-computed="1"]{background:#eef6fc;border-color:#b8d1e5}.report-computation-note{margin:8px 0 12px;padding:10px 12px;background:#eef5fb;border-left:3px solid var(--blue);border-radius:0 8px 8px 0;font-size:12px;color:#29465f;line-height:1.45}.report-entry-table th,.report-entry-table td{vertical-align:middle}.report-entry-table input{min-width:84px;max-width:150px;padding:8px 9px}.report-entry-table input[data-computed="1"]{font-weight:700;color:#173c5a;background:#eef5fb}.report-advanced summary{font-size:13px}.report-advanced-body textarea{min-height:54px}#reportnumber{font-variant-numeric:tabular-nums}@media(max-width:700px){.report-advanced-body .formgrid{grid-template-columns:1fr}}</style>',1)
old="esc((p.clients?.company_name||'Cliente')+' — '+p.name)"
if s.count(old)<2: raise SystemExit("opções de obra não encontradas")
s=s.replace(old,"esc('OBRA'+String(p.work_number||'').padStart(3,'0')+' · '+(p.clients?.company_name||'Cliente')+' — '+p.name)")
# Auto-title, suppress generated fields in per-test fields.
once("(function initReportTemplates(){","Object.values(REPORT_TEMPLATES).forEach(t=>{t.fields=(t.fields||[]).filter(f=>!['report_number','record_number'].includes(f.name));});\nlet lastAutoReportTitle='',reportTitleWasEdited=false;\nfunction ntecToday(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')}\nfunction ntecSelectedProject(){return projectsData.find(p=>String(p.id)===String(document.getElementById('reportproject')?.value||''))}\nfunction updateReportTitleAuto(){const el=document.getElementById('reporttitle');if(!el)return;const tpl=REPORT_TEMPLATES[document.getElementById('reporttype')?.value||'ruptura_concreto']||REPORT_TEMPLATES.outro;const p=ntecSelectedProject();const next=(tpl.label||'Relatório técnico')+(p?' — '+p.name:'');if(!reportTitleWasEdited||!el.value||el.value===lastAutoReportTitle){el.value=next;lastAutoReportTitle=next;reportTitleWasEdited=false;}}\nfunction ntecNextSeries(projectId){const values=reports.filter(r=>String(r.project_id)===String(projectId)).map(r=>Number.parseInt(r.structured_data?.fields?.series,10)).filter(n=>Number.isInteger(n)&&n>0);return values.length?Math.max(...values)+1:1;}\nfunction ntecSetSeriesForWork(force=false){const e=document.querySelector('#reporttemplatefields [data-report-field=\"series\"]');if(!e)return;e.readOnly=false;e.disabled=false;if(!force&&e.dataset.ntecManualSeries==='1')return;const projectId=document.getElementById('reportproject')?.value;e.value=String(projectId?ntecNextSeries(projectId):1);e.dataset.ntecAutoSeries='1';e.dataset.ntecLastAutoSeries=e.value;e.dataset.ntecManualSeries='0';}\nfunction updateReportNumberPreview(){const el=document.getElementById('reportnumber');if(!el)return;const p=ntecSelectedProject();if(!p){el.value='';el.placeholder='Gerado ao selecionar obra e salvar';return;}const prefix='OBRA'+String(p.work_number||'').padStart(3,'0')+'-REL-';const used=reports.filter(r=>String(r.project_id)===String(p.id)).map(r=>String(r.report_number||'')).filter(n=>n.startsWith(prefix)).map(n=>Number(n.slice(prefix.length))).filter(n=>Number.isInteger(n)&&n>0);const next=(used.length?Math.max(...used):0)+1;el.value=prefix+String(next).padStart(4,'0');el.placeholder='Número previsto; definitivo ao salvar';}\n(function initReportTemplates(){",'setup de título')
rx(r"\(function initReportTemplates\(\)\{const sel=document\.getElementById\('reporttype'\);if\(!sel\)return;sel\.innerHTML=.*?renderReportTemplateFields\(\);\}\)\(\);",
"""(function initReportTemplates(){const sel=document.getElementById('reporttype');if(!sel)return;sel.innerHTML=Object.entries(REPORT_TEMPLATES).map(([value,t])=>'<option value="'+esc(value)+'">'+esc(t.label)+'</option>').join('');sel.value='ruptura_concreto';sel.addEventListener('change',()=>{reportTitleWasEdited=false;renderReportTemplateFields();updateReportTitleAuto();updateReportNumberPreview();ntecSetSeriesForWork(true);ntecWireNarrative();ntecGenerateNarrative(true)});document.getElementById('reportproject')?.addEventListener('change',()=>{updateReportTitleAuto();updateReportNumberPreview();ntecSetSeriesForWork(true);ntecGenerateNarrative(false)});document.getElementById('reporttitle')?.addEventListener('input',()=>{if(document.getElementById('reporttitle').value!==lastAutoReportTitle)reportTitleWasEdited=true});renderReportTemplateFields();updateReportTitleAuto();updateReportNumberPreview();ntecSetSeriesForWork(true);ntecWireNarrative();ntecGenerateNarrative(true)})();""",'eventos de título')
marker='function renderReportTemplateFields(values={})'
calc=r'''const ntecOriginalMatrixDefinition = matrixDefinition;
matrixDefinition = function(name){
 const def = ntecOriginalMatrixDefinition.apply(this, arguments);
 const type = document.getElementById('reporttype')?.value || '';
 const tfTypes = ['ruptura_concreto','testemunhos_concreto','prismas_alvenaria','blocos_concreto','graute_alvenaria'];
 if (name === 'primary' && tfTypes.includes(type) && def && Array.isArray(def.columns)) {
   def.columns = def.columns.map(col => {
     const label = String(col);
     return /carga/i.test(label) && /k\s*n/i.test(label) ? label.replace(/k\s*n/ig, 'tf') : col;
   });
 }
 return def;
};
function ntecNum(v){if(v==null)return NaN;const s=String(v).trim().replace(/\s/g,'').replace(/\.(?=\d{3}(?:\D|$))/g,'').replace(',','.');const m=s.match(/-?\d+(?:\.\d+)?/);return m?Number(m[0]):NaN}
function ntecFmt(n,d=2){return Number.isFinite(n)?n.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d}):''}
function ntecHeader(h){return String(h).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')}
function ntecIdx(cols,terms){const headers=cols.map(ntecHeader);for(const term of terms){const exact=headers.findIndex(h=>h===ntecHeader(term));if(exact>=0)return exact}return headers.findIndex(h=>terms.some(t=>h.includes(ntecHeader(t))))}
function ntecValue(row,i){const e=row.querySelector('[data-matrix-cell="'+i+'"]');return e?e.value:''}
function ntecOutput(row,i,n,d=2){if(i<0)return;const e=row.querySelector('[data-matrix-cell="'+i+'"]');if(e){e.value=Number.isFinite(n)?ntecFmt(n,d):'';e.readOnly=true;e.dataset.computed='1'}}
function ntecPair(v){const a=String(v||'').match(/\d+(?:[.,]\d+)?/g);return a&&a.length>=2?[Number(a[0].replace(',','.')),Number(a[1].replace(',','.'))]:null}
function ntecComputed(name){const t=document.getElementById('reporttype')?.value||'';if(name&&name!=='primary')return (t==='blocos_concreto'&&name==='absorption_matrix')?[5,6]:[];return ({ruptura_concreto:[2,4],testemunhos_concreto:[5,7],prismas_alvenaria:[5],blocos_concreto:[5,7],aderencia_argamassa:[3],teor_ar_concreto:[9,11],compressao_argamassa:[4,6],graute_alvenaria:[5],pastilha_mct:[4],inspecao_solo_trado:[3],spt:[5]})[t]||[]}
function ntecRecalc(row,name){const t=document.getElementById('reporttype')?.value||'',def=matrixDefinition(name||'primary');if(!def)return;const cols=def.columns,ix=q=>ntecIdx(cols,q),v=q=>ntecNum(ntecValue(row,ix(q))),put=(q,n,d=2)=>ntecOutput(row,ix(q),n,d);if(name&&name!=='primary'){if(t==='blocos_concreto'&&name==='absorption_matrix'){const tested=v(['massa no ensaio (g)']),dry=v(['massa seca (g)']),sat=v(['massa saturada (g)']);put(['absorção (%)'],dry>0&&Number.isFinite(sat)?(sat-dry)/dry*100:NaN);put(['umidade relativa (%)'],dry>0&&Number.isFinite(tested)?(tested-dry)/dry*100:NaN)}return}const press=v(['carga (tf)','carga (kn)']),isTf=ix(['carga (tf)'])>=0,kn=Number.isFinite(press)?press*(isTf?9.80665:1):NaN;
 if(t==='ruptura_concreto'){const dim=ntecPair(document.querySelector('[data-report-field="specimen_dimensions"]')?.value),ageIdx=ix(['idade (dias)']),ruptIdx=ix(['data de ruptura']),cast=document.querySelector('[data-report-field="casting_date"]')?.value,age=ntecNum(ntecValue(row,ageIdx)),ruptOut=row.querySelector('[data-matrix-cell="'+ruptIdx+'"]');if(ruptOut){ruptOut.readOnly=true;ruptOut.dataset.computed='1';if(cast&&Number.isFinite(age)&&age>=0){const base=new Date(cast+'T12:00:00');base.setDate(base.getDate()+Math.round(age));ruptOut.value=Number.isNaN(base.getTime())?'':String(base.getDate()).padStart(2,'0')+'/'+String(base.getMonth()+1).padStart(2,'0')+'/'+base.getFullYear()}else{ruptOut.value=''}}let fc=NaN;if(dim&&dim[0]>0&&dim[1]>0&&Number.isFinite(kn)){const ratio=dim[1]/dim[0],tab=[[1,.87],[1.25,.93],[1.5,.96],[1.75,.98],[2,1]];let c=ratio>=2?1:NaN;for(let j=1;j<tab.length;j++)if(ratio>=tab[j-1][0]&&ratio<=tab[j][0]){c=tab[j-1][1]+(ratio-tab[j-1][0])*(tab[j][1]-tab[j-1][1])/(tab[j][0]-tab[j-1][0]);break}if(Number.isFinite(c))fc=kn*1000/(Math.PI*dim[0]*dim[0]/4)*c}put(['resistencia (mpa)'],fc)}
 else if(t==='testemunhos_concreto'){const d=v(['diametro (mm)']),fc=d>0&&Number.isFinite(kn)?kn*1000/(Math.PI*d*d/4):NaN;put(['resistencia medida (mpa)'],fc);const f=v(['fator de correcao aplicado']);put(['resultado corrigido (mpa)'],Number.isFinite(fc)&&Number.isFinite(f)?fc*f:NaN)}
 else if(t==='prismas_alvenaria'||t==='graute_alvenaria'){const dim=ntecPair(ntecValue(row,ix(['dimensoes / condicao','dimensoes']))),area=dim&&dim[0]>0&&dim[1]>0?dim[0]*dim[1]:NaN;put(['resistencia (mpa)','resistencia medida (mpa)'],Number.isFinite(area)&&area>0&&Number.isFinite(kn)?kn*1000/area:NaN)}
 else if(t==='blocos_concreto'){const l=v(['comprimento (mm)']),b=v(['largura (mm)']),area=l>0&&b>0?l*b:NaN;put(['area bruta (mm²)','area bruta'],area,1);put(['resistencia individual (mpa)'],area>0&&Number.isFinite(kn)?kn*1000/area:NaN)}
 else if(t==='aderencia_argamassa'){const f=v(['carga (n)']),a=v(['secao (mm²)','secao']);put(['tensao (mpa)'],Number.isFinite(f)&&a>0?f/a:NaN)}
 else if(t==='teor_ar_concreto'){const tot=v(['concreto + tara (g)']),tare=v(['tara (g)']),mass=Number.isFinite(tot)&&Number.isFinite(tare)?tot-tare:NaN;put(['concreto fresco (g)'],mass,1);const vol=v(['volume (l)']);put(['massa especifica (kg/l)'],Number.isFinite(mass)&&vol>0?mass/1000/vol:NaN,3)}
 else if(t==='compressao_argamassa'){const flex=v(['carga flexao (n)']),comp=v(['carga compressao (n)']);put(['resistencia flexao (mpa)'],Number.isFinite(flex)?1.5*flex*100/(40**3):NaN);put(['resistencia compressao (mpa)'],Number.isFinite(comp)?comp/1600:NaN)}
 else if(t==='pastilha_mct'){const a=[v(['leitura a 0']),v(['leitura a 120']),v(['leitura a 240'])];put(['media (mm)'],a.every(Number.isFinite)?a.reduce((x,y)=>x+y,0)/3:NaN)}
 else if(t==='inspecao_solo_trado'){const a=v(['inicio (m)']),b=v(['fim (m)']);put(['espessura (m)'],Number.isFinite(a)&&Number.isFinite(b)&&b>=a?b-a:NaN)}
 else if(t==='spt'){const pen=String(ntecValue(row,ix(['penetracao']))).toLowerCase(),nums=pen.match(/\d+(?:[.,]\d+)?/g)?.map(x=>Number(x.replace(',','.')))||[],total=nums.length>=3?nums.slice(0,3).reduce((a,b)=>a+b,0):(/45\s*cm|15\s*[+\/]\s*15\s*[+\/]\s*15/.test(pen)?45:NaN),b2=v(['golpes 2']),b3=v(['golpes 3']);const n=ix(['n-spt']);ntecOutput(row,n,Math.abs(total-45)<.51&&Number.isFinite(b2)&&Number.isFinite(b3)?Math.round(b2+b3):NaN,0)}
}
'''
once(marker,calc+marker,'motor de cálculo')
narrative = r'''function ntecNarrativeFieldEntries(){
 const holder=document.getElementById('reporttemplatefields');
 if(!holder)return [];
 return [...holder.querySelectorAll('[data-report-field]')].map(el=>{
   const box=el.closest('.field'),label=box?.querySelector('label')?.textContent?.trim()||el.dataset.reportField||'Campo';
   let value=String(el.value||'').trim();
   if(!value)return null;
   if(el.type==='date'&&/^\d{4}-\d{2}-\d{2}$/.test(value))value=value.slice(8,10)+'/'+value.slice(5,7)+'/'+value.slice(0,4);
   return {key:el.dataset.reportField,label,value};
 }).filter(Boolean);
}
function ntecNarrativeMatrices(){
 const tpl=REPORT_TEMPLATES[document.getElementById('reporttype')?.value||'']||{};
 const names=['primary'];
 if(tpl.extraMatrix?.name)names.push(tpl.extraMatrix.name);
 const out=[];
 for(const name of names){
   const def=matrixDefinition(name),body=document.querySelector('tbody[data-report-matrix-rows="'+name+'"]');
   if(!def||!body)continue;
   const rows=[...body.querySelectorAll('tr')].map(row=>def.columns.map((col,i)=>({label:String(col),value:String(row.querySelector('[data-matrix-cell="'+i+'"]')?.value||'').trim()})).filter(x=>x.value)).filter(row=>row.length);
   if(rows.length)out.push({name,columns:def.columns,rows});
 }
 return out;
}
function ntecGenerateNarrative(force=false){
 const type=document.getElementById('reporttype')?.value||'outro';
 const tpl=REPORT_TEMPLATES[type]||REPORT_TEMPLATES.outro||{label:'Relatório técnico',norms:''};
 const project=ntecSelectedProject();
 const title=String(document.getElementById('reporttitle')?.value||tpl.label||'Relatório técnico').trim();
 const date=String(document.getElementById('reportdate')?.value||ntecToday());
 const pdate=/^\d{4}-\d{2}-\d{2}$/.test(date)?date.slice(8,10)+'/'+date.slice(5,7)+'/'+date.slice(0,4):date;
 const norm=String(document.getElementById('reportnormativerefs')?.value||tpl.norms||'').trim();
 const entries=ntecNarrativeFieldEntries();
 const core=entries.filter(x=>!['equipment','calibration','operator','meter_type','apparatus'].includes(x.key));
 const equipment=entries.filter(x=>['equipment','calibration','operator','meter_type','apparatus'].includes(x.key));
 const matrices=ntecNarrativeMatrices();
 const matrixLines=[];
 let resistanceValues=[];
 for(const mat of matrices){
   mat.rows.forEach((row,i)=>{
     matrixLines.push((mat.name==='primary'?'Registro '+(i+1):'Registro complementar '+(i+1))+': '+row.map(x=>x.label+': '+x.value).join('; ')+'.');
   });
   const ri=mat.columns.findIndex(h=>{const t=ntecHeader(h);return t.includes('resistencia')&&t.includes('mpa')&&!t.includes('corrigida')});
   if(ri>=0)for(const row of mat.rows){const val=ntecNum(row[ri]?.value);if(Number.isFinite(val))resistanceValues.push(val);}
 }
 const client=project?.clients?.company_name||'cliente não informado';
 const work=project?.name||'obra não selecionada';
 const workNum=project?.work_number?'OBRA'+String(project.work_number).padStart(3,'0'):'';
 const fieldSentence=core.length?'Dados registrados: '+core.map(x=>x.label+': '+x.value).join('; ')+'.':'Não foram fornecidos dados complementares de identificação da amostra.';
 const content='Este relatório técnico registra o serviço "'+(tpl.label||'ensaio técnico')+'" realizado para '+client+', na obra "'+work+'"'+(workNum?' ('+workNum+')':'')+'. Data do relatório: '+pdate+'. '+fieldSentence+' O escopo e a identificação apresentados foram montados automaticamente a partir dos campos preenchidos nesta ficha.';
 const equipmentSentence=equipment.length?' Equipamento e registros informados: '+equipment.map(x=>x.label+': '+x.value).join('; ')+'.':'';
 const method='Modelo de procedimento: '+(tpl.label||'ensaio técnico')+'. Referências normativas sugeridas no modelo: '+(norm||'não cadastradas para este modelo')+'.'+equipmentSentence+' A equipe deve confirmar que a edição da norma, a preparação das amostras, as condições de ensaio, os equipamentos e o procedimento efetivamente executado correspondem ao serviço realizado. Este texto foi elaborado automaticamente a partir do modelo selecionado e não comprova, por si só, a execução integral de qualquer norma.';
 let results;
 if(matrixLines.length){
   results='Dados de ensaio registrados na ficha:\n'+matrixLines.join('\n');
   if(resistanceValues.length){
     const avg=resistanceValues.reduce((a,b)=>a+b,0)/resistanceValues.length;
     results+='\nResumo numérico das resistências informadas/calculadas: '+resistanceValues.length+' resultado(s); média aritmética '+ntecFmt(avg,2)+' MPa; mínimo '+ntecFmt(Math.min(...resistanceValues),2)+' MPa; máximo '+ntecFmt(Math.max(...resistanceValues),2)+' MPa.';
   }
 } else {
   results='Os resultados serão descritos a partir das leituras registradas na tabela de ensaio. Nenhuma leitura foi presumida ou criada automaticamente.';
 }
 let conclusion;
 if(matrixLines.length){
   conclusion='Foram organizados automaticamente '+matrixLines.length+' registro(s) com os valores disponíveis na ficha. '+(resistanceValues.length?'A série de resistência apresenta média aritmética de '+ntecFmt(resistanceValues.reduce((a,b)=>a+b,0)/resistanceValues.length,2)+' MPa, com valores entre '+ntecFmt(Math.min(...resistanceValues),2)+' e '+ntecFmt(Math.max(...resistanceValues),2)+' MPa. ':'')+'A avaliação de atendimento ou não atendimento deve considerar os critérios de aceitação da norma vigente, o projeto/especificação, a idade do ensaio e o plano de amostragem aplicável. O sistema não declara aprovação ou reprovação automaticamente. Revisão e validação do responsável técnico são necessárias antes da emissão.';
 } else {
   conclusion='A conclusão técnica final deve ser definida após o registro e a conferência dos resultados medidos, dos critérios de aceitação aplicáveis e dos requisitos do projeto. O sistema não presume resultados nem declara conformidade automaticamente. Revisão e validação do responsável técnico são necessárias antes da emissão.';
 }
 const generated={reportcontent:content,reportmethod:method,reportresults:results,reportobservations:conclusion};
 for(const [id,value] of Object.entries(generated)){
   const el=document.getElementById(id);
   if(!el)continue;
   if(force||!el.dataset.ntecManual||el.value===el.dataset.ntecLastGenerated){
     el.value=value;
     el.dataset.ntecLastGenerated=value;
     el.dataset.ntecGenerated='1';
   }
 }
}
function ntecWireNarrative(){
 const form=document.getElementById('reportform');
 if(!form||form.dataset.ntecNarrativeWired==='1')return;
 form.dataset.ntecNarrativeWired='1';
 form.addEventListener('input',e=>{
   const el=e.target;
   if(el.matches('#reportcontent,#reportmethod,#reportresults,#reportobservations')){
     el.dataset.ntecManual='1';
     return;
   }
   ntecGenerateNarrative(false);
 });
 form.addEventListener('change',e=>{
   const el=e.target;
   if(el.matches('#reportcontent,#reportmethod,#reportresults,#reportobservations')){
     el.dataset.ntecManual='1';
     return;
   }
   ntecGenerateNarrative(false);
 });
}
document.getElementById('reportform')?.addEventListener('toggle',()=>ntecGenerateNarrative(false));
'''
once(marker,narrative+marker,'gerador automático da redação técnica')
rx(r"function addReportMatrixRow\(name,values=\[\]\)\{.*?\}\s*function collectMatrixText",
"""function addReportMatrixRow(name,values=[]){const def=matrixDefinition(name),body=document.querySelector('[data-report-matrix-rows="'+name+'"]');if(!def||!body)return;const tr=document.createElement('tr'),computed=ntecComputed(name);tr.innerHTML=def.columns.map((col,i)=>'<td><input type="text" inputmode="decimal" data-matrix-cell="'+i+'" aria-label="'+esc(col)+'" title="'+esc(col)+'" placeholder="'+esc(col)+'" value="'+esc(values[i]??'')+'" '+(computed.includes(i)?'readonly data-computed="1"':'')+'></td>').join('')+'<td><button type="button" class="btn matrix-delete" aria-label="Remover linha" title="Remover linha" onclick="this.closest(\\'tr\\').remove()">×</button></td>';body.appendChild(tr);ntecRecalc(tr,name)}
function collectMatrixText""",'linhas calculadas')
rx(r"function collectMatrixText\(name\)\{.*?\}\s*function reportMatrixHasData",
"""function collectMatrixText(name){const body=document.querySelector('[data-report-matrix-rows="'+name+'"]');if(!body)return '';return [...body.querySelectorAll('tr')].filter(tr=>[...tr.querySelectorAll('[data-matrix-cell]')].some(e=>!e.readOnly&&String(e.value||'').trim())).map(tr=>{ntecRecalc(tr,name);return [...tr.querySelectorAll('[data-matrix-cell]')].map(e=>String(e.value||'').replaceAll('|','/').trim()).join(' | ')}).join(String.fromCharCode(10))}
function reportMatrixHasData""",'captura de resultados')
once("const norm=document.getElementById('reportnormativerefs');if(norm)norm.value=tpl.norms||'';}","const norm=document.getElementById('reportnormativerefs');if(norm)norm.value=tpl.norms||'';holder?.querySelectorAll('[data-report-field]').forEach(el=>{const k=el.dataset.reportField;if(['equipment','calibration','apparatus','container_volume','meter_type','operator'].includes(k)&&!String(el.value||'').trim()){try{el.value=localStorage.getItem('ntec.report.default.'+k)||''}catch(_){}}});holder?.querySelectorAll('tbody[data-report-matrix-rows]').forEach(b=>b.querySelectorAll('tr').forEach(row=>ntecRecalc(row,b.dataset.reportMatrixRows)));if(holder&&!holder.querySelector('.report-computation-note')){const n=document.createElement('div');n.className='report-computation-note';n.textContent=document.getElementById('reporttype')?.value==='ruptura_concreto'?'Como preencher: informe a data de moldagem e a idade de cada CP (ex.: 7 ou 28 dias). A data de ruptura é calculada automaticamente. Digite a carga da prensa em tf; a resistência sai em MPa.':'Como preencher: informe os valores medidos. O sistema calcula as colunas destacadas; confira os resultados antes de emitir.';holder.appendChild(n)}}",'preenchimento automático')
listeners="""document.getElementById('reporttemplatefields')?.addEventListener('input',e=>{const el=e.target;if(el.matches('[data-report-field]')&&['equipment','calibration','apparatus','container_volume','meter_type','operator'].includes(el.dataset.reportField)){try{localStorage.setItem('ntec.report.default.'+el.dataset.reportField,el.value)}catch(_){}}if(el.matches('[data-report-field="series"]'))el.dataset.ntecManualSeries='1';if(el.matches('[data-report-field="casting_date"]'))document.querySelectorAll('tbody[data-report-matrix-rows="primary"] tr').forEach(row=>ntecRecalc(row,'primary'));const row=el.closest('tr'),body=row?.closest('tbody[data-report-matrix-rows]');if(row&&body)ntecRecalc(row,body.dataset.reportMatrixRows)});\ndocument.getElementById('reporttemplatefields')?.addEventListener('change',e=>{const el=e.target;if(el.matches('[data-report-field]')&&['equipment','calibration','apparatus','container_volume','meter_type','operator'].includes(el.dataset.reportField)){try{localStorage.setItem('ntec.report.default.'+el.dataset.reportField,el.value)}catch(_){}}if(el.matches('[data-report-field="series"]'))el.dataset.ntecManualSeries='1';if(el.matches('[data-report-field="casting_date"]'))document.querySelectorAll('tbody[data-report-matrix-rows="primary"] tr').forEach(row=>ntecRecalc(row,'primary'));const row=el.closest('tr'),body=row?.closest('tbody[data-report-matrix-rows]');if(row&&body)ntecRecalc(row,body.dataset.reportMatrixRows)});\n"""
once('function collectReportStructuredData()',listeners+'function collectReportStructuredData()','armazenamento dos equipamentos')
once(".map(r=>({...r,structured_data:r.structured_data||{},normative_references:r.normative_references||'',client:r.projects?.clients?.company_name||'Cliente',project:r.projects?.name||'Obra',typeLabel:reportTypeLabel(r.report_type),statusLabel:",".map(r=>({...r,structured_data:r.structured_data||{},normative_references:r.normative_references||'',client:r.projects?.clients?.company_name||'Cliente',project:r.projects?.name||'Obra',work_number:r.projects?.work_number||null,typeLabel:reportTypeLabel(r.report_type),statusLabel:",'mapeamento da obra do relatório')
rx(r"function clearReportForm\(\)\{.*?\}\s*async function addReport",
"""function clearReportForm(){['reporttitle','reportcontent','reportmethod','reportresults','reportobservations','reportresponsible','reportregistration'].forEach(id=>{const el=document.getElementById(id);if(el){el.value='';delete el.dataset.ntecManual;delete el.dataset.ntecLastGenerated;delete el.dataset.ntecGenerated;}});const d=document.getElementById('reportdate');if(d)d.value=ntecToday();const n=document.getElementById('reportnumber');if(n)n.value='';const p=document.getElementById('reportproject');if(p)p.value='';reportTitleWasEdited=false;lastAutoReportTitle='';renderReportTemplateFields();updateReportTitleAuto();updateReportNumberPreview();ntecSetSeriesForWork(true);ntecWireNarrative();ntecGenerateNarrative(true)}
async function addReport""",'limpeza de formulário')
rx(r"async function addReport\(\)\{.*?\}\s*function renderReports",
"""async function addReport(){ntecGenerateNarrative(false);const projectId=document.getElementById('reportproject').value,title=document.getElementById('reporttitle').value.trim(),type=document.getElementById('reporttype').value,tpl=REPORT_TEMPLATES[type]||REPORT_TEMPLATES.outro;if(!projectId||!title)return alert('Selecione a obra e confira o título do relatório.');for(const f of (tpl.fields||[])){const el=document.querySelector('#reporttemplatefields [data-report-field="'+f.name+'"]');if(f.required&&el&&!String(el.value||'').trim()){el.focus();return alert('Preencha o campo obrigatório: '+f.label)}}if(tpl.matrix?.required&&!reportMatrixHasData('primary'))return alert('Preencha pelo menos uma linha em: '+tpl.matrix.label);if(tpl.extraMatrix?.required&&!reportMatrixHasData(tpl.extraMatrix.name))return alert('Preencha pelo menos uma linha em: '+tpl.extraMatrix.label);const btn=document.querySelector('#reportform button.btn.primary');if(btn){btn.disabled=true;btn.textContent='Salvando…'}try{const saved=await window.NTEC_SUPABASE.saveReport({projectId,title,type,date:document.getElementById('reportdate').value,content:document.getElementById('reportcontent').value,methodology:document.getElementById('reportmethod').value,results:document.getElementById('reportresults').value,observations:document.getElementById('reportobservations').value,technicalResponsible:document.getElementById('reportresponsible').value,professionalRegistration:document.getElementById('reportregistration').value,normativeReferences:document.getElementById('reportnormativerefs').value,structuredData:collectReportStructuredData()});const exact=saved?.reportNumber||'';reports=await window.NTEC_SUPABASE.loadReports();renderReports();clearReportForm();closeForm('reportform');alert('Relatório '+exact+' salvo como rascunho. Confira cálculos, unidades e referência normativa antes de emitir.')}catch(err){alert('Não foi possível salvar o relatório: '+(err?.message||'erro desconhecido'))}finally{if(btn){btn.disabled=false;btn.textContent='Salvar relatório no banco'}}}
function renderReports""",'salvamento do relatório')
rx(r"function renderReports\(\)\{.*?\}\s*function matrixHtml",
"""function renderReports(){document.getElementById('reportsbody').innerHTML=reports.length?reports.map(r=>'<tr><td><strong>'+esc(r.report_number||'Número pendente')+'</strong><div>'+esc(r.title)+'</div><div class="muted small">'+esc(r.normative_references?'Referências registradas':'Referências pendentes')+'</div></td><td>'+esc(r.client)+'<div class="muted small">'+esc(r.project)+'</div></td><td>'+esc(r.typeLabel||r.report_type)+'</td><td>'+esc(r.report_date||'—')+'</td><td>'+badge(r.statusLabel||r.status||'Rascunho')+'</td><td><button class="btn" onclick="editReport(\\''+esc(r.id)+'\\')">Editar</button> <button class="btn" onclick="printNtecReport(\\''+esc(r.id)+'\\')">PDF</button></td></tr>').join(''):'<tr><td colspan="6" class="empty">Nenhum relatório técnico cadastrado no banco.</td></tr>'}
function matrixHtml""",'lista com número')
old="<b>Obra:</b> "+chr(36)+"{esc(r.project)}<br><b>Tipo:</b>"
new="<b>Obra:</b> "+chr(36)+"{esc(r.project)}<br><b>Número do relatório:</b> "+chr(36)+"{esc(r.report_number||'—')}<br><b>Tipo:</b>"
if old not in s: raise SystemExit("trecho de impressão não encontrado")
s=s.replace(old,new,1)
# Print report PDFs in A4 portrait with a compact, readable technical layout.
old_print_layout='@media print{button{display:none}body{margin:12mm}}</style></head><body><header><h1>NTEC ENGENHARIA &amp; GEOTECNIA</h1><div>RELATÓRIO TÉCNICO / RELATÓRIO DE ENSAIO</div></header>'
new_print_layout='@page{size:A4 portrait;margin:14mm 13mm 16mm}body{font:12px Arial,sans-serif;color:#172536;margin:0 auto;max-width:180mm;line-height:1.42}header{border-bottom:2px solid #e3b34f;padding-bottom:10px;margin-bottom:14px}header h1{color:#10263f;font-size:19px;margin:0 0 5px}header div{font-size:11px;color:#526579;font-weight:700;letter-spacing:.25px}h2{color:#1f5f91;font-size:12px;margin:15px 0 6px;break-after:avoid;page-break-after:avoid}.meta{background:#f8fafc;padding:8px;border:1px solid #d8e0e8;border-radius:4px;white-space:pre-wrap;overflow-wrap:anywhere}.sign{display:flex;gap:18mm;margin-top:26mm;break-inside:avoid;page-break-inside:avoid}.sign div{border-top:1px solid #333;width:50%;padding-top:7px;text-align:center;overflow-wrap:anywhere}.report-data-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.report-data-item{border:1px solid #d8e0e8;padding:6px;overflow-wrap:anywhere;break-inside:avoid;page-break-inside:avoid}.report-data-item strong{display:block;font-size:9px;text-transform:uppercase;color:#667586;margin-bottom:3px}.report-data-table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:9px;margin:7px 0;page-break-inside:auto}.report-data-table thead{display:table-header-group}.report-data-table tr{break-inside:avoid;page-break-inside:avoid}.report-data-table th,.report-data-table td{border:1px solid #bfc9d3;padding:4px;text-align:left;vertical-align:top;overflow-wrap:anywhere;word-break:normal}.report-data-table th{background:#edf2f6}button{border:1px solid #ccd5df;background:#fff;border-radius:4px;padding:7px 10px}@media print{html,body{width:auto!important;min-height:0!important}body{margin:0!important;max-width:none!important;font-size:10pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}button{display:none!important}header,h2{break-after:avoid;page-break-after:avoid}.meta,.report-data-item,.sign{break-inside:avoid;page-break-inside:avoid}.report-data-table{width:100%;table-layout:fixed;font-size:8pt}.report-data-table th,.report-data-table td{padding:3px}.sign{margin-top:22mm}}@media screen{body{padding:10mm 0}} </style></head><body><header><h1>NTEC ENGENHARIA &amp; GEOTECNIA</h1><div>${esc(r.typeLabel||r.report_type||"Relatório técnico")}</div></header>'
if s.count(old_print_layout)!=1: raise SystemExit('Layout original de impressão não encontrado exatamente uma vez')
s=s.replace(old_print_layout,new_print_layout,1)
old_print_title='<title>${esc(r.title)}</title>'
new_print_title='<title>${esc(r.title||r.typeLabel||r.report_type||"Relatório técnico")}</title>'
if s.count(old_print_title)!=1: raise SystemExit("Título PDF do relatório não encontrado exatamente uma vez")
s=s.replace(old_print_title,new_print_title,1)
old_print_heading='<h2>${esc(r.title)}</h2>'
new_print_heading='<h2>${esc(r.title||r.typeLabel||r.report_type||"Relatório técnico")}</h2>'
if s.count(old_print_heading)!=1: raise SystemExit("Título interno do PDF não encontrado exatamente uma vez")
s=s.replace(old_print_heading,new_print_heading,1)
once("function openForm(id){document.getElementById(id).classList.remove('hidden');document.getElementById(id).scrollIntoView({behavior:'smooth',block:'nearest'});if(id==='reportform')renderReportTemplateFields()}","function openForm(id){document.getElementById(id).classList.remove('hidden');document.getElementById(id).scrollIntoView({behavior:'smooth',block:'nearest'});if(id==='reportform'){const d=document.getElementById('reportdate');if(d&&!d.value)d.value=ntecToday();renderReportTemplateFields();updateReportTitleAuto();updateReportNumberPreview();ntecWireNarrative();ntecGenerateNarrative(false)}}",'início da ficha')
if 'id="ntec-forgot-password"' not in s:
 once('<button class="auth-toggle" id="ntec-show-signup" type="button">Sou cliente — criar acesso</button>','<button class="auth-toggle" id="ntec-show-signup" type="button">Sou cliente — criar acesso</button><a id="ntec-forgot-password" href="../recuperar-acesso.html" style="display:block;margin-top:12px;text-align:center;color:#1f5f91;font-size:13px">Esqueci minha senha</a>','link esqueci senha')
for word in ['work_number','report_number','ntecRecalc','localStorage.setItem','signInWithPassword']:
 if word not in s: raise SystemExit('Validação falhou: '+word)
if s.count('function addReportMatrixRow(')!=1: raise SystemExit('Há função duplicada de linha da tabela')
p.write_text(s,encoding='utf-8')
print('Applied NTEC report enhancements to '+str(p))
