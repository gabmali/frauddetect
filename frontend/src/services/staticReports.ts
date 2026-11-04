import {snapshot,filterRows,dashboard} from './staticDemo';
import {params,money} from './api';
import type {Filters,Transaction} from '../types';
const headers=['Transação','Cliente','Data','Valor (BRL)','Cidade','UF','Categoria','Tipo','Canal','Score','Risco','Status','Motivos'];
function cells(r:Transaction){return [r.id,r.customer_id,r.timestamp,r.amount,r.city,r.state,r.category,r.kind,r.channel,r.score,r.risk,r.score>=30?'Pendente':'Sem alerta',r.reasons.join(' | ')]}
// Planilhas não devem interpretar conteúdo textual como fórmulas.
export function csvCell(value:unknown){const text=String(value??'');return '"'+(/^[\s]*[=+@-]/.test(text)?"'"+text:text).replace(/"/g,'""')+'"'}
export async function staticReport(format:string,filters:Filters):Promise<Blob>{
 const data=await snapshot(),p=new URLSearchParams(params(filters)),rows=filterRows(data.transactions,p);
 if(format==='csv')return new Blob(['\ufeff'+[headers,...rows.map(cells)].map(row=>row.map(csvCell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});
 if(format==='xlsx'){
  const {default:writeExcelFile}=await import('write-excel-file/universal');
  const data=[headers.map(value=>({value,fontWeight:'bold' as const,color:'#FFFFFF',backgroundColor:'#23476B'})),...rows.map(row=>cells(row).map((value,i)=>({value,...(i===3?{format:'"R$" #,##0.00'}:{})})))];
  return writeExcelFile(data,{sheet:'Transações',columns:[22,18,25,18,23,8,22,18,18,10,12,18,70].map(width=>({width}))}).toBlob();
 }
 if(format==='pdf'){
  const {jsPDF}=await import('jspdf');const doc=new jsPDF();const d=dashboard(data.transactions,p);let y=20;
  const line=(text:string,bold=false)=>{doc.setFont('helvetica',bold?'bold':'normal');for(const part of doc.splitTextToSize(text,175)){if(y>275){doc.addPage();y=20}doc.text(part,18,y);y+=6}};
  doc.setFontSize(16);line('FraudDetect — Relatório de risco',true);doc.setFontSize(10);y+=3;
  line('Dados fictícios para demonstração de portfólio. Sinalização não comprova fraude.');line('Filtros: '+(p.toString()||'Todos os registros'));y+=4;
  line(`Transações: ${d.total.toLocaleString('pt-BR')} | Sinalizadas: ${d.flagged.toLocaleString('pt-BR')} (${d.rate.toFixed(2)}%)`,true);
  line('Volume: '+money(d.volume)+' | Exposição: '+money(d.exposure));line('Média: '+money(d.mean)+' | Mediana: '+money(d.median)+' | P95: '+money(d.p95));
  line(`Período anterior: ${d.previous.total} transações, ${d.previous.rate.toFixed(2)}% sinalizadas.`);y+=4;
  line('Evolução diária: data | transações | sinalizadas',true);for(const point of d.timeline)line(`${point.date} | ${point.total} | ${point.alerts}`);
  y+=4;line('Avaliação global dos modelos em dados sintéticos',true);for(const model of data.models){line(model.name,true);line(`Precisão ${(model.precision*100).toFixed(1)}% | Recall ${(model.recall*100).toFixed(1)}% | F1 ${(model.f1*100).toFixed(1)}% | PR-AUC ${(model.pr_auc*100).toFixed(1)}%`);line(`Treino: ${model.train_size} | Teste: ${model.test_size}`)}
  for(let i=1;i<=doc.getNumberOfPages();i++){doc.setPage(i);doc.setFontSize(9);doc.text(`FraudDetect | ${i}/${doc.getNumberOfPages()}`,18,290)}return doc.output('blob');
 }
 throw new Error('Formato de relatório inválido.');
}
