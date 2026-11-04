import {ApiError} from './api';
import type {Transaction,Model,Point} from '../types';
export type Snapshot={schema:number;cutoff:string;rules:Record<string,number>;models:Model[];transactions:Transaction[]};
let cached:Promise<Snapshot>|undefined;
export function snapshot(){
 if(!cached)cached=fetch(import.meta.env.BASE_URL+'demo.json').then(async response=>{if(!response.ok)throw new Error('Não foi possível carregar a base demonstrativa. Tente novamente.');const data=await response.json();if(data.schema!==1)throw new Error('Formato de demonstração incompatível. Atualize a página.');return data as Snapshot}).catch(error=>{cached=undefined;throw error});
 return cached;
}
export function filterRows(rows:Transaction[],p:URLSearchParams,dates=true){
 const min=Number(p.get('min_amount')||0),max=Number(p.get('max_amount')||1e12),start=p.get('start')||'',end=p.get('end')||'',q=(p.get('q')||'').toLocaleLowerCase('pt-BR'),risk=p.get('risk');
 if(min>max)throw new ApiError('O valor mínimo deve ser menor ou igual ao máximo.',422);
 if(start&&end&&start>end)throw new ApiError('A data inicial deve ser anterior ou igual à final.',422);
 return rows.filter(r=>r.amount>=min&&r.amount<=max&&(!risk||r.risk===risk)&&(!q||r.id.toLowerCase().includes(q)||r.customer_id.toLowerCase().includes(q))&&(!dates||(!start||r.timestamp>=start)&&(!end||r.timestamp<=end+'T23:59:59.999999')));
}
function week(value:string){const d=new Date(value.slice(0,10)+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+4-(d.getUTCDay()||7));const y=d.getUTCFullYear();return `${y}-S${String(Math.ceil(((d.getTime()-Date.UTC(y,0,1))/86400000+1)/7)).padStart(2,'0')}`}
function ranking(map:Map<string,number>):Point[]{return [...map].map(([name,value])=>({name,value})).sort((a,b)=>b.value-a.value||a.name.localeCompare(b.name,'pt-BR'))}
export function summarize(rows:Transaction[],group='dia'){
 const flagged=rows.filter(r=>r.score>=30),values=rows.map(r=>r.amount).sort((a,b)=>a-b),timeline=new Map<string,{date:string;total:number;alerts:number;amount:number}>(),reasons=new Map<string,number>(),categories=new Map<string,number>();
 const quantile=(p:number)=>{if(!values.length)return 0;const i=(values.length-1)*p,l=Math.floor(i);return values[l]+(values[Math.ceil(i)]-values[l])*(i-l)};
 const bins=[0,250,500,1000,2500,5000,10000,Infinity],histogram=bins.slice(0,-1).map((v,i)=>({name:bins[i+1]===Infinity?'10.000+':`${v}–${bins[i+1]}`,value:0}));
 for(const r of rows){const date=group==='semana'?week(r.timestamp):r.timestamp.slice(0,group==='mês'?7:10);const point=timeline.get(date)||{date,total:0,alerts:0,amount:0};point.total++;point.alerts+=Number(r.score>=30);point.amount+=r.amount;timeline.set(date,point);const bin=bins.findIndex((v,i)=>r.amount>=v&&r.amount<bins[i+1]);if(bin>=0)histogram[bin].value++;if(r.score>=30){categories.set(r.category,(categories.get(r.category)||0)+1);for(const reason of r.reasons)reasons.set(reason,(reasons.get(reason)||0)+1)}}
 const volume=values.reduce((s,v)=>s+v,0);
 return {total:rows.length,flagged:flagged.length,rate:rows.length?flagged.length/rows.length*100:0,volume,exposure:flagged.reduce((s,r)=>s+r.amount,0),mean:rows.length?volume/rows.length:0,median:quantile(.5),p95:quantile(.95),timeline:[...timeline.values()].sort((a,b)=>a.date.localeCompare(b.date)),risks:['baixo','médio','alto'].map(name=>({name,value:rows.filter(r=>r.risk===name).length})),reasons:ranking(reasons),categories:ranking(categories),histogram};
}
export function dashboard(rows:Transaction[],p:URLSearchParams){
 const filtered=filterRows(rows,p),group=p.get('group')||'dia',current=summarize(filtered,group);let previous=summarize([],group);
 if(filtered.length||(p.get('start')&&p.get('end'))){const dates=filtered.map(r=>r.timestamp.slice(0,10)).sort(),lo=new Date((p.get('start')||dates[0])+'T00:00:00Z').getTime(),hi=new Date((p.get('end')||dates[dates.length-1])+'T00:00:00Z').getTime()+86400000;const prior=new Date(lo-(hi-lo)).toISOString().slice(0,10),end=new Date(lo).toISOString().slice(0,10);previous=summarize(filterRows(rows,p,false).filter(r=>r.timestamp>=prior&&r.timestamp<end),group)}
 return {...current,previous};
}
function view(r:Transaction){return {...r,revision:0,status:r.score>=30?'Pendente':'Sem alerta',note:'',history:[]}}
export async function staticRequest<T>(path:string,options?:RequestInit):Promise<T>{
 if(options?.signal?.aborted)throw new DOMException('Consulta cancelada','AbortError');
 if(options?.method&&options.method!=='GET')throw new ApiError('Esta demonstração online é de consulta. O projeto completo no GitHub permite importar dados e salvar análises localmente.',403);
 const data=await snapshot(),[route,query='']=path.split('?'),p=new URLSearchParams(query);let result:unknown;
 if(route==='/detector/status')result={available:true,message:'Resultados calculados pelo Python',cutoff:data.cutoff};
 else if(route==='/models')result=data.models;
 else if(route==='/rules')result=data.rules;
 else if(route==='/dashboard')result=dashboard(data.transactions,p);
 else if(route.startsWith('/transactions/')){const r=data.transactions.find(r=>r.id===decodeURIComponent(route.slice('/transactions/'.length)));if(!r)throw new ApiError('Transação não encontrada.',404);result=view(r)}
 else if(route==='/transactions'||route==='/alerts'){
  let rows=filterRows(data.transactions,p);if(route==='/alerts'){rows=rows.filter(r=>r.score>=30);if(p.get('status')&&p.get('status')!=='Pendente')rows=[]}
  const sort=p.get('sort')||'timestamp',direction=p.get('direction')==='asc'?1:-1,key=(['timestamp','amount','score','id'].includes(sort)?sort:'timestamp') as 'timestamp'|'amount'|'score'|'id';rows=[...rows].sort((a,b)=>{const x=a[key],y=b[key];return (typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y)))*direction||a.id.localeCompare(b.id)});
  const page=Math.max(1,Number(p.get('page')||1)),size=Math.min(100,Math.max(1,Number(p.get('size')||15)));result={total:rows.length,items:rows.slice((page-1)*size,page*size).map(view)};
 }else throw new ApiError('Recurso não disponível nesta demonstração.',404);
 return result as T;
}
