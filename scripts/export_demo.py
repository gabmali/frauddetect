"""Gera somente dados fictícios e resultados reais do Python para o GitHub Pages."""
import json
import os
import tempfile
from pathlib import Path
from backend.app.engine import generate,analyze,train,hybrid,DEFAULT_RULES

def export(destination='frontend/public/demo.json'):
    prior=os.environ.get('MODEL_PATH')
    try:
        with tempfile.TemporaryDirectory() as folder:
            os.environ['MODEL_PATH']=str(Path(folder)/'model.joblib')
            _,rows=generate(20000,42)
            rows=analyze(rows)
            models=train(rows)
            rows=hybrid(rows)
            cutoff=rows[int(len(rows)*.8)]['timestamp']
            result={'schema':1,'seed':42,'cutoff':cutoff,'rules':DEFAULT_RULES,'models':models,'transactions':rows}
            target=Path(destination);target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
            print(f'Demonstração exportada: {len(rows)} transações fictícias, {target.stat().st_size} bytes.')
    finally:
        if prior is None:os.environ.pop('MODEL_PATH',None)
        else:os.environ['MODEL_PATH']=prior

if __name__=='__main__':export()
