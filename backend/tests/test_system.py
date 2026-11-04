import os
import tempfile
from pathlib import Path
from io import BytesIO
import pytest

TEMP=tempfile.TemporaryDirectory()
os.environ['DATABASE_URL']='sqlite:///'+str(Path(TEMP.name)/'test.db')
os.environ['MODEL_PATH']=str(Path(TEMP.name)/'model.joblib')
from backend.app.engine import generate,analyze,score_features,DEFAULT_RULES,train
from backend.app.importing import preview,REQUIRED
from backend.app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope='module')
def client():
    from backend.app.database import engine
    with TestClient(app) as c: yield c
    engine.dispose()

def test_reproducible_generation():
    a=generate(100,42);b=generate(100,42)
    assert a==b and len(a[0])==500 and len(a[1])==100
    assert all(0<r['amount'] for r in a[1])

def test_scores_and_risk():
    f=dict(amount_ratio=8,velocity=6,unusual_hour=1,geo_change=1,repeated=5)
    assert score_features(f,DEFAULT_RULES)[:2]==(100,'alto')
    f=dict(amount_ratio=1,velocity=1,unusual_hour=0,geo_change=0,repeated=1)
    assert score_features(f,DEFAULT_RULES)==(0,'baixo',[])
    f['amount_ratio']=5
    assert score_features(f,DEFAULT_RULES)[:2]==(35,'médio')

def test_causal_history():
    _,rows=generate(1000)
    first=analyze(rows[:500]);full=analyze(rows)
    assert first==full[:500]

def test_temporal_models():
    _,rows=generate(1500);results=train(analyze(rows))
    assert len(results)==2
    for r in results:
        assert r['train_size']==1200 and r['test_size']==300
        assert 0<=r['f1']<=1 and 0<=r['pr_auc']<=1
        assert sum(map(sum,r['matrix']))==300

def test_hybrid_out_of_sample():
    from backend.app.engine import hybrid
    _,rows=generate(1000);rows=analyze(rows);train(rows)
    scored=hybrid(rows)
    assert all('model_score' not in r for r in scored[:800])
    assert all(0<=r['model_score']<=100 and r['score']>=r['rule_score'] for r in scored[800:])

def csv_row(id='IMP-TEST',amount='123.45'):
    return (','.join(REQUIRED)+'\n'+f'{id},CLI-TEST,2026-11-01T12:00:00,{amount},Recife,PE,Compras,Pix,Aplicativo\n').encode()

def test_import_validation():
    assert preview(csv_row(),'base.csv')['valid']==1
    assert preview(csv_row(amount='abc'),'base.csv')['valid']==0
    assert preview(csv_row(id='=DANGER'),'base.csv')['valid']==0
    with pytest.raises(ValueError):preview(b'id\n1','base.csv')
    with pytest.raises(ValueError):preview(b'abc','base.exe')
    with pytest.raises(ValueError):preview(b'0'*(5*1024*1024+1),'base.csv')

def test_excel_formula_rejected():
    from openpyxl import Workbook
    w=Workbook();w.active.append(REQUIRED);w.active.append(['=1+1']*len(REQUIRED));b=BytesIO();w.save(b)
    with pytest.raises(ValueError):preview(b.getvalue(),'base.xlsx')

def test_dashboard_and_pagination(client):
    d=client.get('/api/dashboard').json()
    assert d['total']==20000 and sum(x['value'] for x in d['risks'])==20000
    assert d['flagged']<=d['total']
    a=client.get('/api/transactions?size=10&page=1').json();b=client.get('/api/transactions?size=10&page=2').json()
    assert len(a['items'])==10 and a['items'][0]['id']!=b['items'][0]['id']
    filtered=client.get('/api/dashboard?risk=alto').json()
    assert filtered['total']==filtered['flagged']
    assert client.get('/api/transactions?size=101').status_code==422
    assert client.get('/api/dashboard?start=no').status_code==422
    assert client.get('/api/transactions/missing').status_code==404

def test_alert_persistence(client):
    id=client.get('/api/alerts').json()['items'][0]['id']
    assert client.patch('/api/alerts/'+id,json={'status':'Em análise','note':'Revisão de teste','revision':0}).status_code==200
    detail=client.get('/api/transactions/'+id).json()
    assert detail['status']=='Em análise' and detail['note']=='Revisão de teste'
    assert detail['history'][-1]['note']=='Revisão de teste'
    assert client.patch('/api/alerts/'+id,json={'status':'Inválido'}).status_code==422

def test_confirmed_import(client):
    p=client.post('/api/import/preview',files={'file':('test.csv',csv_row(),'text/csv')}).json()
    assert p['valid']==1
    assert client.get('/api/transactions/IMP-TEST').status_code==404
    assert client.post('/api/import/confirm',json={'token':p['token'],'confirmed':False}).status_code==422
    assert client.post('/api/import/confirm',json={'token':p['token'],'confirmed':True}).status_code==200
    assert client.get('/api/transactions/IMP-TEST').status_code==200
    assert client.post('/api/import/confirm',json={'token':p['token'],'confirmed':True}).status_code==422
    p=client.post('/api/import/preview',files={'file':('test.csv',csv_row(),'text/csv')}).json()
    assert p['duplicates']==1 and p['valid']==0

def test_exports(client):
    for fmt,prefix in [('csv',b'\xef\xbb\xbf'),('xlsx',b'PK'),('pdf',b'%PDF')]:
        response=client.get('/api/reports/'+fmt+'?risk=alto')
        assert response.status_code==200 and response.content.startswith(prefix)

def test_rules_recompute(client):
    rules=client.get('/api/rules').json(); rules['value_multiple']=5
    assert client.put('/api/rules',json=rules).status_code==200
    assert client.get('/api/rules').json()['value_multiple']==5

@pytest.mark.parametrize('field',['amount','score','timestamp','id'])
def test_alert_sorting(client,field):
    for direction in ['asc','desc']:
        response=client.get(f'/api/alerts?sort={field}&direction={direction}&size=100')
        assert response.status_code==200
        values=[r[field] for r in response.json()['items']]
        assert values==sorted(values,reverse=direction=='desc')

def test_empty_period_preserves_previous_comparison(client):
    result=client.get('/api/dashboard?start=2026-11-02&end=2026-12-03').json()
    assert result['total']==0
    assert result['previous']['total']>0

def test_full_day_previous_comparison(client):
    current=client.get('/api/dashboard?start=2026-10-02&end=2026-10-02').json()
    previous=client.get('/api/dashboard?start=2026-10-01&end=2026-10-01').json()
    assert current['previous']['total']==previous['total']
    assert current['previous']['volume']==pytest.approx(previous['volume'])

def test_brazilian_csv_and_whitespace():
    content=(' ; '.join(REQUIRED)+'\n IMP-BR ; CLI-BR ; 2026-10-01T12:00:00 ; 150,50 ; Recife ; pe ; Compras ; Pix ; Aplicativo\n').encode()
    result=preview(content,'br.csv')
    assert result['valid']==1
    assert result['rows'][0]['amount']==150.5
    assert result['rows'][0]['state']=='PE'

@pytest.mark.parametrize('original,replacement',[('IMP-TEST','bad/id'),('2026-11-01','9999-11-01'),('Recife,PE','Recife,ZZ'),('123.45','NaN'),('123.45','inf')])
def test_unsafe_import_fields(original,replacement):
    result=preview(csv_row().replace(original.encode(),replacement.encode()),'bad.csv')
    assert result['valid']==0 and len(result['errors'])==1

def test_duplicate_headers_and_empty_files():
    with pytest.raises(ValueError,match='duplicadas'):
        preview((','.join(REQUIRED+['id'])+'\n').encode(),'bad.csv')
    with pytest.raises(ValueError,match='vazio'):preview(b'','empty.csv')

def test_wide_excel_rejected():
    from openpyxl import Workbook
    w=Workbook();w.active.append([f'column{i}' for i in range(51)]);b=BytesIO();w.save(b)
    with pytest.raises(ValueError,match='colunas'):preview(b.getvalue(),'wide.xlsx')

def test_stale_alert_edit_is_rejected(client):
    item=client.get('/api/alerts').json()['items'][0]
    url='/api/alerts/'+item['id']; revision=item['revision']
    first=client.patch(url,json={'status':'Resolvido','note':'Primeira análise','revision':revision})
    assert first.status_code==200
    second=client.patch(url,json={'status':'Falso positivo','note':'Texto desatualizado','revision':revision})
    assert second.status_code==409
    latest=client.get('/api/transactions/'+item['id']).json()
    assert latest['note']=='Primeira análise' and latest['status']=='Resolvido'
    assert latest['revision']>revision

def test_simultaneous_edits_have_one_winner(client):
    from concurrent.futures import ThreadPoolExecutor
    item=client.get('/api/alerts').json()['items'][1]
    before=client.get('/api/transactions/'+item['id']).json()
    def edit(note):
        return client.patch('/api/alerts/'+item['id'],json={'status':'Em análise','note':note,'revision':before['revision']}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(edit,['Aba A','Aba B']))
    assert sorted(results)==[200,409]
    after=client.get('/api/transactions/'+item['id']).json()
    assert len(after['history'])==len(before['history'])+1

@pytest.mark.parametrize('corrupt',[False,True])
def test_model_failure_is_visible_and_blocks_scoring(client,tmp_path,monkeypatch,corrupt):
    path=tmp_path/'missing.joblib'
    if corrupt:path.write_bytes(b'modelo corrompido')
    monkeypatch.setenv('MODEL_PATH',str(path))
    assert client.get('/api/detector/status').json()['available'] is False
    assert client.get('/api/health').json()['status']=='degraded'
    before=client.get('/api/transactions?size=1').json()['total']
    response=client.put('/api/rules',json=DEFAULT_RULES)
    assert response.status_code==503 and 'modelo' in response.json()['detail']
    p=client.post('/api/import/preview',files={'file':('test.csv',csv_row('MODEL-GUARD'),'text/csv')}).json()
    response=client.post('/api/import/confirm',json={'token':p['token'],'confirmed':True})
    assert response.status_code==503
    assert client.get('/api/transactions?size=1').json()['total']==before

def test_report_contents_match_filtered_dashboard(client):
    import pandas as pd
    from io import StringIO
    from pypdf import PdfReader
    query='?risk=alto&start=2026-10-01&end=2026-10-07'
    d=client.get('/api/dashboard'+query).json()
    assert d['total']>0
    csv=client.get('/api/reports/csv'+query)
    frame=pd.read_csv(StringIO(csv.content.decode('utf-8-sig')),sep=';',decimal=',')
    assert len(frame)==d['total'] and set(frame.risk)=={'alto'}
    assert frame.amount.sum()==pytest.approx(d['volume'])
    assert frame.timestamp.min()>='2026-10-01' and frame.timestamp.max()<'2026-10-08'
    xlsx=client.get('/api/reports/xlsx'+query)
    sheets=pd.read_excel(BytesIO(xlsx.content),sheet_name=None)
    summary=sheets['Resumo'].iloc[0]
    assert len(sheets['Transações'])==d['total']==summary['quantidade']
    assert summary['valor']==pytest.approx(d['volume'])
    assert summary['exposição']==pytest.approx(d['exposure'])
    assert sheets['Evolução'].total.sum()==d['total']
    assert sheets['Padrões de risco'].value.sum()==sum(r['value'] for r in d['reasons'])
    pdf=client.get('/api/reports/pdf'+query)
    pages=PdfReader(BytesIO(pdf.content)).pages
    text='\n'.join(p.extract_text() for p in pages)
    assert f'Transações: {d["total"]}' in text
    assert f'{d["volume"]:,.2f}' in text
    assert '2026-10-01 a 2026-10-07' in text
    assert all(f'Página {i+1}' in p.extract_text() for i,p in enumerate(pages))

def test_empty_report_has_zero_summary(client):
    import pandas as pd
    query='?start=2090-01-01&end=2090-01-02'
    workbook=pd.read_excel(BytesIO(client.get('/api/reports/xlsx'+query).content),sheet_name=None)
    assert len(workbook['Transações'])==0
    assert workbook['Resumo'].iloc[0]['quantidade']==0

def test_public_demo_blocks_writes_but_allows_queries(client,monkeypatch):
    monkeypatch.setenv('PUBLIC_DEMO','1')
    assert client.get('/api/dashboard').status_code==200
    assert client.get('/api/reports/csv?risk=alto').status_code==200
    assert client.patch('/api/alerts/any',json={'status':'Resolvido','revision':0}).status_code==403
    assert client.put('/api/rules',json=DEFAULT_RULES).status_code==403
    assert client.post('/api/import/preview',files={'file':('test.csv',csv_row(),'text/csv')}).status_code==403

def test_static_host_serves_only_build(tmp_path):
    from fastapi import FastAPI
    from backend.app.hosting import configure_hosting
    from unittest.mock import patch
    (tmp_path/'index.html').write_text('<html lang="pt-BR">FraudDetect</html>',encoding='utf-8')
    with patch.dict(os.environ,{'STATIC_DIR':str(tmp_path)}):
        hosted=FastAPI();configure_hosting(hosted)
    with TestClient(hosted) as c:
        assert 'FraudDetect' in c.get('/').text
        assert c.get('/backend/app/main.py').status_code==404
        assert c.get('/data/frauddetect.db').status_code==404
