import {ExportButton} from '../components/ExportButton';
import {useResource} from '../hooks/useResource';
import {params,money,number} from '../services/api';
import {Card,Metrics,State} from '../components/UI';
import type {Dashboard,Filters} from '../types';
export function Reports({filters,version}:{filters:Filters;version:number}){
 const{data:d,error,loading,reload}=useResource<Dashboard>('/dashboard?'+params(filters),version);
 return <><State error={error} loading={loading}/>{error&&<button className="button secondary" onClick={reload}>Tentar novamente</button>}
 {d&&!loading&&<><Metrics d={d}/><Card title="Comparação com o período anterior" subtitle="Janela imediatamente anterior com a mesma duração do período selecionado"><div className="report-comparison"><div><small>Transações · atual / anterior</small><strong>{number(d.total)} / {number(d.previous.total)}</strong></div><div><small>Sinalizadas · atual / anterior</small><strong>{d.rate.toLocaleString('pt-BR',{maximumFractionDigits:2})}% / {d.previous.rate.toLocaleString('pt-BR',{maximumFractionDigits:2})}%</strong></div><div><small>Volume anterior</small><strong>{money(d.previous.volume)}</strong></div></div>{!d.previous.total&&<p>Não há dados no período anterior para uma comparação representativa.</p>}</Card>
 <Card title="Exportar relatório" subtitle="Os filtros da página se aplicam a todos os arquivos"><div className="exports">{['csv','xlsx','pdf'].map(f=><ExportButton key={f} format={f} filters={filters} className="export-tile"><strong>{f==='xlsx'?'Excel':f.toUpperCase()}</strong><span>{f==='pdf'?'Resumo, evolução e métricas':'Transações filtradas'}</span></ExportButton>)}</div><p className="muted">Métricas dos modelos usam o conjunto sintético de teste global, independente dos filtros. Alto risco não confirma fraude.</p></Card></>}</>
}
