import React from 'react';
import {describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {Risk,State} from './UI';
import {Filters,initialFilters} from './Filters';
describe('Interface principal',()=>{it('comunica o risco sem afirmar fraude',()=>{render(<Risk risk="alto"/>);expect(screen.getByText('Alto risco')).toBeInTheDocument()});it('exibe falha de API de forma acessível',()=>{render(<State error="Conexão indisponível" loading={false}/>);expect(screen.getByRole('alert')).toHaveTextContent('Conexão indisponível')});it('envia o filtro de risco selecionado',()=>{const change=vi.fn();render(<Filters value={initialFilters} onChange={change}/>);fireEvent.change(screen.getByLabelText('Nível de risco'),{target:{value:'alto'}});expect(change).toHaveBeenCalledWith({...initialFilters,risk:'alto'})})});
