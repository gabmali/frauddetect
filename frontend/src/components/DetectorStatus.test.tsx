import React from 'react';
import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {DetectorStatus} from './DetectorStatus';
import {useResource} from '../hooks/useResource';
vi.mock('../hooks/useResource',()=>({useResource:vi.fn()}));
afterEach(cleanup);
describe('Disponibilidade do detector',()=>{
 it('exibe aviso persistente quando o modelo não está disponível',()=>{
  vi.mocked(useResource).mockReturnValue({data:{available:false,message:'Modelo indisponível'},error:'',loading:false,reload:vi.fn()});render(<DetectorStatus version={0}/>);
  expect(screen.getByRole('alert')).toHaveTextContent('Modelo indisponível');expect(screen.getByRole('alert')).toHaveTextContent('último processamento válido');
 });
 it('não exibe alerta quando o modelo foi validado',()=>{
  vi.mocked(useResource).mockReturnValue({data:{available:true,message:'Disponível'},error:'',loading:false,reload:vi.fn()});render(<DetectorStatus version={0}/>);expect(screen.queryByRole('alert')).not.toBeInTheDocument();
 });
});
