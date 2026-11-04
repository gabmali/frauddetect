import {createContext,useCallback,useContext,useEffect,useRef,type ReactNode} from 'react';
import {useConfirm} from './Confirm';
type Guard={dirty:boolean;message:string};
const Context=createContext<{register:(guard:Guard)=>()=>void;canLeave:()=>Promise<boolean>}>({register:()=>()=>{},canLeave:async()=>true});
export function UnsavedProvider({children}:{children:ReactNode}){
 const guard=useRef<Guard>();const confirm=useConfirm();
 const register=useCallback((value:Guard)=>{guard.current=value;return()=>{if(guard.current===value)guard.current=undefined}},[]);
 const canLeave=useCallback(async()=>!guard.current?.dirty||await confirm(guard.current.message),[confirm]);
 return <Context.Provider value={{register,canLeave}}>{children}</Context.Provider>
}
export function useUnsavedChanges(dirty:boolean,message:string){
 const{register}=useContext(Context);
 useEffect(()=>register({dirty,message}),[dirty,message,register]);
 useEffect(()=>{if(!dirty)return;function warn(event:BeforeUnloadEvent){event.preventDefault();event.returnValue=''}window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn)},[dirty]);
}
export const useNavigationGuard=()=>useContext(Context).canLeave;
