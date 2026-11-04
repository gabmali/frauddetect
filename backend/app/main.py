from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
from collections import Counter
import json, secrets, time
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, func
from .database import Session, Transaction, Customer, Alert, History, ModelResult, Setting, initialize, persist_analysis
from .engine import DEFAULT_RULES, analyze, score_features, hybrid, detector_status, ModelUnavailableError
from .importing import preview, REQUIRED
import os
from threading import RLock
mutation_lock=RLock()

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app=FastAPI(title='FraudDetect — API demonstrativa',lifespan=lifespan)
@app.exception_handler(ModelUnavailableError)
async def unavailable_model(request,error):
    return JSONResponse(status_code=503,content={'detail':str(error)})

@app.get('/api/detector/status')
def detector(): return detector_status()
app.add_middleware(CORSMiddleware,allow_origins=[os.getenv('FRONTEND_ORIGIN','http://localhost:5173')],allow_methods=['GET','POST','PATCH','PUT'],allow_headers=['Content-Type'])

class Filters:
    def __init__(self,q: str=Query('',max_length=100),risk: str=Query('',pattern='^(|baixo|médio|alto)$'),start: str='',end: str='',min_amount: float=Query(0,ge=0),max_amount: float=Query(1e12,ge=0)):
        self.q=q; self.risk=risk; self.start=start; self.end=end; self.min_amount=min_amount; self.max_amount=max_amount
        for d in (start,end):
            if d:
                try:
                    parsed=datetime.strptime(d,'%Y-%m-%d')
                    if not 2000<=parsed.year<=2100: raise ValueError()
                except ValueError: raise HTTPException(422,'Data inválida. Use AAAA-MM-DD.')
        if start and end and start>end: raise HTTPException(422,'Período inválido.')
        if min_amount>max_amount: raise HTTPException(422,'Intervalo de valores inválido.')

from fastapi import Depends

def filtered(s,f):
    query=s.query(Transaction).filter(Transaction.amount>=f.min_amount,Transaction.amount<=f.max_amount)
    if f.q: query=query.filter(or_(Transaction.id.contains(f.q,autoescape=True),Transaction.customer_id.contains(f.q,autoescape=True)))
    if f.risk: query=query.filter(Transaction.risk==f.risk)
    if f.start: query=query.filter(Transaction.timestamp>=f.start)
    if f.end: query=query.filter(Transaction.timestamp<=f.end+'T23:59:59.999999')
    return query

def serialize(t,s):
    alert=s.get(Alert,t.id)
    revision=s.query(func.max(History.id)).filter_by(alert_id=t.id).scalar() or 0
    return dict(t.data,status=alert.status if alert else 'Sem alerta',revision=revision)

@app.get('/api/health')
def health():
    model=detector_status()
    return {'status':'ok' if model['available'] else 'degraded','mode':'Dados 100% sintéticos','detector':model}

@app.get('/api/transactions')
def transactions(f: Filters=Depends(),page:int=Query(1,ge=1),size:int=Query(15,ge=1,le=100),sort:str=Query('timestamp',pattern='^(timestamp|amount|score|id)$'),direction:str=Query('desc',pattern='^(asc|desc)$')):
    with Session() as s:
        query=filtered(s,f); col=getattr(Transaction,sort)
        rows=query.order_by(col.desc() if direction=='desc' else col.asc(),Transaction.id).offset((page-1)*size).limit(size).all()
        return dict(total=query.count(),items=[serialize(t,s) for t in rows])

@app.get('/api/transactions/{id}')
def detail(id:str):
    with Session() as s:
        t=s.get(Transaction,id)
        if not t: raise HTTPException(404,'Transação não encontrada.')
        return dict(serialize(t,s),note=s.get(Alert,id).note if s.get(Alert,id) else '',history=[dict(timestamp=h.timestamp,status=h.status,note=h.note) for h in s.query(History).filter_by(alert_id=id).order_by(History.id)])

def aggregate(rows, group):
    total=len(rows); flagged=[r for r in rows if r['score']>=30]
    dates={}; categories=Counter(); reasons=Counter(); risks=Counter(r['risk'] for r in rows)
    for r in rows:
        d=datetime.fromisoformat(r['timestamp']); key=d.strftime('%Y-%m-%d') if group=='dia' else d.strftime('%G-S%V') if group=='semana' else d.strftime('%Y-%m')
        point=dates.setdefault(key,dict(date=key,total=0,alerts=0,amount=0)); point['total']+=1;point['alerts']+=int(r['score']>=30);point['amount']+=r['amount']
        if r['score']>=30:
            categories[r['category']]+=1
            reasons.update(r['reasons'])
    amounts=[r['amount'] for r in rows]
    hist,bins=np.histogram(amounts,bins=[0,250,500,1000,2500,5000,10000,float('inf')])
    return dict(total=total,flagged=len(flagged),rate=len(flagged)/total*100 if total else 0,exposure=sum(r['amount'] for r in flagged),volume=sum(amounts),mean=float(np.mean(amounts)) if amounts else 0,median=float(np.median(amounts)) if amounts else 0,p95=float(np.percentile(amounts,95)) if amounts else 0,timeline=list(sorted(dates.values(),key=lambda x:x['date'])),risks=[dict(name=k,value=risks[k]) for k in ['baixo','médio','alto']],reasons=[dict(name=k,value=v) for k,v in reasons.most_common()],categories=[dict(name=k,value=v) for k,v in categories.most_common()],histogram=[dict(name=f'{int(bins[i])}–{int(bins[i+1]) if np.isfinite(bins[i+1]) else "+"}',value=int(v)) for i,v in enumerate(hist)])

@app.get('/api/dashboard')
def dashboard(f:Filters=Depends(),group:str=Query('dia',pattern='^(dia|semana|mês)$')):
    with Session() as s:
        rows=[t.data for t in filtered(s,f).all()]; result=aggregate(rows,group)
        if rows or (f.start and f.end):
            from datetime import timedelta
            lo=datetime.fromisoformat(f.start) if f.start else datetime.fromisoformat(min(r['timestamp'] for r in rows)).replace(hour=0,minute=0,second=0,microsecond=0)
            hi=datetime.fromisoformat(f.end) if f.end else datetime.fromisoformat(max(r['timestamp'] for r in rows)).replace(hour=0,minute=0,second=0,microsecond=0)
            hi+=timedelta(days=1)
            duration=hi-lo
            prior=filtered(s,Filters(q=f.q,risk=f.risk,start='',end='',min_amount=f.min_amount,max_amount=f.max_amount)).filter(Transaction.timestamp>=(lo-duration).isoformat(),Transaction.timestamp<lo.isoformat()).all()
            result['previous']=aggregate([t.data for t in prior],group)
        else: result['previous']=aggregate([],group)
        return result

@app.get('/api/models')
def models():
    with Session() as s: return [r.data for r in s.query(ModelResult).all()]

@app.get('/api/alerts')
def alerts(f:Filters=Depends(),status:str=Query('',pattern='^(|Pendente|Em análise|Resolvido|Falso positivo)$'),page:int=Query(1,ge=1),size:int=Query(15,ge=1,le=100),sort:str=Query('score',pattern='^(timestamp|amount|score|id)$'),direction:str=Query('desc',pattern='^(asc|desc)$')):
    with Session() as s:
        query=filtered(s,f).join(Alert,Alert.id==Transaction.id)
        if status: query=query.filter(Alert.status==status)
        col=getattr(Transaction,sort)
        return dict(total=query.count(),items=[dict(serialize(t,s),note=s.get(Alert,t.id).note) for t in query.order_by(col.desc() if direction=='desc' else col.asc(),Transaction.id).offset((page-1)*size).limit(size)])

class AlertUpdate(BaseModel):
    status:str=Field(pattern='^(Pendente|Em análise|Resolvido|Falso positivo)$')
    note:str=Field('',max_length=2000)
    revision:int=Field(ge=0)

@app.patch('/api/alerts/{id}')
def update_alert(id:str,body:AlertUpdate):
    with Session() as s:
        # Reserva de escrita antes da leitura, inclusive entre processos SQLite.
        s.connection().exec_driver_sql('BEGIN IMMEDIATE')
        a=s.get(Alert,id)
        if not a: raise HTTPException(404,'Alerta não encontrado.')
        revision=s.query(func.max(History.id)).filter_by(alert_id=id).scalar() or 0
        if revision!=body.revision:
            raise HTTPException(409,'Este alerta foi alterado em outra aba. Carregue a versão atual antes de salvar; seu texto foi preservado.')
        a.status=body.status;a.note=body.note
        s.add(History(alert_id=id,timestamp=datetime.now().isoformat(),status=a.status,note=a.note));s.commit()
    return {'message':'Análise registrada.'}

class Rules(BaseModel):
    value_multiple:float=Field(4,ge=1,le=50)
    velocity_count:int=Field(4,ge=2,le=100)
    velocity_minutes:int=Field(10,ge=1,le=120)
    geo_minutes:int=Field(60,ge=1,le=360)
    repeat_count:int=Field(3,ge=2,le=100)

@app.get('/api/rules')
def get_rules():
    with Session() as s:
        r=s.get(Setting,'rules');return r.data if r else DEFAULT_RULES

@app.put('/api/rules')
def put_rules(body:Rules):
    with mutation_lock, Session() as s:
        rows=hybrid(analyze([t.data for t in s.query(Transaction).all()],body.model_dump()))
        persist_analysis(s,rows)
        s.merge(Setting(id='rules',data=body.model_dump()));s.commit()
    return {'message':'Regras salvas e transações reavaliadas. Alertas históricos preservados.'}

pending={}
@app.post('/api/import/preview')
async def import_preview(file:UploadFile=File(...)):
    content=await file.read(5*1024*1024+1)
    try: result=preview(content,file.filename or '')
    except Exception as e:
        if isinstance(e,ValueError): raise HTTPException(422,str(e))
        raise HTTPException(422,'Não foi possível ler o arquivo. Verifique o formato e as colunas.')
    with Session() as s:
        ids={r[0] for r in s.query(Transaction.id).all()}
    duplicates=[r for r in result['rows'] if r['id'] in ids]
    result['rows']=[r for r in result['rows'] if r['id'] not in ids];result['valid']=len(result['rows']);result['duplicates']=len(duplicates)
    now=time.monotonic()
    for k in list(pending):
        if pending[k][0]<now-900: del pending[k]
    if result['valid'] and len(pending)>=10: raise HTTPException(429,'Há muitas prévias abertas. Aguarde 15 minutos.')
    token=secrets.token_urlsafe(24) if result['valid'] else None
    if token: pending[token]=(now,result['rows'])
    return dict(result,rows=result['rows'][:10],token=token)

class Confirmation(BaseModel):
    token:str=Field(max_length=100)
    confirmed:bool

@app.post('/api/import/confirm')
def import_confirm(body:Confirmation):
    entry=pending.get(body.token)
    if not body.confirmed or not entry or entry[0]<time.monotonic()-900: raise HTTPException(422,'Confirmação inválida ou expirada. Gere uma nova prévia.')
    with mutation_lock, Session() as s:
        existing=[t.data for t in s.query(Transaction).all()]; ids={r['id'] for r in existing}; incoming=[r for r in entry[1] if r['id'] not in ids]
        if not incoming: raise HTTPException(422,'Nenhuma linha nova válida para importar.')
        allrows=hybrid(analyze(existing+incoming,get_rules()));newids={r['id'] for r in incoming}
        customer_ids={id for (id,) in s.query(Customer.id).all()}
        new_customers={r['customer_id'] for r in incoming}-customer_ids
        s.bulk_insert_mappings(Customer,[dict(id=id,data={'id':id}) for id in new_customers])
        persist_analysis(s,allrows,newids)
        s.commit()
    pending.pop(body.token,None)
    return {'message':f'{len(incoming)} transação importada.' if len(incoming)==1 else f'{len(incoming)} transações importadas.'}

def safe_cell(v):
    return "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v

@app.get('/api/reports/{format}')
def report(format:str,f:Filters=Depends()):
    if format not in ('csv','xlsx','pdf'): raise HTTPException(422,'Formato inválido.')
    with Session() as s:
        statuses=dict(s.query(Alert.id,Alert.status).all())
        rows=[dict(t.data,status=statuses.get(t.id,'Sem alerta')) for t in filtered(s,f).order_by(Transaction.timestamp).all()]
    columns=REQUIRED+['score','risk','status']
    frame=pd.DataFrame([{k:safe_cell(r.get(k,'')) for k in columns} for r in rows],columns=columns)
    if format=='csv': content=frame.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'); mime='text/csv'
    elif format=='xlsx':
        summary=dashboard(f,'dia')
        out=BytesIO()
        with pd.ExcelWriter(out,engine='openpyxl') as writer:
            frame.to_excel(writer,index=False,sheet_name='Transações')
            pd.DataFrame([{'quantidade':len(rows),'valor':summary['volume'],'sinalizadas':summary['flagged'],'percentual':summary['rate'],'exposição':summary['exposure'],'média':summary['mean'],'mediana':summary['median'],'percentil_95':summary['p95'],'quantidade_anterior':summary['previous']['total'],'valor_anterior':summary['previous']['volume']}]).to_excel(writer,index=False,sheet_name='Resumo')
            pd.DataFrame(summary['timeline']).to_excel(writer,index=False,sheet_name='Evolução')
            pd.DataFrame(summary['reasons']).to_excel(writer,index=False,sheet_name='Padrões de risco')
            pd.DataFrame(summary['categories']).to_excel(writer,index=False,sheet_name='Categorias')
            pd.DataFrame([{k:m[k] for k in ['name','precision','recall','f1','pr_auc','test_size']} for m in models()]).to_excel(writer,index=False,sheet_name='Modelos globais')
        content=out.getvalue();mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        out=BytesIO();c=canvas.Canvas(out);summary=dashboard(f,'dia')
        c.setTitle('FraudDetect — relatório sintético');y=800
        lines=['FraudDetect | Relatório demonstrativo','Dados 100% fictícios. Alto risco não comprova fraude.',f'Período: {f.start or "início"} a {f.end or "fim"} | Risco: {f.risk or "todos"}',f'Transações: {len(rows)} | Volume: R$ {summary["volume"]:,.2f}',f'Sinalizadas: {summary["flagged"]} ({summary["rate"]:.2f}%)',f'Exposição: R$ {summary["exposure"]:,.2f}',f'Período anterior: {summary["previous"]["total"]} transações',f'Média: {summary["mean"]:.2f} | Mediana: {summary["median"]:.2f} | P95: {summary["p95"]:.2f}','Principais motivos:']+[f'{r["name"]}: {r["value"]}' for r in summary['reasons']]+['Evolução diária:']+[f'{r["date"]}: {r["total"]} transações, {r["alerts"]} alertas' for r in summary['timeline']]+['Métricas dos modelos (teste sintético global):']+[f'{m["name"]}: precisão {m["precision"]:.3f}, recall {m["recall"]:.3f}, F1 {m["f1"]:.3f}' for m in models()]
        from reportlab.lib.utils import simpleSplit
        for line in lines:
            for wrapped in simpleSplit(line,'Helvetica',11,515):
                if y<55:
                    c.setFont('Helvetica',9);c.drawRightString(555,30,f'Página {c.getPageNumber()}');c.showPage();y=800
                c.setFillColor(HexColor('#142D4E'));c.setFont('Helvetica',11);c.drawString(40,y,wrapped);y-=21
        c.setFont('Helvetica',9);c.drawRightString(555,30,f'Página {c.getPageNumber()}')
        c.save();content=out.getvalue();mime='application/pdf'
    return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="frauddetect.{format}"'})


from .hosting import configure_hosting
configure_hosting(app)
