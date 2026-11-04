"""Hospedagem da demonstração: serve apenas o build e restringe gravações públicas."""
import os
import base64
import binascii
import hmac
from pathlib import Path
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

def is_public_demo():
    return os.getenv('PUBLIC_DEMO','0')=='1'

def configure_hosting(app):
    @app.get('/healthz',include_in_schema=False)
    def readiness(): return {'status':'ok'}

    @app.middleware('http')
    async def public_demo_guard(request,call_next):
        headers={'X-Robots-Tag':'noindex, nofollow, noarchive'}
        if request.url.path=='/robots.txt':
            return PlainTextResponse('User-agent: *\nDisallow: /\n',headers=headers)
        if os.getenv('REQUIRE_DEMO_AUTH','0')=='1' and request.url.path!='/healthz':
            password=os.getenv('DEMO_ACCESS_PASSWORD','')
            if len(password)<16:
                return JSONResponse(status_code=503,content={'detail':'A demonstração está aguardando a configuração de acesso.'},headers=headers)
            authenticated=False
            try:
                scheme,encoded=request.headers.get('authorization','').split(' ',1)
                user,provided=base64.b64decode(encoded,validate=True).split(b':',1)
                authenticated=(scheme.lower()=='basic' and hmac.compare_digest(user,os.getenv('DEMO_ACCESS_USER','recrutador').encode()) and hmac.compare_digest(provided,password.encode()))
            except (ValueError,binascii.Error):
                pass
            if not authenticated:
                return JSONResponse(status_code=401,content={'detail':'Acesso restrito. Informe as credenciais fornecidas pela desenvolvedora.'},headers={**headers,'WWW-Authenticate':'Basic realm="FraudDetect - Recrutadores", charset="UTF-8"'})
        if is_public_demo() and request.url.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
            return JSONResponse(status_code=403,content={'detail':'Esta demonstração permite consultas e exportações. Execute o projeto localmente para importar dados, editar análises ou reavaliar regras.'},headers=headers)
        response=await call_next(request)
        response.headers.update(headers)
        if os.getenv('REQUIRE_DEMO_AUTH','0')=='1':response.headers['Cache-Control']='private, no-store'
        return response

    directory=Path(os.getenv('STATIC_DIR','frontend/dist'))
    if directory.is_dir():
        app.mount('/',StaticFiles(directory=str(directory),html=True),name='frontend')
