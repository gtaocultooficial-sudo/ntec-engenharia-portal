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
  <small>O arquivo é processado no navegador e não é enviado a um serviço externo de OCR. É necessária conexão para carregar as bibliotecas de leitura.</small>
</div>
<style>
.ntec-ocr-card{border:1px solid var(--line);border-radius:12px;padding:15px;margin:0 0 16px;background:#f7fafc}
.ntec-ocr-card h3{margin:0 0 6px;color:var(--navy);font-size:16px}
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
 async function getPages(file){
   if(!/\.pdf$/i.test(file.name)&&file.type!=='application/pdf')return [await createImageBitmap(file)];
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
     try{for(let i=0;i<pages.length;i++){status('Lendo página '+(i+1)+' de '+pages.length+'…');const result=await worker.recognize(pages[i]);output.push('--- Página '+(i+1)+' ---\n'+result.data.text);if(typeof ImageBitmap!=='undefined'&&pages[i] instanceof ImageBitmap)pages[i].close?.();}}
     finally{await worker.terminate();}
     textEl.value=output.join('\n\n');status('Leitura concluída. Confira o texto; a escrita manual pode gerar erros. Clique em “Aplicar sugestões” para preencher os campos reconhecidos.');
   }catch(e){const detail=(e&&typeof e.message==='string'&&e.message.trim())?e.message:(typeof e==='string'?e:(e&&e.name?e.name+' (verifique conexão, bloqueio de CDN ou formato do arquivo)':String(e)));status('Falha na leitura automática: '+detail+'. Tente JPG/PNG ou PDF menor que 20 MB; se persistir, envie a mensagem exata para diagnóstico.');console.error('NTEC OCR error:',e);}
   finally{readBtn.disabled=false;}
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
