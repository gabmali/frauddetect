from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.hosting import configure_hosting
import pytest

@pytest.fixture
def restricted(monkeypatch,tmp_path):
    monkeypatch.setenv('REQUIRE_DEMO_AUTH','1')
    monkeypatch.setenv('DEMO_ACCESS_PASSWORD','senha-ficticia-de-teste-2026')
    monkeypatch.setenv('STATIC_DIR',str(tmp_path))
    (tmp_path/'index.html').write_text('FraudDetect',encoding='utf-8')
    app=FastAPI()
    @app.get('/api/test')
    def data():return {'synthetic':True}
    configure_hosting(app)
    with TestClient(app) as client:yield client

@pytest.mark.parametrize('path',['/','/api/test','/docs'])
def test_recruiter_pages_require_auth(restricted,path):
    assert restricted.get(path).status_code==401
    assert restricted.get(path,auth=('recrutador','incorreta')).status_code==401
    assert restricted.get(path,auth=('recrutador','senha-ficticia-de-teste-2026')).status_code==200

def test_missing_secret_never_opens_site(restricted,monkeypatch):
    monkeypatch.delenv('DEMO_ACCESS_PASSWORD')
    assert restricted.get('/').status_code==503
    assert restricted.get('/healthz').json()=={'status':'ok'}

def test_auth_and_indexing_headers(restricted):
    response=restricted.get('/',auth=('recrutador','senha-ficticia-de-teste-2026'))
    assert response.headers['cache-control']=='private, no-store'
    assert 'noindex' in response.headers['x-robots-tag']
    assert 'Disallow: /' in restricted.get('/robots.txt').text
    assert restricted.get('/api/test',headers={'Authorization':'Basic !!!'}).status_code==401
