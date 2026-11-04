"""Hospedagem da demonstração: serve apenas o build e restringe gravações públicas."""
import os
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

def is_public_demo():
    return os.getenv('PUBLIC_DEMO','0')=='1'

def configure_hosting(app):
    @app.middleware('http')
    async def public_demo_guard(request,call_next):
        if is_public_demo() and request.url.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
            return JSONResponse(status_code=403,content={'detail':'Esta demonstração pública permite consultas e exportações. Execute o projeto localmente para importar dados, editar análises ou reavaliar regras.'})
        return await call_next(request)

    directory=Path(os.getenv('STATIC_DIR','frontend/dist'))
    if directory.is_dir():
        app.mount('/',StaticFiles(directory=str(directory),html=True),name='frontend')
