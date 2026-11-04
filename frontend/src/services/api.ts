export class ApiError extends Error{constructor(message:string,public status:number){super(message)}}
import type {Filters} from '../types';
export function params(filters:Filters){return new URLSearchParams(Object.entries(filters).filter(([,v])=>v!=='' )).toString()}
export async function api<T>(path:string,options?:RequestInit):Promise<T>{if(import.meta.env.VITE_PAGES_DEMO==='true'){const{staticRequest}=await import('./staticDemo');return staticRequest<T>(path,options)}let res:Response;try{res=await fetch('/api'+path,options)}catch(e){if((e as Error).name==='AbortError')throw e;throw new Error('Não foi possível conectar ao servidor. Verifique a conexão e tente novamente.')}if(!res.ok){const error=await res.json().catch(()=>({}));throw new ApiError(typeof error.detail==='string'?error.detail:res.status>=500?'O servidor não conseguiu concluir a operação. Tente novamente.':'Confira os filtros e os campos informados.',res.status)}return res.json()}
export function json(method:string,body:unknown):RequestInit{return {method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}}
export const money=(v:number)=>v.toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
export const number=(v:number)=>v.toLocaleString('pt-BR');
