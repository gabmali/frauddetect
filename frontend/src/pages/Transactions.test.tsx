import React from 'react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {Transactions} from './Transactions';
import {initialFilters} from '../components/Filters';
import {useResource} from '../hooks/useResource';
vi.mock('../hooks/useResource',()=>({useResource:vi.fn()}));
const resource=vi.mocked(useResource);
beforeEach(()=>{cleanup();resource.mockReturnValue({data:{total:0,items:[]},error:'',loading:false,reload:vi.fn()})});
describe('Regressões da tabela',()=>{
 it('preserva status ao aplicar outro filtro e retorna à primeira página',()=>{
   const {rerender}=render(<Transactions filters={initialFilters} version={0} onOpen={vi.fn()} alerts/>);
   fireEvent.change(screen.getByLabelText('Status do alerta'),{target:{value:'Em análise'}});
   rerender(<Transactions filters={{...initialFilters,risk:'alto'}} version={0} onOpen={vi.fn()} alerts/>);
   expect(screen.getByLabelText('Status do alerta')).toHaveValue('Em análise');
   expect(resource.mock.calls[resource.mock.calls.length-1]?.[0]).toContain('status=Em%20an%C3%A1lise');
   expect(resource.mock.calls[resource.mock.calls.length-1]?.[0]).toContain('page=1');
 });
 it('ordena alertas por valor e comunica a direção',()=>{
   render(<Transactions filters={initialFilters} version={0} onOpen={vi.fn()} alerts/>);
   fireEvent.click(screen.getByRole('button',{name:'Valor'}));
   expect(resource.mock.calls[resource.mock.calls.length-1]?.[0]).toContain('sort=amount&direction=asc');
   expect(screen.getByRole('columnheader',{name:/Valor/})).toHaveAttribute('aria-sort','ascending');
 });
 it('oferece nova tentativa quando a consulta falha',()=>{
   const retry=vi.fn();resource.mockReturnValue({data:undefined,error:'Falha de conexão',loading:false,reload:retry});
   render(<Transactions filters={initialFilters} version={0} onOpen={vi.fn()}/>);
   fireEvent.click(screen.getByRole('button',{name:'Tentar novamente'}));expect(retry).toHaveBeenCalledOnce();
 });
});
