import {SlidersHorizontal,RotateCcw} from 'lucide-react';
import type {Filters as FilterType} from '../types';
export const initialFilters:FilterType={q:'',risk:'',start:'',end:'',min_amount:'',max_amount:''};
export function Filters({value,onChange}:{value:FilterType;onChange:(v:FilterType)=>void}){
 function field(k:keyof FilterType,v:string){onChange({...value,[k]:v})}
 const badDates=!!(value.start&&value.end&&value.start>value.end);
 const badValues=!!(value.min_amount&&value.max_amount&&Number(value.min_amount)>Number(value.max_amount));
 return <><div className="filters"><span className="filter-title"><SlidersHorizontal size={17}/> Filtros</span>
 <label>De<input aria-invalid={badDates} type="date" min="2000-01-01" max={value.end||'2100-12-31'} value={value.start} onChange={e=>field('start',e.target.value)}/></label>
 <label>Até<input aria-invalid={badDates} type="date" min={value.start||'2000-01-01'} max="2100-12-31" value={value.end} onChange={e=>field('end',e.target.value)}/></label>
 <label>Nível de risco<select aria-label="Nível de risco" value={value.risk} onChange={e=>field('risk',e.target.value)}><option value="">Todos os níveis</option>{['baixo','médio','alto'].map(r=><option key={r} value={r}>{r==='baixo'?'Baixo':r==='médio'?'Médio':'Alto'}</option>)}</select></label>
 <label>Valor mínimo<input aria-invalid={badValues} type="number" step="0.01" min="0" max="1000000000" placeholder="R$ 0,00" value={value.min_amount} onChange={e=>field('min_amount',e.target.value)}/></label>
 <label>Valor máximo<input aria-invalid={badValues} type="number" step="0.01" min="0" max="1000000000" placeholder="Sem limite" value={value.max_amount} onChange={e=>field('max_amount',e.target.value)}/></label>
 <button className="ghost" aria-label="Limpar filtros" onClick={()=>onChange(initialFilters)}><RotateCcw size={17}/><span>Limpar</span></button></div>
 {(badDates||badValues)&&<p role="alert" className="error filter-error">{badDates?'A data inicial deve ser anterior ou igual à data final.':'O valor mínimo deve ser menor ou igual ao valor máximo.'}</p>}</>
}
