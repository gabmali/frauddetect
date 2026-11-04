import {useState,type ReactNode} from 'react';
import {Download} from 'lucide-react';
import {params} from '../services/api';
import type {Filters} from '../types';
export function ExportButton({format,filters,children,className='button secondary'}:{format:string;filters:Filters;children?:ReactNode;className?:string}){
  const[busy,setBusy]=useState(false);const[message,setMessage]=useState('');
  async function download(){setBusy(true);setMessage('');try{
    let blob:Blob;
    if(import.meta.env.VITE_PAGES_DEMO==='true'){const{staticReport}=await import('../services/staticReports');blob=await staticReport(format,filters)}else{
    const response=await fetch('/api/reports/'+format+'?'+params(filters));
    if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:'Não foi possível gerar o arquivo. Verifique os filtros.')}
    blob=await response.blob();}
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='frauddetect.'+format;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);setMessage('Arquivo gerado. Confira os downloads do navegador.');
  }catch(e){setMessage((e as Error).message||'Falha na exportação. Tente novamente.')}finally{setBusy(false)}}
  return <div className="export-control"><button className={className} onClick={download} disabled={busy}><Download size={17}/>{busy?'Gerando arquivo…':children||'Exportar CSV'}</button>{message&&<p role="status" className="export-feedback">{message}</p>}</div>
}
