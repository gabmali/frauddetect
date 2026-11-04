"""Mede geração, regras e agregação, sem escrever na base da aplicação."""
import gc
import json
import platform
import time
from pathlib import Path
from backend.app.engine import generate,analyze
from backend.app.main import aggregate

def run():
    result={'python':platform.python_version(),'platform':platform.platform(),'scope':'Geração, regras causais e agregação em memória; sem treino ou gravação SQL','measurements':[]}
    for count in [20000,100000]:
        t=time.perf_counter();_,rows=generate(count);generated=time.perf_counter()
        rows=analyze(rows);analyzed=time.perf_counter();summary=aggregate(rows,'dia');ended=time.perf_counter()
        assert summary['total']==count
        result['measurements'].append({'rows':count,'generate_seconds':round(generated-t,3),'rules_seconds':round(analyzed-generated,3),'aggregate_seconds':round(ended-analyzed,3),'flagged':summary['flagged']})
        del rows,summary;gc.collect()
    Path('docs/benchmark.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
