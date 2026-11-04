import React from 'react';
import {describe,it,expect,vi,beforeAll,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {ConfirmProvider,useConfirm} from './Confirm';
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}});
afterEach(cleanup);
function Example({onFinish}:{onFinish:(v:boolean)=>void}){const confirm=useConfirm();return <button onClick={async()=>onFinish(await confirm('Salvar as alterações?'))}>Solicitar confirmação</button>}
describe('Confirmações acessíveis',()=>{
 it.each([['Confirmar',true],['Cancelar',false]] as const)('retorna o resultado de %s sem usar confirmação nativa',async(label,value)=>{
   const result=vi.fn();const native=vi.spyOn(window,'confirm');
   render(<ConfirmProvider><Example onFinish={result}/></ConfirmProvider>);
   fireEvent.click(screen.getByRole('button',{name:'Solicitar confirmação'}));
   expect(screen.getByRole('dialog',{name:'Confirmar ação'})).toHaveAccessibleDescription('Salvar as alterações?');
   fireEvent.click(screen.getByRole('button',{name:label}));
   await waitFor(()=>expect(result).toHaveBeenCalledWith(value));
   expect(native).not.toHaveBeenCalled();native.mockRestore();
 });
});
