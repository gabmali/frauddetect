"""Dados sintéticos e regras causais: cada evento usa apenas o passado do cliente."""
from datetime import datetime, timedelta
from collections import defaultdict, deque
import os
import numpy as np
import pandas as pd
from faker import Faker

DEFAULT_RULES = dict(value_multiple=4.0, velocity_count=4, velocity_minutes=10, geo_minutes=60, repeat_count=3)
FEATURES = ['amount_ratio', 'velocity', 'unusual_hour', 'geo_change', 'repeated']

def generate(count=20000, seed=42):
    rng = np.random.default_rng(seed)
    fake = Faker('pt_BR'); fake.seed_instance(seed)
    cities = [('São Paulo','SP'),('Recife','PE'),('Curitiba','PR'),('Manaus','AM'),('Salvador','BA')]
    customers = [dict(id=f'CLI-{i:04}', name=f'Cliente sintético {i:04}', city=cities[i%5][0], state=cities[i%5][1], baseline=float(rng.uniform(100,900))) for i in range(500)]
    rows=[]
    start=datetime(2026,8,1)
    for i in range(count):
        c=customers[int(rng.integers(500))]; suspicious=bool(rng.random()<0.065)
        city,state=cities[int(rng.integers(5))] if suspicious else (c['city'],c['state'])
        amount=round(c['baseline']*float(rng.lognormal(0,0.6))*(6 if suspicious and rng.random()<0.65 else 1),2)
        date=start+timedelta(seconds=int(rng.integers(92*86400)))
        if suspicious: date=date.replace(hour=int(rng.integers(0,5)))
        # Pequenas sequências rotuladas exercitam frequência e repetição.
        if 1<=i%200<=5:
            anchor=rows[-1]
            c=customers[int(anchor['customer_id'].split('-')[1])]
            date=datetime.fromisoformat(anchor['timestamp'])+timedelta(seconds=30)
            amount=anchor['amount'];city,state=cities[(i%5)]
            suspicious=True
        rows.append(dict(id=f'TX-{seed}-{i:07}', customer_id=c['id'], timestamp=date.isoformat(), amount=amount, city=city,state=state, category=fake.random_element(['Compras','Serviços','Transferências','Alimentação','Viagens']),kind=fake.random_element(['Pix','Cartão','TED','Boleto']),channel=fake.random_element(['Aplicativo','Internet banking','Terminal']),label=int(suspicious)))
    return customers, sorted(rows,key=lambda r:(r['timestamp'],r['id']))

def score_features(f, rules):
    checks=[(f['amount_ratio']>rules['value_multiple'],35,'Valor acima do histórico'),(f['velocity']>=rules['velocity_count'],25,'Muitas operações em curto intervalo'),(f['unusual_hour'],10,'Horário incomum'),(f['geo_change'],25,'Mudança geográfica incompatível'),(f['repeated']>=rules['repeat_count'],20,'Repetição de operações')]
    score=min(100,sum(w for hit,w,_ in checks if hit))
    return score, 'alto' if score>=60 else 'médio' if score>=30 else 'baixo', [reason for hit,_,reason in checks if hit]

def analyze(rows, rules=None):
    rules=rules or DEFAULT_RULES
    history=defaultdict(lambda: dict(total=0.,count=0,last=None,recent=deque()))
    output=[]
    for row in sorted(rows,key=lambda r:(r['timestamp'],r['id'])):
        r=dict(row); h=history[r['customer_id']]; t=datetime.fromisoformat(r['timestamp'])
        while h['recent'] and (t-h['recent'][0][0]).total_seconds()>rules['velocity_minutes']*60: h['recent'].popleft()
        f=dict(amount_ratio=r['amount']/(h['total']/h['count'] if h['count'] else max(r['amount'],1)),velocity=len(h['recent'])+1,unusual_hour=int(t.hour<6),geo_change=int(bool(h['last'] and h['last'][1]!=r['city'] and (t-h['last'][0]).total_seconds()<rules['geo_minutes']*60)),repeated=1+sum(amount==r['amount'] for _,amount in h['recent']))
        score,risk,reasons=score_features(f,rules)
        r.update(f); r.update(score=score,risk=risk,reasons=reasons,recommendation='Revisar contexto e evidências' if score>=30 else 'Monitoramento habitual')
        output.append(r); h['total']+=r['amount']; h['count']+=1; h['last']=(t,r['city']); h['recent'].append((t,r['amount']))
    return output

def train(rows):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, confusion_matrix
    frame=pd.DataFrame(rows).sort_values('timestamp'); split=int(len(frame)*.8)
    X=frame[FEATURES]; y=frame.label
    models={'Random Forest':RandomForestClassifier(n_estimators=100,max_depth=8,random_state=42,class_weight='balanced',n_jobs=2),'Regressão logística':make_pipeline(StandardScaler(),LogisticRegression(max_iter=500,class_weight='balanced',random_state=42))}
    results=[]
    for name,model in models.items():
        model.fit(X.iloc[:split],y.iloc[:split]); pred=model.predict(X.iloc[split:]); scores=model.predict_proba(X.iloc[split:])[:,1]
        importance=model.feature_importances_ if hasattr(model,'feature_importances_') else abs(model[-1].coef_[0])
        results.append(dict(name=name,precision=precision_score(y.iloc[split:],pred,zero_division=0),recall=recall_score(y.iloc[split:],pred,zero_division=0),f1=f1_score(y.iloc[split:],pred,zero_division=0),pr_auc=average_precision_score(y.iloc[split:],scores),matrix=confusion_matrix(y.iloc[split:],pred,labels=[0,1]).tolist(),importance=dict(zip(FEATURES,map(float,importance))),train_size=split,test_size=len(frame)-split))
    import joblib
    from pathlib import Path
    Path('data').mkdir(exist_ok=True)
    joblib.dump({'model':models['Random Forest'],'cutoff':str(frame.iloc[split]['timestamp'])},os.getenv('MODEL_PATH','data/model.joblib'))
    return results

class ModelUnavailableError(RuntimeError):
    pass

def model_artifact():
    import joblib
    from pathlib import Path
    path=Path(os.getenv('MODEL_PATH','data/model.joblib'))
    try:
        artifact=joblib.load(path)
        if not hasattr(artifact['model'],'predict_proba'): raise ValueError()
        datetime.fromisoformat(artifact['cutoff'])
        return artifact
    except Exception as error:
        raise ModelUnavailableError('O modelo de Machine Learning está ausente ou inválido. A reavaliação e a importação estão bloqueadas. Restaure o modelo local correspondente à base.') from error

def detector_status():
    try:
        artifact=model_artifact()
        return dict(available=True,message='Detector híbrido disponível',cutoff=artifact['cutoff'])
    except ModelUnavailableError as error:
        return dict(available=False,message=str(error))

def hybrid(rows):
    """O modelo só pontua operações posteriores ao fim de seu treino."""
    artifact=model_artifact()
    eligible=[r for r in rows if r['timestamp']>=artifact['cutoff']]
    if not eligible: return rows
    scores=artifact['model'].predict_proba(pd.DataFrame(eligible)[FEATURES])[:,1]*100
    for r,model_score in zip(eligible,scores):
        r['model_score']=float(model_score);r['rule_score']=r['score']
        contribution=int(model_score*.2)
        r['score']=min(100,r['score']+contribution)
        r['risk']='alto' if r['score']>=60 else 'médio' if r['score']>=30 else 'baixo'
        if contribution>=10:r['reasons'].append('Indicador preditivo elevado (modelo sintético)')
        r['recommendation']='Revisar contexto e evidências' if r['score']>=30 else 'Monitoramento habitual'
    return rows
