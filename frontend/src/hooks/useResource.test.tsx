import {describe,it,expect,vi} from 'vitest';
import {renderHook,waitFor} from '@testing-library/react';
import {useResource} from './useResource';
import {api} from '../services/api';
vi.mock('../services/api',()=>({api:vi.fn()}));
describe('Consistência de consultas',()=>{
 it('remove os dados antigos quando o novo recorte falha',async()=>{
   vi.mocked(api).mockResolvedValueOnce({total:50}).mockRejectedValueOnce(new Error('Período inválido'));
   const{result,rerender}=renderHook(({path})=>useResource<{total:number}>(path),{initialProps:{path:'/dashboard'}});
   await waitFor(()=>expect(result.current.data?.total).toBe(50));
   rerender({path:'/dashboard?start=bad'});
   await waitFor(()=>expect(result.current.error).toBe('Período inválido'));
   expect(result.current.data).toBeUndefined();
 });
});
