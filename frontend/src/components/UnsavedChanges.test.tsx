import React,{useState} from 'react';
import {describe,it,expect,vi,beforeAll,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {ConfirmProvider} from './Confirm';
import {UnsavedProvider,useUnsavedChanges,useNavigationGuard} from './UnsavedChanges';
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}});
afterEach(cleanup);
function Editor({leave}:{leave:()=>void}){
 const[dirty,setDirty]=useState(false);useUnsavedChanges(dirty,'Descartar regras editadas?');const canLeave=useNavigationGuard();
 return <><button onClick={()=>setDirty(true)}>Editar regras</button><button onClick={()=>setDirty(false)}>Marcar salvo</button><button onClick={async()=>{if(await canLeave())leave()}}>Sair</button></>
}
describe('Proteção de regras não salvas',()=>{
 it('cancela a navegação, confirma o descarte e libera após salvar',async()=>{
  const leave=vi.fn();render(<ConfirmProvider><UnsavedProvider><Editor leave={leave}/></UnsavedProvider></ConfirmProvider>);
  fireEvent.click(screen.getByText('Editar regras'));fireEvent.click(screen.getByText('Sair'));
  fireEvent.click(screen.getByRole('button',{name:'Cancelar'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());expect(leave).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText('Sair'));fireEvent.click(screen.getByRole('button',{name:'Confirmar'}));await waitFor(()=>expect(leave).toHaveBeenCalledOnce());
  fireEvent.click(screen.getByText('Marcar salvo'));fireEvent.click(screen.getByText('Sair'));await waitFor(()=>expect(leave).toHaveBeenCalledTimes(2));
 });
 it('protege fechamento da página somente enquanto houver edição',()=>{
  render(<ConfirmProvider><UnsavedProvider><Editor leave={vi.fn()}/></UnsavedProvider></ConfirmProvider>);
  fireEvent.click(screen.getByText('Editar regras'));const dirtyEvent=new Event('beforeunload',{cancelable:true});window.dispatchEvent(dirtyEvent);expect(dirtyEvent.defaultPrevented).toBe(true);
  fireEvent.click(screen.getByText('Marcar salvo'));const cleanEvent=new Event('beforeunload',{cancelable:true});window.dispatchEvent(cleanEvent);expect(cleanEvent.defaultPrevented).toBe(false);
 });
});
