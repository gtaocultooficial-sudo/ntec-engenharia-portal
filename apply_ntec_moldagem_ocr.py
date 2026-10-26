#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/admin/index.html")
s = path.read_text(encoding="utf-8")
anchor = '<div class="field"><label>Número do relatório (automático)</label>'
if s.count(anchor) != 1:
    raise SystemExit("Não encontrei o ponto único do formulário para inserir leitura de ficha de moldagem.")

panel = r"""
<div id="ntec-moldagem-ocr" class="ntec-ocr-card">
  <h3>Importar ficha de moldagem</h3>
  <p>Envie uma foto, imagem ou PDF. A leitura automática é uma sugestão: confira os dados reconhecidos antes de salvar o relatório.</p>
  <div class="ntec-ocr-controls">
    <input id="ntec-ocr-file" type="file" accept="image/*,.pdf,application/pdf">
    <button type="button" class="btn secondary" id="ntec-ocr-read">Ler ficha e sugerir preenchimento</button>
  </div>
  <div id="ntec-ocr-status" role="status" aria-live="polite">Aceita foto de celular, imagem digitalizada ou PDF.</div>
  <label for="ntec-ocr-text">Texto reconhecido (confira e corrija antes de aplicar)</label>
  <textarea id="ntec-ocr-text" rows="7" placeholder="O texto extraído da ficha aparecerá aqui para conferência."></textarea>
  <button type="button" class="btn secondary" id="ntec-ocr-apply">Aplicar sugestões aos campos</button>
  <hr>
  <h4>Conferência dos corpos de prova (CPs)</h4>
  <p>Cada linha da ficha original representa uma série de moldagem. Use o <b>nº da série de controle</b> para vincular a série à obra e manter a sequência; não cadastre a série de campo, que permanece zerada. Informe cada CP da série, sua idade e data prevista de ruptura. A previsão não é a data real do ensaio; os resultados podem ser lançados depois, inclusive parcialmente.</p>
  <div class="ntec-ocr-controls"><button type="button" class="btn secondary" id="ntec-cp-add">+ Adicionar CP</button><button type="button" class="btn secondary" id="ntec-cp-transfer">Transferir CPs conferidos para o relatório</button></div>
  <div class="ntec-cp-table-wrap"><table class="ntec-cp-table"><thead><tr><th>Nº da série de controle</th><th>Identificação do CP</th><th>Idade (dias)</th><th>Data prevista</th><th>Carga real (tf), se ensaiado</th><th></th></tr></thead><tbody id="ntec-cp-rows"></tbody></table></div>
  <small>Não preenchemos automaticamente números duvidosos da escrita manual. Os resultados reais de ruptura devem ser lançados somente após o ensaio.</small>
  <small>O arquivo é processado no navegador e não é enviado a um serviço externo de OCR. É necessária conexão para carregar as bibliotecas de leitura.</small>
</div>
<style>
.ntec-ocr-card{border:1px solid var(--line);border-radius:12px;padding:15px;margin:0 0 16px;background:#f7fafc}
.ntec-ocr-card h3{margin:0 0 6px;color:var(--navy);font-size:16px}
.ntec-ocr-card h4{margin:12px 0 5px;color:var(--navy);font-size:14px}
.ntec-cp-table-wrap{overflow-x:auto;margin:8px 0}
.ntec-cp-table{width:100%;border-collapse:collapse;min-width:620px}
.ntec-cp-table th,.ntec-cp-table td{border:1px solid #d5dee7;padding:6px;text-align:left;font-size:12px}
.ntec-cp-table th{background:#eaf0f5}
.ntec-cp-table input{width:100%;min-width:85px;padding:7px;border:1px solid #cbd6e1;border-radius:5px;box-sizing:border-box}
.ntec-cp-table input[data-cp-date="1"]{background:#eef5fb}
.ntec-ocr-card p,.ntec-ocr-card small{display:block;color:#526579;font-size:12px;line-height:1.5}
.ntec-ocr-controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
.ntec-ocr-card input[type=file]{max-width:100%;padding:8px}
.ntec-ocr-card textarea{width:100%;box-sizing:border-box;margin:6px 0 10px}
#ntec-ocr-status{font-size:12px;font-weight:700;margin:8px 0;color:#29465f}
</style>
<script>
(function(){
 const fileEl=document.getElementById('ntec-ocr-file'), readBtn=document.getElementById('ntec-ocr-read'),
 statusEl=document.getElementById('ntec-ocr-status'), textEl=document.getElementById('ntec-ocr-text'),
 applyBtn=document.getElementById('ntec-ocr-apply');
 if(!fileEl||!readBtn||!textEl)return;
 const status=t=>statusEl.textContent=t;
 function loadScript(src,test){
   if(test())return Promise.resolve();
   return new Promise((resolve,reject)=>{
     let el=document.querySelector('script[data-ntec-ocr-lib="'+src+'"]');
     if(el){el.addEventListener('load',resolve,{once:true});el.addEventListener('error',reject,{once:true});return;}
     el=document.createElement('script');el.src=src;el.async=true;el.dataset.ntecOcrLib=src;
     el.onload=resolve;el.onerror=()=>reject(new Error('Não foi possível carregar a biblioteca de leitura.'));
     document.head.appendChild(el);
   });
 }
 function makeOcrVariants(source){
   const variants=[];
   for(const angle of [0,90,180,270]){
     const rotated=document.createElement('canvas'),ctx=rotated.getContext('2d');
     const sw=source.width,sh=source.height;
     rotated.width=(angle===90||angle===270)?sh:sw;
     rotated.height=(angle===90||angle===270)?sw:sh;
     ctx.translate(rotated.width/2,rotated.height/2);ctx.rotate(angle*Math.PI/180);ctx.drawImage(source,-sw/2,-sh/2);
     const scale=Math.min(2.2,3200/Math.max(rotated.width,rotated.height));
     const enlarged=document.createElement('canvas');enlarged.width=Math.round(rotated.width*scale);enlarged.height=Math.round(rotated.height*scale);
     const ectx=enlarged.getContext('2d');ectx.drawImage(rotated,0,0,enlarged.width,enlarged.height);
     const img=ectx.getImageData(0,0,enlarged.width,enlarged.height),d=img.data;
     for(let i=0;i<d.length;i+=4){const gray=0.299*d[i]+0.587*d[i+1]+0.114*d[i+2];const v=Math.max(0,Math.min(255,(gray-128)*1.35+145));d[i]=d[i+1]=d[i+2]=v;}
     ectx.putImageData(img,0,0);variants.push({canvas:enlarged,angle});
   }
   return variants;
 }
 function ocrScore(text,confidence){
   const raw=String(text||''),t=raw.toLowerCase(),terms=['formulario de moldagem','moldagem','concreto','argamassa','graute','codigo da obra','construtora','data','fornecedor','corpo de prova','abatimento','ruptura','resistencia','nota fiscal','volume'];
   let score=terms.reduce((n,w)=>n+(t.includes(w)?6:0),0);
   const words=(raw.match(/[A-Za-zÀ-ÿ]{3,}/g)||[]).length;
   const chars=(raw.match(/[A-Za-zÀ-ÿ]/g)||[]).length;
   const junk=(raw.match(/[|{}~\\[\\]<>]/g)||[]).length;
   score+=Math.min(words,80)*0.18+Math.min(chars/80,8);
   score-=junk*0.35;
   if(Number.isFinite(confidence))score+=confidence*0.12;
   return score;
 }
 async function getPages(file){
   if(!/\.pdf$/i.test(file.name)&&file.type!=='application/pdf'){const bitmap=await createImageBitmap(file);const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;canvas.getContext('2d').drawImage(bitmap,0,0);bitmap.close?.();return [canvas];}
   await loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',()=>!!window.pdfjsLib);
   const pdfjs=window.pdfjsLib;pdfjs.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
   const pdf=await pdfjs.getDocument({data:await file.arrayBuffer()}).promise,pages=[];
   for(let i=1;i<=Math.min(pdf.numPages,12);i++){
     const page=await pdf.getPage(i),viewport=page.getViewport({scale:1.6}),canvas=document.createElement('canvas');
     canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
     await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;pages.push(canvas);
   }
   return pages;
 }
 readBtn.addEventListener('click',async()=>{
   const file=fileEl.files&&fileEl.files[0];if(!file){status('Selecione uma foto, imagem ou PDF primeiro.');return;}
   if(file.size>20*1024*1024){status('Arquivo acima de 20 MB. Reduza o arquivo e tente novamente.');return;}
   readBtn.disabled=true;textEl.value='';
   try{
     status('Carregando leitor de texto…');
     await loadScript('https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js',()=>!!window.Tesseract);
     const pages=await getPages(file);
     status('Preparando o reconhecimento em português…');
     const worker=await Tesseract.createWorker('por+eng',1,{langPath:'https://tessdata.projectnaptha.com/4.0.0',gzip:true,logger:m=>{if(m.status)status('Leitura: '+m.status+(m.progress?' '+Math.round(m.progress*100)+'%':''));}});
     const output=[];
     try{for(let i=0;i<pages.length;i++){status('Preparando página '+(i+1)+' de '+pages.length+'…');const variants=makeOcrVariants(pages[i]);let best={score:-1,text:'',angle:0,mode:'6'};for(const variant of variants){for(const mode of ['6','11','12']){status('Lendo página '+(i+1)+' — rotação '+variant.angle+'°, modo '+mode+'…');await worker.setParameters({tessedit_pageseg_mode:mode});const result=await worker.recognize(variant.canvas);const score=ocrScore(result.data.text,result.data.confidence);if(score>best.score)best={score,text:result.data.text,angle:variant.angle,mode,canvas:variant.canvas};}}const regions=[{name:'CABEÇALHO',from:0,to:0.34,left:0,right:1},{name:'TABELA DE MOLDAGEM E CPs',from:0.25,to:0.82,left:0,right:1},{name:'TABELA — METADE ESQUERDA',from:0.25,to:0.82,left:0,right:0.52},{name:'TABELA — METADE DIREITA',from:0.25,to:0.82,left:0.48,right:1},{name:'TABELA — COLUNAS INICIAIS',from:0.30,to:0.80,left:0,right:0.34},{name:'TABELA — COLUNAS CENTRAIS',from:0.30,to:0.80,left:0.28,right:0.70},{name:'TABELA — COLUNAS FINAIS',from:0.30,to:0.80,left:0.64,right:1},{name:'RODAPÉ E OBSERVAÇÕES',from:0.76,to:1,left:0,right:1}];const regionText=[];for(const region of regions){const crop=document.createElement('canvas');const sx=Math.round(best.canvas.width*region.left),sw=Math.max(1,Math.round(best.canvas.width*(region.right-region.left)));crop.width=sw;crop.height=Math.max(1,Math.round(best.canvas.height*(region.to-region.from)));crop.getContext('2d').drawImage(best.canvas,sx,Math.round(best.canvas.height*region.from),sw,crop.height,0,0,crop.width,crop.height);let regionBest={score:-1,text:'',mode:'6'};for(const mode of ['6','11','12']){status('Refinando página '+(i+1)+' — '+region.name+'…');await worker.setParameters({tessedit_pageseg_mode:mode});const rr=await worker.recognize(crop);const digits=(rr.data.text.match(/[0-9]{2,}/g)||[]).length;const sc=ocrScore(rr.data.text,rr.data.confidence)+(region.name.includes('TABELA')?Math.min(digits,30)*0.3:0);if(sc>regionBest.score)regionBest={score:sc,text:rr.data.text,mode};}regionText.push('--- '+region.name+' (modo '+regionBest.mode+') ---\\n'+regionBest.text);}output.push('--- Página '+(i+1)+' (orientação '+best.angle+'°, modo '+best.mode+') ---\\n'+best.text+'\\n\\n'+regionText.join('\\n\\n'));}}
     finally{await worker.terminate();}
     textEl.value=output.join('\n\n');status('Leitura concluída. Confira o texto; a escrita manual pode gerar erros. Clique em “Aplicar sugestões” para preencher os campos reconhecidos.');
   }catch(e){const detail=(e&&typeof e.message==='string'&&e.message.trim())?e.message:(typeof e==='string'?e:(e&&e.name?e.name+' (verifique conexão, bloqueio de CDN ou formato do arquivo)':String(e)));status('Falha na leitura automática: '+detail+'. Tente JPG/PNG ou PDF menor que 20 MB; se persistir, envie a mensagem exata para diagnóstico.');console.error('NTEC OCR error:',e);}
   finally{readBtn.disabled=false;}
 });
 function cpDateFromAge(age){
   const cast=document.querySelector('[data-report-field="casting_date"]')?.value;
   const n=Number(String(age||'').replace(',','.'));
   if(!cast||!Number.isFinite(n)||n<0)return '';
   const d=new Date(cast+'T12:00:00');d.setDate(d.getDate()+Math.round(n));
   return Number.isNaN(d.getTime())?'':String(d.getDate()).padStart(2,'0')+'/'+String(d.getMonth()+1).padStart(2,'0')+'/'+d.getFullYear();
 }
 function addOcrCpRow(values={}){
   const body=document.getElementById('ntec-cp-rows');if(!body)return;
   const tr=document.createElement('tr');
   tr.innerHTML='<td><input data-cp="series" aria-label="Número da série da ficha" placeholder="Ex.: 01"></td><td><input data-cp="id" aria-label="Identificação do CP" placeholder="Ex.: 01-A"></td><td><input data-cp="age" type="number" min="0" step="1" aria-label="Idade em dias" placeholder="7 / 28"></td><td><input data-cp="date" aria-label="Data prevista de ruptura" placeholder="dd/mm/aaaa"></td><td><input data-cp="load" inputmode="decimal" aria-label="Carga real em tf" placeholder="Só após ensaio"></td><td><button type="button" class="btn secondary" data-cp-remove aria-label="Remover CP">×</button></td>';
   body.appendChild(tr);
   for(const k of ['series','id','age','date','load']){const el=tr.querySelector('[data-cp="'+k+'"]');if(el&&values[k]!=null)el.value=values[k];}
   const date=tr.querySelector('[data-cp="date"]');date.dataset.cpDate='1';
   if(!date.value&&tr.querySelector('[data-cp="age"]').value)date.value=cpDateFromAge(tr.querySelector('[data-cp="age"]').value);
 }
 document.getElementById('ntec-cp-add')?.addEventListener('click',()=>addOcrCpRow());
 document.getElementById('ntec-cp-rows')?.addEventListener('click',e=>{if(e.target.closest('[data-cp-remove]'))e.target.closest('tr')?.remove()});
 document.getElementById('ntec-cp-rows')?.addEventListener('input',e=>{
   if(e.target.matches('[data-cp="age"]')){const row=e.target.closest('tr'),date=row?.querySelector('[data-cp="date"]');if(date&&!date.dataset.manual)date.value=cpDateFromAge(e.target.value);}
   if(e.target.matches('[data-cp="date"]'))e.target.dataset.manual='1';
 });
 document.getElementById('ntec-cp-transfer')?.addEventListener('click',()=>{
   const rows=[...document.querySelectorAll('#ntec-cp-rows tr')].map(tr=>Object.fromEntries(['series','id','age','date','load'].map(k=>[k,String(tr.querySelector('[data-cp="'+k+'"]')?.value||'').trim()])));
   const valid=rows.filter(r=>r.series||r.id||r.age||r.date||r.load);
   if(!valid.length){status('Adicione e confira ao menos um CP antes de transferir.');return;}
   if(document.getElementById('reporttype')?.value!=='ruptura_concreto'){status('Selecione o tipo “Ruptura de concreto” para transferir CPs.');return;}
   if(typeof matrixDefinition!=='function'||typeof addReportMatrixRow!=='function'){status('A tabela do relatório não está disponível. Reabra o formulário e tente novamente.');return;}
   const def=matrixDefinition('primary');if(!def?.columns?.length){status('Não foi possível identificar as colunas do relatório.');return;}
   const normHeader=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
   const idx=terms=>def.columns.findIndex(col=>terms.some(t=>normHeader(col).includes(t)));
   const ix={id:idx(['identificação do cp','identificacao do cp','cp nº','cp n°','cp','amostra']),series:idx(['nº série','numero da serie','série da moldagem','serie da moldagem']),age:idx(['idade']),date:idx(['data de ruptura','ruptura']),load:idx(['carga (tf)','carga de ruptura'])};
   if(ix.id<0||ix.age<0||ix.date<0||ix.load<0){status('As colunas de CP, idade, data de ruptura e carga (tf) não foram encontradas na tabela do relatório. Nada foi transferido.');return;}
   if(ix.series===ix.id)ix.series=-1;
   const existing=[...document.querySelectorAll('tbody[data-report-matrix-rows="primary"] tr')].map(tr=>({id:String(tr.querySelector('[data-matrix-cell="'+ix.id+'"]')?.value||'').trim().toLowerCase(),age:String(tr.querySelector('[data-matrix-cell="'+ix.age+'"]')?.value||'').trim().toLowerCase()}));
   let added=0,skipped=0;
   valid.forEach(r=>{
     const id=String(r.id||'').trim().toLowerCase(),age=String(r.age||'').trim().toLowerCase();
     if((id||age)&&existing.some(x=>(id&&x.id===id)&&(!age||!x.age||x.age===age))){skipped++;return;}
     const vals=Array(def.columns.length).fill('');vals[ix.id]=(ix.series<0&&r.series&&r.id)?r.series+' / '+r.id:r.id;if(ix.series>=0)vals[ix.series]=r.series;vals[ix.age]=r.age;vals[ix.date]=r.date;vals[ix.load]=r.load;addReportMatrixRow('primary',vals);added++;existing.push({id,age});
   });
   status(added+' CP(s) transferido(s) para a tabela do relatório'+(skipped?'; '+skipped+' possível(is) duplicado(s) ignorado(s)':'')+'. Confira as datas, as idades e as cargas antes de salvar.');
 });
 function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
 function valueAfter(text,labels){
   const lines=text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
   for(const label of labels){const wanted=norm(label);for(let i=0;i<lines.length;i++){const line=lines[i],n=norm(line),pos=n.indexOf(wanted);if(pos>=0){const raw=line.split(/[:|]/);if(raw.length>1&&raw.slice(1).join(':').trim().length>1)return raw.slice(1).join(':').trim();if(lines[i+1]&&!/^[\d\W]+$/.test(lines[i+1]))return lines[i+1];}}}
   return '';
 }
 function fillField(el,val){if(!el||!val||el.readOnly||el.disabled)return false;el.value=val;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true;}
 applyBtn.addEventListener('click',()=>{
   const t=textEl.value;if(!t.trim()){status('Faça a leitura ou cole o texto da ficha primeiro.');return;}
   let filled=0;
   const dateRaw=valueAfter(t,['data da moldagem','data de moldagem','data da coleta']);
   const dateMatch=dateRaw.match(/(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{2,4})/);
   if(dateMatch){let y=dateMatch[3];if(y.length===2)y='20'+y;const iso=y+'-'+dateMatch[2].padStart(2,'0')+'-'+dateMatch[1].padStart(2,'0');const el=document.querySelector('[data-report-field="casting_date"]');if(fillField(el,iso))filled++;}
   const dims=valueAfter(t,['dimensoes dos corpos de prova','dimensoes cp','dimensoes','diametro']);
   if(dims){const el=document.querySelector('[data-report-field="specimen_dimensions"]');if(fillField(el,dims))filled++;}
   const fields=[...document.querySelectorAll('#reporttemplatefields [data-report-field]')];
   for(const el of fields){const box=el.closest('.field'),label=box?.querySelector('label')?.textContent||el.dataset.reportField;const key=norm(label+' '+el.dataset.reportField);let labels=[];if(/fornecedor|supplier/.test(key))labels=['fornecedor'];else if(/nota fiscal|invoice/.test(key))labels=['nota fiscal','nf'];else if(/caminhao|betonada/.test(key))labels=['caminhao','betonada'];else if(/lote|batch/.test(key))labels=['lote','batch'];else if(/abatimento|slump/.test(key))labels=['abatimento','slump'];else if(/identificacao|codigo.*obra|work number/.test(key))labels=['identificacao da obra','codigo da obra'];if(labels.length){const v=valueAfter(t,labels);if(v&&fillField(el,v))filled++;}}
   const typeText=norm(t),typeEl=document.getElementById('reporttype');
   if(typeEl&&/graute/.test(typeText)&&[...typeEl.options].some(o=>o.value==='graute_alvenaria')){typeEl.value='graute_alvenaria';typeEl.dispatchEvent(new Event('change',{bubbles:true}));}
   else if(typeEl&&/argamassa/.test(typeText)&&[...typeEl.options].some(o=>o.value==='compressao_argamassa')){typeEl.value='compressao_argamassa';typeEl.dispatchEvent(new Event('change',{bubbles:true}));}
   else if(typeEl&&/concreto/.test(typeText)&&[...typeEl.options].some(o=>o.value==='ruptura_concreto')){typeEl.value='ruptura_concreto';typeEl.dispatchEvent(new Event('change',{bubbles:true}));}
   status('Sugestões aplicadas: '+filled+' campo(s). Confira todos os campos e as tabelas de CPs manualmente antes de salvar; nenhum resultado de ruptura foi inventado.');
 });
})();
</script>
"""
s = s.replace(anchor, panel + "\n" + anchor, 1)
path.write_text(s, encoding="utf-8")
print("Leitura assistida de ficha inserida.")
