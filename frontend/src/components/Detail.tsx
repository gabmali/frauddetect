import {publicDemo} from '../services/demo';
import {useConfirm} from './Confirm';

import {useEffect,useRef,useState} from 'react';

import {X} from 'lucide-react';

import {useResource} from '../hooks/useResource';

import {api,json,money,ApiError} from '../services/api';

import {Risk,State} from './UI';

import type {Transaction} from '../types';

export function Detail({id,onClose,onChange}:{id:string;onClose:()=>void;onChange:()=>void}){

  const confirmAction=useConfirm();

  const{data:t,error,loading,reload}=useResource<Transaction>('/transactions/'+encodeURIComponent(id));

  const dialog=useRef<HTMLDialogElement>(null);const[status,setStatus]=useState('Pendente');const[note,setNote]=useState('');const[message,setMessage]=useState('');const[conflict,setConflict]=useState(false);const[busy,setBusy]=useState(false);

  const dirty=!!t&&(status!==t.status||note!==(t.note||''));

  async function close(){if(busy)return;if(dirty&&!await confirmAction('Descartar as alterações não salvas desta análise?'))return;onClose()}

  useEffect(()=>{const previous=document.activeElement as HTMLElement;dialog.current?.showModal();return()=>previous?.focus()},[]);

  useEffect(()=>{if(t){setStatus(t.status);setNote(t.note||'')}},[t]);

  return <dialog ref={dialog} className="detail" aria-labelledby="detail-title" onCancel={e=>{e.preventDefault();close()}} onClick={e=>{if(e.target===dialog.current)close()}}>

    <div className="detail-header"><div><span className="eyebrow">DETALHES DA OPERAÇÃO</span><h2 id="detail-title">{id}</h2></div><button onClick={close} disabled={busy} aria-label="Fechar detalhes"><X/></button></div>

    <State error={error} loading={loading}/>{error&&<button className="button secondary" onClick={reload}>Tentar novamente</button>}

    {message&&<p className="message" role="status">{message}</p>}

    {conflict&&<button className="button secondary" onClick={async()=>{if(await confirmAction('Carregar a análise atual? Copie sua observação antes de continuar: o texto local será substituído.')){setConflict(false);setMessage('');reload()}}}>Carregar versão atual</button>}

    {t&&!loading&&<><div className="detail-value"><strong>{money(t.amount)}</strong><Risk risk={t.risk}/></div><dl>{[['Cliente',t.customer_id],['Data',new Date(t.timestamp).toLocaleString('pt-BR')],['Local',t.city+' / '+t.state],['Tipo e canal',t.kind+' · '+t.channel],['Score híbrido',t.score+'/100'],['Pontos das regras',(t.rule_score??t.score)+'/100'],['Indicador do modelo',t.model_score==null?'Não avaliado: evento anterior ao corte de treino':t.model_score.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+'/100 (não calibrado)']].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>

    <h3>Motivos da classificação</h3>{t.reasons.length?<ul>{t.reasons.map(r=><li key={r}>{r}</li>)}</ul>:<p>Nenhuma regra acionada.</p>}

    <p className="notice">{t.recommendation}. Uma sinalização não comprova fraude.</p>

    {t.status!=='Sem alerta'&&<form onSubmit={async e=>{e.preventDefault();if(!await confirmAction('Registrar esta análise no histórico?'))return;setBusy(true);setMessage('');try{const r=await api<{message:string}>('/alerts/'+encodeURIComponent(id),json('PATCH',{status,note,revision:t.revision}));setMessage(r.message);onChange();reload()}catch(e){setMessage((e as Error).message);if(e instanceof ApiError&&e.status===409)setConflict(true)}finally{setBusy(false)}}}>

      <label>Status<select value={status} disabled={busy} onChange={e=>setStatus(e.target.value)}>{['Pendente','Em análise','Resolvido','Falso positivo'].map(s=><option key={s}>{s}</option>)}</select></label>

      <label>Observações<textarea disabled={busy} maxLength={2000} value={note} onChange={e=>setNote(e.target.value)} placeholder="Registre as evidências da sua revisão"/><small>{note.length}/2.000 caracteres</small></label>

      <button className="primary" disabled={publicDemo||busy||!dirty||conflict}>{busy?'Salvando…':'Salvar análise'}</button>

    </form>}

    <h3>Histórico de alterações</h3>{t.history?.length?<ol className="history-list">{[...t.history].reverse().map((h,i)=><li key={i}><b>{h.status}</b><small>{new Date(h.timestamp).toLocaleString('pt-BR')}</small><p>{h.note||'Sem observações.'}</p></li>)}</ol>:<p className="muted">Nenhuma alteração registrada.</p>}</>}

  </dialog>

}
