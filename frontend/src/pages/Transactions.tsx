import {useEffect,useState} from 'react';
import {ChevronLeft,ChevronRight,ArrowDownUp} from 'lucide-react';
import {useResource} from '../hooks/useResource';
import {params,money,number} from '../services/api';
import {Risk,State} from '../components/UI';
import {ExportButton} from '../components/ExportButton';
import type {Filters,Transaction} from '../types';

export function Transactions({filters,version,onOpen,alerts=false}:{filters:Filters;version:number;onOpen:(id:string)=>void;alerts?:boolean}){
  const filterId=params(filters);
  const [position,setPosition]=useState({key:filterId,page:1});
  const page=position.key===filterId?position.page:1;
  const setPage=(page:number)=>setPosition({key:filterId,page});
  const [sort,setSort]=useState(alerts?'score':'timestamp');
  const [direction,setDirection]=useState('desc');
  const [status,setStatus]=useState('');
  const {data,error,loading,reload}=useResource<{total:number;items:Transaction[]}>(
    (alerts?'/alerts?':'/transactions?')+filterId+`&page=${page}&sort=${sort}&direction=${direction}&status=${encodeURIComponent(status)}`,version);
  const pages=Math.max(1,Math.ceil((data?.total??0)/15));
  useEffect(()=>{if(data&&page>pages)setPage(pages)},[data,page,pages,filterId]);
  function order(key:string){setDirection(key===sort?(direction==='desc'?'asc':'desc'):key==='timestamp'||key==='score'?'desc':'asc');setSort(key);setPage(1)}
  function heading(key:string,label:string){return <th aria-sort={sort===key?(direction==='asc'?'ascending':'descending'):'none'}><button onClick={()=>order(key)}>{label}<ArrowDownUp size={12}/>{sort===key&&<span aria-hidden="true">{direction==='asc'?'↑':'↓'}</span>}</button></th>}
  return <section className="card transaction-card" aria-busy={loading}>
    <div className="table-toolbar"><div><h3>{alerts?'Fila de revisão':'Todas as transações'}</h3><p aria-live="polite">{loading?'Consultando registros…':data?number(data.total)+' registros encontrados':'Consulta indisponível'}</p></div>
    {alerts?<label>Status do alerta<select aria-label="Status do alerta" value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}><option value="">Todos os status</option>{['Pendente','Em análise','Resolvido','Falso positivo'].map(s=><option key={s}>{s}</option>)}</select></label>:<ExportButton format="csv" filters={filters}/>}</div>
    <State error={error} loading={loading}/>{error&&<button className="secondary button" onClick={reload}>Tentar novamente</button>}
    {data&&!loading&&!error&&<><div className="table-scroll" tabIndex={0} aria-label="Tabela de transações; role horizontalmente para ver todas as colunas"><table><caption className="sr-only">{alerts?'Alertas para revisão':'Transações filtradas'}. Selecione um identificador para abrir os detalhes.</caption><thead><tr>{heading('id','Transação')}{heading('timestamp','Data e horário')}<th scope="col">Cliente / local</th>{heading('amount','Valor')}<th scope="col">Tipo / canal</th>{heading('score','Score')}<th scope="col">Risco</th><th scope="col">Status</th></tr></thead><tbody>{data.items.map(t=><tr key={t.id}><td><button className="text-link" onClick={()=>onOpen(t.id)} aria-label={'Abrir transação '+t.id}>{t.id}</button><small>{t.category}</small></td><td>{new Date(t.timestamp).toLocaleDateString('pt-BR')}<small>{new Date(t.timestamp).toLocaleTimeString('pt-BR')}</small></td><td>{t.customer_id}<small>{t.city}, {t.state}</small></td><td className="amount">{money(t.amount)}</td><td>{t.kind}<small>{t.channel}</small></td><td><div className="score"><b>{t.score}</b><progress aria-label={'Score de risco '+t.score+' de 100'} value={t.score} max={100}/></div></td><td><Risk risk={t.risk}/></td><td><span className={'status status-'+t.status.replace(/ /g,'-')}>{t.status}</span></td></tr>)}</tbody></table></div>
    {!data.items.length&&<div className="empty"><strong>Nenhum registro encontrado</strong><p>Tente ampliar o período ou ajustar os filtros de busca e status.</p></div>}
    <div className="pagination"><span>{data.total?`${number((page-1)*15+1)}–${number(Math.min(page*15,data.total))} de ${number(data.total)} registros`:'0 registros'} · Página {page} de {pages}</span><div><button aria-label="Página anterior" disabled={page===1} onClick={()=>setPage(page-1)}><ChevronLeft size={16}/></button><button aria-label="Próxima página" disabled={page>=pages} onClick={()=>setPage(page+1)}><ChevronRight size={16}/></button></div></div></>}
  </section>
}
