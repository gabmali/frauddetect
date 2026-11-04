import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({base:process.env.VITE_BASE_PATH||'/',plugins:[react()],server:{proxy:{'/api':process.env.FRAUDDETECT_API||'http://127.0.0.1:8000'}},test:{environment:'jsdom',setupFiles:['./src/test-setup.ts']}});
