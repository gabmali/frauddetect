import {createContext,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
type Confirm=(message:string)=>Promise<boolean>;
const Context=createContext<Confirm|null>(null);
export function useConfirm(){const confirm=useContext(Context);if(!confirm)throw new Error('Confirmação indisponível');return confirm}
function Confirmation({message,onFinish}:{message:string;onFinish:(v:boolean)=>void}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement;ref.current?.showModal();return()=>{ref.current?.close();previous?.focus()}},[]);
 return <dialog ref={ref} className="confirmation" aria-labelledby="confirm-title" aria-describedby="confirm-message" onCancel={e=>{e.preventDefault();onFinish(false)}}>
 <h2 id="confirm-title">Confirmar ação</h2><p id="confirm-message">{message}</p><div><button className="button secondary" autoFocus onClick={()=>onFinish(false)}>Cancelar</button><button className="primary" onClick={()=>onFinish(true)}>Confirmar</button></div></dialog>
}
export function ConfirmProvider({children}:{children:ReactNode}){
 const[pending,setPending]=useState<{message:string;resolve:(value:boolean)=>void}>();
 function ask(message:string){return new Promise<boolean>(resolve=>setPending({message,resolve}))}
 return <Context.Provider value={ask}>{children}{pending&&<Confirmation message={pending.message} onFinish={value=>{pending.resolve(value);setPending(undefined)}}/>}</Context.Provider>
}
