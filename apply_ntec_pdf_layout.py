#!/usr/bin/env python3
from pathlib import Path
import re, sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "_site/admin/index.html")
source = path.read_text(encoding="utf-8")

replacement = r"""function printNtecReport(id){
 const r=reports.find(x=>String(x.id)===String(id));
 if(!r)return alert('Relatório não encontrado. Atualize a página e tente novamente.');
 const type=r.report_type||'outro';
 const tpl=REPORT_TEMPLATES[type]||REPORT_TEMPLATES.outro||{};
 const sd=r.structured_data||{},fields=sd.fields||{},tables=sd.matrix||{};
 const reportNumber=r.report_number||fields.report_number||'Não informado';
 const workCode=r.work_number?'OBRA'+String(r.work_number).padStart(3,'0'):(fields.record_number||'Não informado');
 const dateValue=r.report_date||'';
 const fmtDate=value=>{
   const s=String(value??'').trim();
   const m=s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
   return m?m[3]+'/'+m[2]+'/'+m[1]:(s||'—');
 };
 const fmtValue=(field,value)=>field?.type==='date'?fmtDate(value):String(value??'').trim();
 const headings={
  ruptura_concreto:'ENSAIOS DE COMPRESSÃO EM CORPOS DE PROVA DE CONCRETO',
  testemunhos_concreto:'CONTROLE DA QUALIDADE DE TESTEMUNHOS DE ESTRUTURAS DE CONCRETO',
  prismas_alvenaria:'DETERMINAÇÃO DA RESISTÊNCIA À COMPRESSÃO DE PRISMAS DE ALVENARIA',
  blocos_concreto:'CONTROLE DE QUALIDADE DE BLOCOS DE CONCRETO',
  teor_ar_concreto:'TEOR DE AR EM CONCRETO FRESCO - MÉTODO PRESSOMÉTRICO',
  aderencia_argamassa:'ENSAIO DE ADERÊNCIA À TRAÇÃO - REVESTIMENTO DE ARGAMASSA',
  compressao_argamassa:'ENSAIO DE RESISTÊNCIA À FLEXÃO E À COMPRESSÃO DE ARGAMASSA',
  graute_alvenaria:'CONTROLE TECNOLÓGICO DE GRAUTE PARA ALVENARIA',
  spt:'RELATÓRIO DE SONDAGEM SPT',
  pastilha_mct:'ENSAIO DE PASTILHA - CLASSIFICAÇÃO MCT',
  inspecao_solo_trado:'INSPEÇÃO DE SOLO POR TRADO',
  pavimentacao:'CONTROLE TECNOLÓGICO DE PAVIMENTAÇÃO',
  acompanhamento:'RELATÓRIO DE ACOMPANHAMENTO DE OBRA',
  vistoria:'RELATÓRIO TÉCNICO DE VISTORIA'
 };
 const reportHeading=headings[type]||String(r.typeLabel||r.report_type||'RELATÓRIO TÉCNICO').toLocaleUpperCase('pt-BR');
 const norm=String(r.normative_references||tpl.norms||'').trim();
 const escVal=value=>esc(value==null||String(value).trim()===''?'—':String(value));
 const section=(title,value)=>value&&String(value).trim()?'<section class="n-section"><div class="n-section-title">'+esc(title)+'</div><div class="n-text">'+esc(String(value).trim())+'</div></section>':'';
 const pairRows=items=>{
  let html='';
  for(let i=0;i<items.length;i+=2){
   const a=items[i],b=items[i+1];
   html+='<tr><th>'+esc(a.label)+'</th><td>'+escVal(a.value)+'</td>';
   if(b)html+='<th>'+esc(b.label)+'</th><td>'+escVal(b.value)+'</td>';
   else html+='<th></th><td></td>';
   html+='</tr>';
  }
  return html;
 };
 const baseInfo=[
  {label:'CLIENTE',value:r.client||'Não informado'},
  {label:'OBRA',value:r.project||'Não informada'},
  {label:'CÓDIGO DA OBRA',value:fields.record_number||workCode},
  {label:'RELATÓRIO Nº',value:reportNumber},
  {label:'DATA DO RELATÓRIO',value:fmtDate(dateValue)},
  {label:'FORNECEDOR',value:fields.supplier||fields.concrete_supplier||fields.vendor||'—'}
 ];
 const fieldDefs=(tpl.fields||[]).filter(f=>!['report_number','record_number','series'].includes(f.name)&&String(fields[f.name]??'').trim()!=='');
 const detailPairs=fieldDefs.map(f=>({label:f.label,value:fmtValue(f,fields[f.name])}));
 const fieldHtml=detailPairs.length?'<div class="n-section-title">IDENTIFICAÇÃO E DADOS DO ENSAIO</div><table class="n-info"><tbody>'+pairRows(detailPairs)+'</tbody></table>':'';
 const resultTable=(text,columns,label)=>{
  if(!String(text||'').trim()||!columns?.length)return '';
  const rows=String(text).trim().split(/\r?\n/).filter(line=>line.trim()).map(line=>line.split('|').map(cell=>cell.trim()));
  const isPress=['ruptura_concreto','testemunhos_concreto','prismas_alvenaria','blocos_concreto','graute_alvenaria'].includes(type);
  const head=columns.map(col=>isPress&&/carga\s*\(kN\)/i.test(String(col))?String(col).replace(/\(kN\)/i,'(tf)'):String(col));
  const body=rows.map(row=>{
    while(row.length<head.length)row.push('');
    return '<tr>'+row.slice(0,head.length).map(cell=>String(cell||'').trim()?'<td>'+esc(fmtDate(cell))+'</td>':'<td></td>').join('')+'</tr>';
  }).join('');
  const className=head.length>=10?'n-results n-results-wide':'n-results';
  return '<div class="n-section-title n-table-title">'+esc(label||'RESULTADOS DO ENSAIO')+'</div><table class="'+className+'"><thead><tr>'+head.map(col=>'<th>'+esc(col)+'</th>').join('')+'</tr></thead><tbody>'+body+'</tbody></table>';
 };
 const series=String(fields.series||'').trim();
 const seriesBar=series?'<div class="n-series">SÉRIE / LOTE DE CP: '+esc(series)+'</div>':'';
 const mainTable=resultTable(tables.primary,tpl.matrix?.columns,tpl.matrix?.label);
 const extraTable=resultTable(tpl.extraMatrix?tables[tpl.extraMatrix.name]:'',tpl.extraMatrix?.columns,tpl.extraMatrix?.label);
 let resultSummary=String(r.results||'').trim();
 if(resultSummary.startsWith('Dados de ensaio registrados na ficha:')){
  resultSummary=resultSummary.split(String.fromCharCode(10)).filter(line=>line.startsWith('Resumo numérico das resistências')||line.startsWith('Resumo numérico')).join(String.fromCharCode(10));
 }
 const contentHtml=section('OBJETO / DESCRIÇÃO DO SERVIÇO',r.content);
 const methodHtml=section('MÉTODO / PROCEDIMENTO APLICADO',r.methodology);
 const resultsHtml=section('RESUMO DOS RESULTADOS',resultSummary);
 const observationsHtml=section('OBSERVAÇÕES / CONCLUSÃO TÉCNICA',r.observations);
 const calibration=String(fields.calibration||'').trim();
 const equipment=String(fields.equipment||fields.apparatus||'').trim();
 const equipmentLine=equipment||calibration?'<div class="n-calibration"><b>EQUIPAMENTO / CALIBRAÇÃO:</b> '+esc([equipment,calibration].filter(Boolean).join(' - '))+'</div>':'';
 const responsible=String(r.technical_responsible||'').trim();
 const registration=String(r.professional_registration||'').trim();
 const doc='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(r.title||reportHeading)+' - '+esc(reportNumber)+'</title><style>'+
 '@page{size:A4 portrait;margin:7mm 7mm 8mm}*{box-sizing:border-box}html,body{margin:0;padding:0}body{font:8.5pt Arial,Helvetica,sans-serif;color:#111;line-height:1.25;background:#fff}.n-document{width:100%;max-width:196mm;margin:0 auto;border:1px solid #222;padding:3mm}.n-header{width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:2mm}.n-header td{border:1px solid #333;padding:2mm;vertical-align:middle}.n-logo{width:22%;text-align:center;font-size:17pt;font-weight:900;color:#10263f;letter-spacing:.5px}.n-logo small{display:block;font-size:6.5pt;letter-spacing:1px;font-weight:700}.n-company{text-align:center;font-size:10pt;font-weight:700}.n-company small{display:block;font-size:7pt;font-weight:400;margin-top:2px}.n-docbox{width:24%;text-align:center;font-size:7pt}.n-docbox b{display:block;font-size:8pt}.n-docbox strong{display:block;font-size:9pt;margin-top:3px;overflow-wrap:anywhere}.n-title{border:1px solid #333;padding:2.2mm;text-align:center;font-weight:700;font-size:9pt;margin-bottom:2mm;text-transform:uppercase}.n-norm{border:1px solid #444;border-top:0;padding:1.7mm 2mm;text-align:center;font-size:7pt;margin-top:-2mm;margin-bottom:2.5mm;overflow-wrap:anywhere}.n-section-title{background:#e8e8e8;border:1px solid #333;padding:1.5mm 2mm;text-align:center;font-weight:700;font-size:7.5pt;margin-top:2.2mm}.n-info{border-collapse:collapse;width:100%;table-layout:fixed}.n-info th,.n-info td{border:1px solid #555;padding:1.5mm;vertical-align:top;overflow-wrap:anywhere}.n-info th{width:16%;font-weight:700;text-align:left;background:#f7f7f7;font-size:7pt}.n-info td{width:34%;font-size:8pt}.n-series{border:1px solid #333;border-top:0;padding:1.5mm 2mm;font-weight:700;background:#fafafa}.n-results{border-collapse:collapse;width:100%;table-layout:fixed;font-size:7.3pt;margin:0}.n-results th,.n-results td{border:1px solid #444;padding:1.2mm 1mm;text-align:center;vertical-align:middle;overflow-wrap:anywhere;word-break:normal}.n-results th{background:#f1f1f1;font-weight:700;font-size:6.8pt}.n-results-wide{font-size:6.2pt}.n-results-wide th{font-size:5.8pt;padding:.8mm .5mm}.n-results-wide td{padding:.9mm .5mm}.n-section{margin-top:2.2mm;break-inside:avoid;page-break-inside:avoid}.n-section .n-text{border:1px solid #555;border-top:0;padding:2mm;white-space:pre-wrap;overflow-wrap:anywhere;font-size:7.5pt;line-height:1.3}.n-calibration{border:1px solid #555;padding:1.7mm 2mm;font-size:7pt;margin-top:2mm;overflow-wrap:anywhere}.n-footer-note{border:1px solid #555;padding:1.7mm 2mm;font-size:6.5pt;line-height:1.25;margin-top:2mm}.n-signature{display:grid;grid-template-columns:1fr 1fr;gap:10mm;margin:9mm 3mm 1mm;break-inside:avoid;page-break-inside:avoid}.n-signature div{text-align:center;font-size:7.5pt;overflow-wrap:anywhere}.n-signature .n-line{border-top:1px solid #222;padding-top:1.5mm}.n-date{text-align:right;font-size:7pt;margin-top:4mm}.n-print-actions{text-align:center;margin:5mm 0}.n-print-actions button{font:inherit;padding:6px 12px}@media print{.n-document{max-width:none;margin:0;border:1px solid #222;padding:2.5mm}.n-print-actions{display:none!important}.n-section,.n-info,.n-results,.n-calibration,.n-footer-note,.n-signature{break-inside:avoid;page-break-inside:avoid}.n-results{font-size:7pt}.n-results-wide{font-size:6pt}.n-results-wide th{font-size:5.6pt}.n-header,.n-section-title{break-after:avoid;page-break-after:avoid}}@media screen{body{padding:6mm;background:#eceff2}.n-document{box-shadow:0 2px 15px #0002}}'+
 '</style></head><body><main class="n-document">'+
 '<table class="n-header"><tr><td class="n-logo">NTEC<small>ENGENHARIA</small></td><td class="n-company">NTEC ENGENHARIA &amp; GEOTECNIA<small>Controle tecnológico e ensaios de materiais</small></td><td class="n-docbox">RELATÓRIO DE ENSAIO<b>IDENTIFICAÇÃO</b><strong>'+esc(reportNumber)+'</strong><span>'+esc(fmtDate(dateValue))+'</span></td></tr></table>'+
 '<div class="n-title">'+esc(reportHeading)+'</div>'+
 (norm?'<div class="n-norm">'+esc(norm)+'</div>':'')+
 '<div class="n-section-title">DADOS DO CLIENTE / OBRA</div><table class="n-info"><tbody>'+pairRows(baseInfo)+'</tbody></table>'+
 fieldHtml+
 seriesBar+
 mainTable+
 extraTable+
 contentHtml+
 methodHtml+
 resultsHtml+
 observationsHtml+
 equipmentLine+
 '<div class="n-footer-note">Os resultados apresentados referem-se às amostras e informações identificadas neste relatório. A interpretação deve considerar a edição normativa aplicável, o procedimento efetivamente realizado, os critérios de aceitação e as especificações do projeto. A emissão final deve ser revisada e validada pelo responsável técnico.</div>'+
 '<div class="n-date">Data do relatório: '+esc(fmtDate(dateValue))+'</div>'+
 '<div class="n-signature"><div class="n-line">'+esc(responsible||'Responsável técnico')+'<br>'+esc(registration||'Registro profissional')+'<br>NTEC ENGENHARIA &amp; GEOTECNIA</div><div class="n-line">Assinatura do responsável técnico</div></div>'+
 '<div class="n-print-actions"><button onclick="window.print()">Imprimir / salvar como PDF</button></div></main><script>window.onload=()=>setTimeout(()=>window.print(),250)<\/script></body></html>';
 const w=window.open('','_blank');
 if(!w)return alert('Permita pop-ups para gerar o PDF.');
 w.document.open();w.document.write(doc);w.document.close();
}
function closeEditModal""";

s2, n = re.subn(r"function printNtecReport\(id\)\{.*?\}\s*function closeEditModal", lambda _m: replacement, source, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Não encontrei exatamente uma função printNtecReport para atualizar")
if "size:A4 portrait" not in s2 or "DADOS DO CLIENTE / OBRA" not in s2 or "SÉRIE / LOTE DE CP" not in s2:
    raise SystemExit("Validação do novo layout de impressão falhou")
path.write_text(s2, encoding="utf-8")
print("Applied NTEC lab-style portrait PDF template to", path)
