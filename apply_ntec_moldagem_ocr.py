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
  <h4>Campos detectados — revise antes de aplicar</h4>
  <div id="ntec-ocr-fields-preview" class="ntec-ocr-fields-preview" aria-live="polite"><p>Envie a ficha e clique em “Ler ficha”. Os campos encontrados aparecerão separados aqui para revisão.</p></div>
  <details class="ntec-ocr-raw"><summary>Texto bruto do OCR (avançado; pode conter erros)</summary>
    <label for="ntec-ocr-text">Texto reconhecido</label>
    <textarea id="ntec-ocr-text" rows="6" placeholder="O texto completo reconhecido aparecerá aqui para diagnóstico."></textarea>
  </details>
  <button type="button" class="btn secondary" id="ntec-ocr-apply">Aplicar sugestões aos campos</button>
  <hr>
  <h4>Conferência dos corpos de prova (CPs)</h4>
  <p>Cada linha da ficha original representa uma série de moldagem. Use o <b>nº da série de controle</b> para vincular a série à obra e manter a sequência; não cadastre a série de campo, que permanece zerada. Informe cada CP da série, sua idade e data prevista de ruptura. A previsão não é a data real do ensaio; os resultados podem ser lançados depois, inclusive parcialmente.</p>
  <div class="ntec-ocr-controls"><button type="button" class="btn secondary" id="ntec-cp-add">+ Adicionar CP</button><button type="button" class="btn secondary" id="ntec-cp-transfer">Transferir CPs conferidos para o relatório</button></div>
  <div class="ntec-cp-table-wrap"><table class="ntec-cp-table"><thead><tr><th>Nº da série de controle</th><th>Identificação do CP</th><th>Idade (dias)</th><th>Data prevista</th><th>Carga real (tf), se ensaiado</th><th></th></tr></thead><tbody id="ntec-cp-rows"></tbody></table></div>
  <h4>Gerar CPs por série</h4>
  <p>Uma linha preenchida da ficha corresponde a uma série. A série de campo é ignorada; o sistema continua a numeração de controle da obra. Ajuste os valores abaixo conforme a ficha antes de gerar.</p>
  <button type="button" class="btn secondary" id="ntec-cp-use-form02">Preencher padrão confirmado desta ficha (FCK 40 · 10 séries)</button>
  <div class="ntec-series-generator">
    <label>Primeira série de controle <input id="ntec-cp-start-series" type="number" min="1" max="99999" step="1" value="1"></label>
    <label>Linhas de série preenchidas <input id="ntec-cp-series-count" type="number" min="1" max="10" step="1" value="10"></label>
    <label>Idades (dias, separadas por vírgula) <input id="ntec-cp-ages" value="7,28" placeholder="Ex.: 3, 7, 28"></label>
    <label>CPs por idade (na mesma ordem) <input id="ntec-cp-age-counts" value="2,2" placeholder="Ex.: 2, 2, 2"></label>
  </div>
  <button type="button" class="btn secondary" id="ntec-cp-generate">Gerar CPs e séries sequenciais</button>
  <h4>Dados individuais das 10 séries</h4>
  <p>Horários, carga/identificação, abatimento, BT, nota fiscal e volume ficam separados por série. Os campos que não puderem ser confirmados pela ficha ficam para conferência, mas não impedem a geração das 10 séries.</p>
  <div class="ntec-cp-table-wrap"><table class="ntec-cp-table ntec-series-detail-table"><thead><tr><th>Série de controle</th><th>Carga (horário)</th><th>Horário de moldagem</th><th>CPs</th><th>Abatimento (mm)</th><th>Nº série BT</th><th>Nota fiscal</th><th>Volume (m³)</th></tr></thead><tbody id="ntec-series-meta-rows"></tbody></table></div>
  <small>O gerador cria as 10 séries e os 40 CPs. A carga real da prensa fica vazia até o ensaio. BT, nota fiscal, volumes e abatimentos pré-carregados são sugestões lidas visualmente do manuscrito: revise cada linha antes de salvar.</small>
  <small>Não preenchemos automaticamente números manuscritos incertos. Os resultados reais de ruptura devem ser lançados somente após o ensaio.</small>
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
.ntec-cp-table input[data-cp-date="1"]{background:#eef5fb}.ntec-series-generator{display:grid;grid-template-columns:repeat(3,minmax(120px,1fr));gap:8px;margin:8px 0}.ntec-series-generator label{font-size:12px;font-weight:700;color:#29465f}.ntec-series-generator input{display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:8px;border:1px solid #cbd6e1;border-radius:5px}.ntec-series-detail-table{min-width:1050px}.ntec-series-detail-table input{min-width:80px}.ntec-series-detail-table input[data-series-meta="series"]{min-width:55px;width:64px}@media(max-width:650px){.ntec-series-generator{grid-template-columns:1fr}}
.ntec-ocr-card p,.ntec-ocr-card small{display:block;color:#526579;font-size:12px;line-height:1.5}
.ntec-ocr-controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
.ntec-ocr-card input[type=file]{max-width:100%;padding:8px}
.ntec-ocr-card textarea{width:100%;box-sizing:border-box;margin:6px 0 10px}
#ntec-ocr-status{font-size:12px;font-weight:700;margin:8px 0;color:#29465f}.ntec-ocr-fields-preview{display:grid;grid-template-columns:repeat(2,minmax(160px,1fr));gap:8px;margin:8px 0 12px}.ntec-ocr-field-card{border:1px solid #d5dee7;border-radius:7px;padding:8px;background:#fff;min-width:0}.ntec-ocr-field-card img{display:block;width:100%;max-height:90px;object-fit:contain;background:#f8fafc;border-radius:4px;margin:0 0 7px}.ntec-ocr-fields-preview label{display:block;font-size:12px;font-weight:700;color:#29465f}.ntec-ocr-fields-preview input{display:block;box-sizing:border-box;width:100%;margin-top:4px;padding:8px;border:1px solid #cbd6e1;border-radius:5px;font-weight:400}.ntec-ocr-raw{margin:8px 0;border:1px solid #d5dee7;border-radius:7px;padding:8px}.ntec-ocr-raw summary{cursor:pointer;font-size:12px;font-weight:700;color:#526579}@media(max-width:650px){.ntec-ocr-fields-preview{grid-template-columns:1fr}}
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
   const raw=String(text||''),t=raw.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
   // Pontua rótulos próprios do FORM02 para escolher orientação legível.
   const anchors=['formulario de moldagem','codigo da obra','n serie campo','n serie controle','construtora','caracteristica do material','abatimento teorico','local de aplicacao','idades de ruptura','horario do moldador','total de cps coletados','recepcao no laboratorio','fornecedor','quantidade cps','moldagem','form02'];
   let score=anchors.reduce((n,w)=>n+(t.includes(w)?12:0),0);
   const words=(raw.match(/[A-Za-zÀ-ÿ]{3,}/g)||[]).length;
   const chars=(raw.match(/[A-Za-zÀ-ÿ]/g)||[]).length;
   const digits=(raw.match(/\d/g)||[]).length;
   const junk=(raw.match(/[|{}~<>]/g)||[]).length;
   score+=Math.min(words,100)*0.22+Math.min(chars/60,10)+Math.min(digits,80)*0.05;
   score+=(chars/Math.max(1,raw.length))*12;
   score-=junk*0.5;
   if(Number.isFinite(confidence))score+=confidence*0.2;
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
   readBtn.disabled=true;applyBtn.disabled=true;textEl.value='';
   const initialPreview=document.getElementById('ntec-ocr-fields-preview');if(initialPreview)initialPreview.innerHTML='<p>Leitura iniciada. Os recortes e campos aparecerão abaixo durante o processamento.</p>';
   try{
     status('Carregando leitor de texto…');
     await loadScript('https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js',()=>!!window.Tesseract);
     const pages=await getPages(file);
     status('Preparando o reconhecimento em português…');
     const worker=await Tesseract.createWorker('por+eng',1,{langPath:'https://tessdata.projectnaptha.com/4.0.0',gzip:true,logger:m=>{if(m.status)status('Leitura: '+m.status+(m.progress?' '+Math.round(m.progress*100)+'%':''));}});
     const output=[];
     try{for(let i=0;i<pages.length;i++){status('Preparando página '+(i+1)+' de '+pages.length+'…');const variants=makeOcrVariants(pages[i]);let best={score:-1,text:'',angle:0,mode:'6'};for(const variant of variants){for(const mode of ['6','11','12']){status('Lendo página '+(i+1)+' — rotação '+variant.angle+'°, modo '+mode+'…');await worker.setParameters({tessedit_pageseg_mode:mode});const result=await worker.recognize(variant.canvas);const score=ocrScore(result.data.text,result.data.confidence);if(score>best.score)best={score,text:result.data.text,angle:variant.angle,mode,canvas:variant.canvas};}}const fieldCrops=[
       {key:'work_code',label:'Código da obra',left:.50,right:.66,top:.06,bottom:.145},
       {key:'casting_date',label:'Data da moldagem',left:.655,right:.79,top:.06,bottom:.145},
       {key:'contractor',label:'Construtora',left:.085,right:.285,top:.155,bottom:.205},
       {key:'address',label:'Endereço',left:.285,right:.425,top:.155,bottom:.205},
       {key:'supplier',label:'Fornecedor',left:.405,right:.56,top:.18,bottom:.235},
       {key:'material',label:'Característica do material',left:.075,right:.37,top:.18,bottom:.25},
       {key:'fck',label:'FCK',left:.065,right:.16,top:.205,bottom:.275},
       {key:'slump',label:'Abatimento teórico',left:.29,right:.42,top:.195,bottom:.255},
       {key:'application',label:'Local de aplicação',left:.30,right:.515,top:.265,bottom:.66}
     ];
     function ocrFieldClean(key,text){
       let value=String(text||'').replace(/\s+/g,' ').trim();
       if(key==='supplier')value=value.replace(/\b(fornecedor|lan[cç]amento|bombeado|convencional|abatimento|obtido|local de aplica[cç][aã]o|informado pelo cliente)\b/gi,' ');
       if(key==='contractor')value=value.replace(/\bconstrutora\b/gi,' ');
       if(key==='address')value=value.replace(/\bendere[cç]o\b/gi,' ');
       if(key==='application')value=value.replace(/\b(local de aplica[cç][aã]o|informado pelo cliente|quantidade|forma|obra)\b/gi,' ').replace(/^\s*(?:\d{1,3}\s+){1,3}/,' ');
       return value.replace(/\s+/g,' ').trim().replace(/^[|:=\- ]+|[|:=\- ]+$/g,'');
     }
     function ocrFieldScore(field,text,confidence){
       const raw=String(text||'').trim(),key=field.key;
       if(!raw)return -100;
       let score=0;
       if(key==='casting_date'){
         const m=raw.match(/\b\d{1,2}[\s\/.,'-]\d{1,2}[\s\/.,'-]\d{2,4}\b/);
         score=m?100:-50;
       }else if(key==='work_code'){
         const withoutNBR=raw.replace(/\bNBR\b.*$/i,'');
         const m=withoutNBR.match(/\b\d{3,6}\b/);
         score=m?100+m[0].length:-50;
       }else if(key==='fck'||key==='slump'){
         const nums=raw.match(/\b\d{1,3}(?:[.,]\d+)?\b/g)||[];
         const valid=nums.map(x=>Number(x.replace(',','.'))).filter(n=>key==='fck'?(n>=10&&n<=100):(n>=0&&n<=300));
         score=valid.length?55+valid.length*5:-50;
       }else{
         const cleaned=ocrFieldClean(key,raw),words=cleaned.match(/[A-Za-zÀ-ÿ]{3,}/g)||[];
         score=Math.min(cleaned.length,45)*0.3+words.length*3;
         if(key==='supplier'&&/\b(supermix|polimix|engemix|supremo|concrebase|concrevale)\b/i.test(cleaned))score+=25;
         if(key==='contractor'&&/\b(barros|construtora|engenharia|obras|constru[cç][aã]o)\b/i.test(cleaned))score+=10;
         if(key==='address'&&/\b(rua|avenida|av\.|morumbi|centro|vila|jardim)\b/i.test(cleaned))score+=10;
         if(key==='application'){
           if(/vigas|travamento|pilar|laje|funda[cç][aã]o|bloco|radier|sapata|baldrame|parede/i.test(cleaned))score=50+Math.min(cleaned.length,30);
           else if(/^de$/i.test(cleaned))score=12;
           else score=-40;
         }
         if(!words.length&&!(key==='application'&&/^de$/i.test(cleaned)))score=-25;
       }
       if(Number.isFinite(confidence))score+=Math.max(0,confidence)*0.03;
       return score;
     }
     async function recognizeFieldCrop(canvas,field){
       let best={score:-1,text:''};
       for(const mode of ['6','11']){
         await worker.setParameters({tessedit_pageseg_mode:mode,preserve_interword_spaces:'1'});
         const rr=await worker.recognize(canvas);
         const txt=String(rr.data.text||'').replace(/\s+/g,' ').trim();
         const sc=ocrFieldScore(field,txt,rr.data.confidence);
         if(sc>best.score)best={score:sc,text:txt};
       }
       const minimumScore=field.key==='supplier'?14:10;if(best.score<minimumScore)best.text='';
       return best;
     }
     const cropSuggestions=[],previewBox=document.getElementById('ntec-ocr-fields-preview');
     if(previewBox)previewBox.innerHTML='';
     for(const f of fieldCrops){
       status('Recortando e lendo campo '+f.label+'…');
       const crop=document.createElement('canvas');
       const x=Math.round(best.canvas.width*f.left),y=Math.round(best.canvas.height*f.top);
       crop.width=Math.max(1,Math.round(best.canvas.width*(f.right-f.left)));
       crop.height=Math.max(1,Math.round(best.canvas.height*(f.bottom-f.top)));
       crop.getContext('2d').drawImage(best.canvas,x,y,crop.width,crop.height,0,0,crop.width,crop.height);
       const cropImage=crop.toDataURL('image/png');let previewInput=null;
       if(previewBox){
         const card=document.createElement('div');card.className='ntec-ocr-field-card';
         const image=document.createElement('img');image.src=cropImage;image.alt='Recorte da ficha: '+f.label;
         const label=document.createElement('label'),caption=document.createElement('span');previewInput=document.createElement('input');
         caption.textContent=f.label;previewInput.type='text';previewInput.placeholder='Lendo…';previewInput.dataset.ocrField=f.key;
         label.appendChild(caption);label.appendChild(previewInput);card.appendChild(image);card.appendChild(label);previewBox.appendChild(card);
       }
       let detected='';
       if(f.key==='application'){
         const lines=[{top:.255,bottom:.335},{top:.335,bottom:.405},{top:.405,bottom:.485}],parts=[];
         let lineNumber=0;
         for(const line of lines){
           lineNumber++;status('Lendo local de aplicação — linha '+lineNumber+' de 3…');
           const part=document.createElement('canvas'),py=Math.round(best.canvas.height*line.top),ph=Math.max(1,Math.round(best.canvas.height*(line.bottom-line.top)));
           part.width=crop.width;part.height=ph;
           part.getContext('2d').drawImage(best.canvas,x,py,crop.width,ph,0,0,crop.width,ph);
           const res=await recognizeFieldCrop(part,f);if(res.text)parts.push(ocrFieldClean('application',res.text));
         }
         detected=parts.join(' ').replace(/\s+/g,' ').trim();
         if(!/\b(vigas|travamento|pilar|laje|funda[cç][aã]o|bloco|radier|sapata|baldrame|parede)\b/i.test(detected))detected='';
       }else{
         const res=await recognizeFieldCrop(crop,f);detected=ocrFieldClean(f.key,res.text);
       }
       if(previewInput){previewInput.value=detected;previewInput.placeholder='Não reconhecido — confira manualmente';}
       cropSuggestions.push({key:f.key,label:f.label,text:detected,image:cropImage});
     }
     const regions=[{name:'CABEÇALHO',from:0,to:0.27,left:0,right:1},{name:'TABELA DE MOLDAGEM E CPs',from:0.22,to:0.80,left:0,right:1},{name:'RODAPÉ E OBSERVAÇÕES',from:0.75,to:1,left:0,right:1}];const regionText=[];for(const region of regions){const crop=document.createElement('canvas');const sx=Math.round(best.canvas.width*region.left),sw=Math.max(1,Math.round(best.canvas.width*(region.right-region.left)));crop.width=sw;crop.height=Math.max(1,Math.round(best.canvas.height*(region.to-region.from)));crop.getContext('2d').drawImage(best.canvas,sx,Math.round(best.canvas.height*region.from),sw,crop.height,0,0,crop.width,crop.height);let regionBest={score:-1,text:'',mode:'6'};for(const mode of ['6','11']){status('Refinando página '+(i+1)+' — '+region.name+'…');await worker.setParameters({tessedit_pageseg_mode:mode});const rr=await worker.recognize(crop);const digits=(rr.data.text.match(/[0-9]{2,}/g)||[]).length;const sc=ocrScore(rr.data.text,rr.data.confidence)+(region.name.includes('TABELA')?Math.min(digits,30)*0.3:0);if(sc>regionBest.score)regionBest={score:sc,text:rr.data.text,mode};}regionText.push('--- '+region.name+' (modo '+regionBest.mode+') ---\n'+regionBest.text);}     output.push('--- CAMPOS DETECTADOS POR RECORTE (confira) ---\n'+cropSuggestions.map(f=>f.label+': '+f.text).join('\n')+'\n\n--- Página '+(i+1)+' (orientação '+best.angle+'°, modo '+best.mode+') ---\n'+best.text+'\n\n'+regionText.join('\n\n'));}}
     finally{await worker.terminate();}
     textEl.value=output.join('\n\n');status('Leitura concluída. Confira o texto; a escrita manual pode gerar erros. Clique em “Aplicar sugestões” para preencher os campos reconhecidos.');
   }catch(e){const detail=(e&&typeof e.message==='string'&&e.message.trim())?e.message:(typeof e==='string'?e:(e&&e.name?e.name+' (verifique conexão, bloqueio de CDN ou formato do arquivo)':String(e)));status('Falha na leitura automática: '+detail+'. Tente JPG/PNG ou PDF menor que 20 MB; se persistir, envie a mensagem exata para diagnóstico.');console.error('NTEC OCR error:',e);}
   finally{readBtn.disabled=false;applyBtn.disabled=false;}
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

 function ntecDefaultControlSeries(){
   let maximum=0;const pid=String(document.getElementById('reportproject')?.value||'');
   if(!pid)return 1;
   const pool=Array.isArray(reports)?reports:[];
   for(const report of pool){
     if(pid&&String(report.project_id||report.projectId||'')!==pid)continue;
     const sd=report.structured_data||{};
     const serialized=JSON.stringify(sd);
     for(const m of serialized.matchAll(/s[ée]rie\s*0*(\d+)\s*(?:\/|-)\s*cp/gi))maximum=Math.max(maximum,Number(m[1])||0);
     const inspect=(value)=>{
       if(Array.isArray(value)){value.forEach(inspect);return;}
       if(!value||typeof value!=='object')return;
       if(Array.isArray(value.columns)&&Array.isArray(value.rows)){
         const names=value.columns.map(c=>norm(c)),si=names.findIndex(n=>n.includes('serie'));
         for(const row of value.rows){
           const cells=Array.isArray(row)?row:[];
           const namedSeries=cells.find(cell=>cell&&typeof cell==='object'&&/serie/.test(norm(cell.label||'')));
           if(namedSeries){const n=Number.parseInt(namedSeries.value,10);if(Number.isInteger(n)&&n>maximum)maximum=n;}
           else if(si>=0){const cell=cells[si],raw=cell&&typeof cell==='object'?(cell.value||''):cell;const n=Number.parseInt(raw,10);if(Number.isInteger(n)&&n>maximum)maximum=n;}
           const text=cells.map(c=>String(c&&typeof c==='object'?(c.value||''):c||'')).join(' ');
           for(const m of text.matchAll(/s[ée]rie\s*0*(\d+)\s*(?:\/|-)\s*cp/gi))maximum=Math.max(maximum,Number(m[1])||0);
         }
       }
       Object.values(value).forEach(inspect);
     };
     inspect(sd);
   }
   return maximum+1;
 }
 function ntecNextControlSeries(){
   const el=document.getElementById('ntec-cp-start-series');
   const n=Number.parseInt(el?.value||'',10);
   return Number.isInteger(n)&&n>0?n:ntecDefaultControlSeries();
 }
 function ntecRenderSeriesMetaRows(start,count){
   const body=document.getElementById('ntec-series-meta-rows');if(!body)return;
   const starts=['06:46','07:20','08:25','08:38','09:10','11:25','11:40','12:50','14:00','14:50'];
   const molding=['08:15','08:40','09:15','10:00','10:21','12:21','13:30','13:21','14:55','15:40'];
   const values=[140,130,140,140,120,130,130,120,140,120];
   const btNumbers=['2533','2793','2011','2006','2537','2118','2006','2309','2296','2309'];
   const invoices=['174915','174917','174924','174922','174924','174936','174937','174943','174949','174954'];
   const volumes=['10.0','10.0','8.0','8.0','10.0','8.0','8.0','8.0','8.0','8.0'];
   body.innerHTML='';
   for(let i=0;i<count;i++){
     const tr=document.createElement('tr');
     const fields=[
       ['series',String(start+i).padStart(2,'0')],
       ['load-time',starts[i]||''],
       ['molding-time',molding[i]||''],
       ['cp-count','4'],

       ['slump',String(values[i]??'')],
       ['bt',btNumbers[i]||''],
       ['invoice',invoices[i]||''],
       ['volume',volumes[i]||'']
     ];
     tr.innerHTML=fields.map(([key,value])=>'<td><input data-series-meta="'+key+'" aria-label="'+key+'" value="'+String(value).replace(/&/g,'&amp;').replace(/"/g,'&quot;')+'"></td>').join('');
     body.appendChild(tr);
   }
   ntecSyncSeriesMetadataToReport();
 }
 function ntecReadSeriesMetadata(){
   return [...document.querySelectorAll('#ntec-series-meta-rows tr')].map(tr=>{
     const read=k=>String(tr.querySelector('[data-series-meta="'+k+'"]')?.value||'').trim();
     return {series:read('series'),loadTime:read('load-time'),moldingTime:read('molding-time'),cpCount:read('cp-count'),slump:read('slump'),bt:read('bt'),invoice:read('invoice'),volume:read('volume')};
   });
 }
 function ntecSyncSeriesMetadataToReport(){
   const rows=ntecReadSeriesMetadata();if(!rows.length)return;
   const target=document.getElementById('reportobservations')||document.getElementById('reportresults')||document.getElementById('reportcontent');
   if(!target)return;
   const marker='DADOS INDIVIDUAIS POR SÉRIE — FICHA EMPREITEC';
   const before=String(target.value||'');const keep=before.includes(marker)?before.slice(0,before.indexOf(marker)).trim():before.trim();
   const value=x=>x||'—';
   const header='PADRÃO CONFIRMADO: obra 1408 | moldagem 16/10/2026 | FCK 40 MPa | fornecedor Supermix | vigas de travamento | brita 0 e brita 1 | abatimento teórico 120 ± 20 mm | CPs cilíndricos 100 x 200 mm | 2 CPs aos 7 dias e 2 CPs aos 28 dias por série.';
   const lines=rows.map(r=>'Série de controle '+value(r.series)+' | carga/horário '+value(r.loadTime)+' | moldagem '+value(r.moldingTime)+' | CPs '+value(r.cpCount)+' | abatimento '+value(r.slump)+' mm | BT '+value(r.bt)+' | nota fiscal '+value(r.invoice)+' | volume '+value(r.volume)+' m³');
   target.value=(keep?keep+'\n\n':'')+header+'\n'+marker+'\n'+lines.join('\n');
   target.dispatchEvent(new Event('input',{bubbles:true}));target.dispatchEvent(new Event('change',{bubbles:true}));
 }
 document.getElementById('ntec-cp-use-form02')?.addEventListener('click',()=>{
   const staged=[...document.querySelectorAll('#ntec-cp-rows tr')];
   const hasStaged=staged.some(tr=>['series','id','age','date','load'].some(k=>String(tr.querySelector('[data-cp="'+k+'"]')?.value||'').trim()));
   if(hasStaged&&!confirm('Substituir os CPs que já estão na conferência pelo padrão de 10 séries desta ficha?'))return;
   if(hasStaged){const stagedBody=document.getElementById('ntec-cp-rows');if(stagedBody)stagedBody.innerHTML='';}
   const typeEl=document.getElementById('reporttype');
   if(typeEl&&[...typeEl.options].some(o=>o.value==='ruptura_concreto')){typeEl.value='ruptura_concreto';typeEl.dispatchEvent(new Event('change',{bubbles:true}));}
   const projectSelect=document.getElementById('reportproject');
   if(projectSelect&&typeof projectsData!=='undefined'){
     const candidates=projectsData.filter(p=>String(p.work_number||'').replace(/\D/g,'')==='1408');
     if(candidates.length===1){projectSelect.value=String(candidates[0].id);projectSelect.dispatchEvent(new Event('change',{bubbles:true}));}
   }
   const casting=document.querySelector('[data-report-field="casting_date"]');
   if(casting){casting.value='2026-10-16';casting.dispatchEvent(new Event('input',{bubbles:true}));casting.dispatchEvent(new Event('change',{bubbles:true}));}
   const dimensions=document.querySelector('[data-report-field="specimen_dimensions"]');
   if(dimensions){dimensions.value='100 x 200';dimensions.dispatchEvent(new Event('input',{bubbles:true}));dimensions.dispatchEvent(new Event('change',{bubbles:true}));}
   const fields=[...document.querySelectorAll('#reporttemplatefields [data-report-field]')];
   for(const el of fields){
     const box=el.closest('.field'),label=box?.querySelector('label')?.textContent||'',key=norm(label+' '+el.dataset.reportField);
     let value=null,numeric=null;
     if(/fck|resistencia caracteristica/.test(key)){value='40';numeric=40;}
     else if(/fornecedor|supplier/.test(key))value='Supermix';
     else if(/construtora|empreiteira|contractor/.test(key))value='DP BARROS';
     else if(/abatimento teorico|slump teorico/.test(key)){value='120 ± 20 mm';numeric=120;}
     else if(/local de aplicacao|elemento estrutural|aplicacao/.test(key))value='Vigas de travamento';
     else if(/agregado|brita|granulometria/.test(key))value='Brita 0 e Brita 1';
     else if(/volume/.test(key))continue;
     if(value!==null){
       el.value=el.type==='number'&&numeric!==null?String(numeric):value;
       el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
     }
   }
   const codeTargets=fields.filter(el=>/codigo da obra|work code|identificacao da obra/.test(norm((el.closest('.field')?.querySelector('label')?.textContent||'')+' '+el.dataset.reportField)));
   codeTargets.forEach(el=>{el.value='1408';el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));});
   const setIfEmpty=(id,value)=>{const el=document.getElementById(id);if(el&&!String(el.value||'').trim()){el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}};
   setIfEmpty('reportcontent','Moldagem de concreto para vigas de travamento. FCK especificado: 40 MPa. Agregados: brita 0 e brita 1. Corpos de prova cilíndricos de 100 x 200 mm.');
   setIfEmpty('reportmethod','Dados transcritos da ficha de moldagem EMPREITEC. Foram previstos 2 CPs para 7 dias e 2 CPs para 28 dias em cada série. Registrar a data real do ensaio e a carga da prensa quando cada CP for rompido.');
   document.getElementById('ntec-cp-series-count').value='10';
   document.getElementById('ntec-cp-ages').value='7,28';
   document.getElementById('ntec-cp-age-counts').value='2,2';
   const start=ntecDefaultControlSeries();document.getElementById('ntec-cp-start-series').value=String(start);
   ntecRenderSeriesMetaRows(start,10);
   if(typeof updateReportTitleAuto==='function')updateReportTitleAuto();
   status('Aplicando padrão confirmado: obra 1408, moldagem 16/10/2026, FCK 40 MPa, Supermix, vigas de travamento, brita 0 + brita 1 e 10 séries.');
   document.getElementById('ntec-cp-generate')?.click();
   const generated=document.querySelectorAll('#ntec-cp-rows tr').length;
   if(generated===40){
     document.getElementById('ntec-cp-transfer')?.click();
   }else{
     status('O padrão não gerou os 40 CPs esperados (gerados: '+generated+'). Confira as idades, a quantidade por idade e a mensagem anterior; nada foi transferido automaticamente.');
   }
 });
 document.getElementById('ntec-series-meta-rows')?.addEventListener('input',()=>ntecSyncSeriesMetadataToReport());
 document.getElementById('ntec-cp-generate')?.addEventListener('click',()=>{
   const count=Number.parseInt(document.getElementById('ntec-cp-series-count')?.value||'',10);
   const ages=String(document.getElementById('ntec-cp-ages')?.value||'').split(/[;,]/).map(x=>Number.parseInt(x.trim(),10));
   const qtys=String(document.getElementById('ntec-cp-age-counts')?.value||'').split(/[;,]/).map(x=>Number.parseInt(x.trim(),10));
   if(!Number.isInteger(count)||count<1||count>10){status('Informe de 1 a 10 linhas de série preenchidas.');return;}
   if(!ages.length||ages.length!==qtys.length||ages.some(n=>!Number.isInteger(n)||n<0)||qtys.some(n=>!Number.isInteger(n)||n<0||n>20)||qtys.reduce((a,b)=>a+b,0)<1){status('Confira as idades e a quantidade de CPs por idade. Use a mesma quantidade de idades e números de CPs.');return;}
   if(document.getElementById('reporttype')?.value!=='ruptura_concreto'){status('Selecione “Ruptura de concreto” antes de gerar os CPs.');return;}
   const existingRows=[...document.querySelectorAll('#ntec-cp-rows tr')];
   if(existingRows.some(tr=>['series','id','age','date','load'].some(k=>String(tr.querySelector('[data-cp="'+k+'"]')?.value||'').trim()))&&!confirm('Substituir as linhas de CPs que já estão na conferência?'))return;
   const body=document.getElementById('ntec-cp-rows');body.innerHTML='';
   const start=ntecNextControlSeries();
   const metaBody=document.getElementById('ntec-series-meta-rows');
   if(metaBody){
     if(metaBody.rows.length!==count)ntecRenderSeriesMetaRows(start,count);
     else [...metaBody.rows].forEach((row,i)=>{const inp=row.querySelector('[data-series-meta="series"]');if(inp)inp.value=String(start+i).padStart(2,'0');});
   }
   let total=0;
   for(let si=0;si<count;si++){
     const controlSeries=start+si;let cpNo=1;
     ages.forEach((age,ai)=>{
       for(let j=0;j<qtys[ai];j++){
         const cpId='CP'+String(cpNo).padStart(2,'0');
         addOcrCpRow({series:String(controlSeries).padStart(2,'0'),id:cpId,age:String(age),date:cpDateFromAge(age),load:''});
         cpNo++;total++;
       }
     });
   }
   ntecSyncSeriesMetadataToReport();
   status('Gerados '+total+' CP(s) em '+count+' séries de controle, da '+String(start).padStart(2,'0')+' à '+String(start+count-1).padStart(2,'0')+'. Cada série tem '+qtys.reduce((a,b)=>a+b,0)+' CP(s). Confira os dados individuais e transfira para o relatório. A carga real da prensa continua vazia.');
 });
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
   const normHeader=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
   const idx=terms=>{
     const wanted=terms.map(normHeader);
     const exact=def.columns.findIndex(col=>wanted.includes(normHeader(col)));
     if(exact>=0)return exact;
     // Prefix matching prevents a header such as "Dimensões do CP" from being mistaken for the CP identifier.
     return def.columns.findIndex(col=>wanted.some(t=>normHeader(col).startsWith(t)));
   };
   const ix={
     id:idx(['identificação do cp','identificacao do cp','cp nº','cp n°','nº do cp','numero do cp','amostra nº','amostra n°','amostra','cp']),
     series:idx(['nº da série de controle','numero da serie de controle','nº de série de controle','numero de serie de controle','nº série','nº de série','numero da serie','numero de serie','série de controle','serie de controle','série da moldagem','serie da moldagem']),
     age:idx(['idade (dias)','idade dias','idade']),
     date:idx(['data de ruptura','data prevista de ruptura','data prevista','ruptura']),
     load:idx(['carga (tf)','carga de ruptura','carga real','carga'])
   };
   if(ix.id<0||ix.age<0){status('Não foi possível localizar as colunas de identificação do CP e idade na tabela do relatório. Nada foi transferido; confira o modelo de relatório.');return;}if(ix.date<0)ix.date=idx(['data prevista','previsão de ruptura','previsao de ruptura']);if(ix.date<0){status('Não foi localizada uma coluna de data de ruptura/previsão no relatório. Nada foi transferido.');return;}
   if(ix.series===ix.id)ix.series=-1;
   const existing=[...document.querySelectorAll('tbody[data-report-matrix-rows="primary"] tr')].map(tr=>({id:String(tr.querySelector('[data-matrix-cell="'+ix.id+'"]')?.value||'').trim().toLowerCase(),age:String(tr.querySelector('[data-matrix-cell="'+ix.age+'"]')?.value||'').trim().toLowerCase(),series:ix.series>=0?String(tr.querySelector('[data-matrix-cell="'+ix.series+'"]')?.value||'').trim().toLowerCase():''}));
   let added=0,skipped=0;
   valid.forEach(r=>{
     const series=String(r.series||'').trim().toLowerCase(),age=String(r.age||'').trim().toLowerCase();
     const id=String((ix.series<0&&r.series&&r.id)?'Série '+r.series+' / '+r.id:(r.id||'')).trim().toLowerCase();
     if(id&&existing.some(x=>x.id===id&&(ix.series<0||x.series===series)&&(!age||!x.age||x.age===age))){skipped++;return;}
     const vals=Array(def.columns.length).fill('');vals[ix.id]=(ix.series<0&&r.series&&r.id)?'Série '+r.series+' / '+r.id:(r.id||'');if(ix.series>=0)vals[ix.series]=r.series;vals[ix.age]=r.age;vals[ix.date]=r.date;if(ix.load>=0)vals[ix.load]=r.load;addReportMatrixRow('primary',vals);added++;existing.push({id,age,series});
   });
   status(added+' CP(s) transferido(s) para a tabela do relatório'+(skipped?'; '+skipped+' possível(is) duplicado(s) ignorado(s)':'')+'. Confira as datas, as idades e as cargas antes de salvar.');
 });
 function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
 function ocrCandidate(key){return String(document.querySelector('[data-ocr-field="'+key+'"]')?.value||'').trim();}
 function valueAfter(text,labels){
   const lines=String(text||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
   // Prefer the separately OCR'd fixed-field crops, which are less likely to mix adjacent columns.
   const cropStart=lines.findIndex(x=>norm(x).includes('campos detectados por recorte'));
   if(cropStart>=0){
     const cropEnd=lines.findIndex((x,i)=>i>cropStart&&norm(x).startsWith('pagina'));
     const cropLines=lines.slice(cropStart+1,cropEnd<0?undefined:cropEnd);
     for(const label of labels){
       const wanted=norm(label);
       const hit=cropLines.find(line=>{const parts=line.split(':');return parts.length>1&&(norm(parts[0])===wanted||norm(parts[0]).startsWith(wanted+' '));});
       if(hit){const value=hit.slice(hit.indexOf(':')+1).trim();if(value&&!/^\[nao reconhecido\]$/i.test(norm(value)))return value;}
     }
   }
   for(const label of labels){const wanted=norm(label);for(let i=0;i<lines.length;i++){const line=lines[i],n=norm(line);if(!n.includes(wanted))continue;const raw=line.split(/[:|]/);if(raw.length>1){const value=raw.slice(1).join(':').trim();if(value.length>1&&norm(value)!==wanted)return value;}const next=lines.slice(i+1,i+3).find(x=>x.length>1&&!/^[\d\W]+$/.test(x)&&!norm(x).includes('pagina'));if(next)return next;}}
   return '';
 }
 function fillField(el,val){if(!el||!val||el.readOnly||el.disabled)return false;el.value=val;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true;}
 applyBtn.addEventListener('click',()=>{
   const t=textEl.value,previewHasData=[...document.querySelectorAll('[data-ocr-field]')].some(el=>String(el.value||'').trim());
   if(!t.trim()&&!previewHasData){status('Faça a leitura da ficha ou preencha ao menos um campo de conferência antes de aplicar.');return;}
   let filled=0,matchedWorkCode='';
   const workCodeMatch=ocrCandidate('work_code').match(/\d{3,6}/),projectSelect=document.getElementById('reportproject');
   if(workCodeMatch&&projectSelect){
     const digits=workCodeMatch[0],compact=value=>String(value||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');
     const expected='obra'+digits.padStart(3,'0');
     const matches=[...projectSelect.options].filter(o=>compact(o.textContent).includes(expected));
     if(matches.length===1&&projectSelect.value!==matches[0].value){
       projectSelect.value=matches[0].value;projectSelect.dispatchEvent(new Event('change',{bubbles:true}));filled++;matchedWorkCode=digits;
     }else if(matches.length===1){matchedWorkCode=digits;}
   }
   const dateRaw=ocrCandidate('casting_date')||valueAfter(t,['data da moldagem','data de moldagem','data da coleta']);
   const dateMatch=dateRaw.match(/(\d{1,2})[\s\/.,'-](\d{1,2})[\s\/.,'-](\d{2,4})/);
   if(dateMatch){let y=dateMatch[3];if(y.length===2)y='20'+y;const iso=y+'-'+dateMatch[2].padStart(2,'0')+'-'+dateMatch[1].padStart(2,'0');const el=document.querySelector('[data-report-field="casting_date"]');if(fillField(el,iso))filled++;}
   const dims=valueAfter(t,['dimensoes dos corpos de prova','dimensoes cp','dimensoes','diametro']);
   if(dims){const el=document.querySelector('[data-report-field="specimen_dimensions"]');if(fillField(el,dims))filled++;}
   const fields=[...document.querySelectorAll('#reporttemplatefields [data-report-field]')];
   for(const el of fields){
     const box=el.closest('.field'),label=box?.querySelector('label')?.textContent||el.dataset.reportField,key=norm(label+' '+el.dataset.reportField);
     let labels=[],directKey='';
     if(/fornecedor|supplier/.test(key)){labels=['fornecedor'];directKey='supplier';}
     else if(/construtora|empreiteira|contractor/.test(key)){labels=['construtora'];directKey='contractor';}
     else if(/endereco|address/.test(key)){labels=['endereco','endereço'];directKey='address';}
     else if(/nota fiscal|invoice/.test(key))labels=['nota fiscal','nf'];
     else if(/caminhao|betonada|bt numero/.test(key))labels=['caminhao','bt'];
     else if(/lote|batch/.test(key))labels=['lote','batch'];
     else if(/fck|resistencia caracteristica/.test(key)){labels=['fck'];directKey='fck';}
     else if(/abatimento teorico|slump teorico/.test(key)){labels=['abatimento teorico'];directKey='slump';}
     else if(/abatimento|slump/.test(key)){labels=['abatimento','slump'];directKey='slump';}
     else if(/local de aplicacao|elemento estrutural|aplicacao/.test(key)){labels=['local de aplicacao'];directKey='application';}
     else if(/volume/.test(key))labels=['volume'];
     else if(/identificacao|codigo.*obra|work number/.test(key))labels=['identificacao da obra','codigo da obra'];
     if(labels.length){
       let v=(directKey?ocrCandidate(directKey):'')||valueAfter(t,labels);
       if(directKey==='supplier')v=v.replace(/^fornecedor\s*/i,'').trim();
       if(directKey==='contractor')v=v.replace(/^construtora\s*/i,'').trim();
       if(directKey==='address')v=v.replace(/^endereco\s*/i,'').trim();
       if(directKey==='fck'||directKey==='slump'){const m=v.match(/\b\d{1,3}(?:[.,]\d+)?\b/);if(m)v=m[0];}
       if(directKey==='application')v=v.replace(/^\s*(?:\d{1,3}\s+){1,3}/,'').trim();
       if(v&&fillField(el,v))filled++;
     }
   }
   const material=String(ocrCandidate('material')||valueAfter(t,['caracteristica do material'])).toLowerCase(),typeEl=document.getElementById('reporttype');
   // The blank template prints all three material choices. Change the report type only if the crop OCR sees an explicit check mark.
   const checkedConcrete=/concreto\s*(?:\(\s*[xX]\s*\)|\[\s*[xX]\s*\]|[✓✔☒☑])/i.test(material);
   const checkedMortar=/argamassa\s*(?:\(\s*[xX]\s*\)|\[\s*[xX]\s*\]|[✓✔☒☑])/i.test(material);
   const checkedGrout=/graute\s*(?:\(\s*[xX]\s*\)|\[\s*[xX]\s*\]|[✓✔☒☑])/i.test(material);
   const selectedType=checkedConcrete&&!checkedMortar&&!checkedGrout?'ruptura_concreto':checkedMortar&&!checkedConcrete&&!checkedGrout?'compressao_argamassa':checkedGrout&&!checkedConcrete&&!checkedMortar?'graute_alvenaria':'';
   if(typeEl&&selectedType&&[...typeEl.options].some(o=>o.value===selectedType)){typeEl.value=selectedType;typeEl.dispatchEvent(new Event('change',{bubbles:true}));}
   status('Sugestões aplicadas: '+filled+' campo(s).'+(matchedWorkCode?' Obra vinculada pelo código '+matchedWorkCode+'.':'')+' Confira os valores e a tabela antes de salvar. O tipo do material só é alterado quando a marcação do formulário é inequívoca.');
 });
})();
</script>
"""
s = s.replace(anchor, panel + "\n" + anchor, 1)
path.write_text(s, encoding="utf-8")
print("Leitura assistida de ficha inserida.")
