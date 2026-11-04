import {useResource} from '../hooks/useResource';
export function DetectorStatus({version}:{version:number}){
 const{data,error,reload}=useResource<{available:boolean;message:string}>('/detector/status',version);
 if(data?.available&&!error)return null;
 if(!data&&!error)return null;
 return <section className="message error" role="alert"><strong>{error||data?.message}</strong><p>As classificações exibidas são do último processamento válido. Nenhuma nova avaliação será feita sem o modelo.</p><button className="button secondary" onClick={reload}>Verificar detector novamente</button></section>
}
