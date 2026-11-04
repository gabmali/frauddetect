import React from 'react';
import {describe,it,expect,vi,beforeAll,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {ConfirmProvider} from './Confirm';
import {Detail} from './Detail';
import {useResource} from '../hooks/useResource';
import {api} from '../services/api';
vi.mock('../hooks/useResource',()=>({useResource:vi.fn()}));
vi.mock('../services/api',()=>({ApiError:class extends Error{},api:vi.fn(),json:(method:string,body:unknown)=>({method,body}),money:(value:number)=>'R$ '+value}));
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}});
afterEach(()=>{cleanup();vi.clearAllMocks()});
const transaction={id:'TX-QA',revision:0,customer_id:'CLI-QA',timestamp:'2026-10-31T12:00:00',amount:100,city:'Recife',state:'PE',kind:'Pix',channel:'Aplicativo',score:60,risk:'alto',status:'Pendente',note:'',reasons:['Repetição de operações'],recommendation:'Revisar',history:[]};
describe('Análise do alerta',()=>{
 it('protege a observação não salva e permite cancelar o fechamento',async()=>{
   vi.mocked(useResource).mockReturnValue({data:transaction,loading:false,error:'',reload:vi.fn()});const close=vi.fn();
   render(<ConfirmProvider><Detail id="TX-QA" onClose={close} onChange={vi.fn()}/></ConfirmProvider>);
   expect(screen.getByRole('button',{name:'Salvar análise'})).toBeDisabled();
   fireEvent.change(screen.getByPlaceholderText('Registre as evidências da sua revisão'),{target:{value:'Minha revisão'}});
   fireEvent.click(screen.getByRole('button',{name:'Fechar detalhes'}));
   fireEvent.click(screen.getByRole('button',{name:'Cancelar'}));
   await waitFor(()=>expect(screen.getByPlaceholderText('Registre as evidências da sua revisão')).toHaveValue('Minha revisão'));
   expect(close).not.toHaveBeenCalled();
 });
 it('salva com confirmação, mostra feedback e recarrega o histórico',async()=>{
   const reload=vi.fn(),changed=vi.fn();vi.mocked(useResource).mockReturnValue({data:transaction,loading:false,error:'',reload});vi.mocked(api).mockResolvedValue({message:'Análise registrada.'});
   render(<ConfirmProvider><Detail id="TX-QA" onClose={vi.fn()} onChange={changed}/></ConfirmProvider>);
   fireEvent.change(screen.getByPlaceholderText('Registre as evidências da sua revisão'),{target:{value:'Observação de QA'}});
   fireEvent.click(screen.getByRole('button',{name:'Salvar análise'}));fireEvent.click(screen.getByRole('button',{name:'Confirmar'}));
   await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('Análise registrada.'));
   expect(changed).toHaveBeenCalledOnce();expect(reload).toHaveBeenCalledOnce();expect(api).toHaveBeenCalledWith('/alerts/TX-QA',expect.objectContaining({method:'PATCH'}));
 });
});
