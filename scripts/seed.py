"""Execute da raiz: python -m scripts.seed [--count 20000]."""
import argparse
from pathlib import Path
import pandas as pd
from backend.app.database import initialize
from backend.app.engine import generate

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--count',type=int,default=20000);args=parser.parse_args()
    if args.count<1000: parser.error('Use pelo menos 1.000 linhas para treinar os modelos.')
    Path('data/synthetic').mkdir(parents=True,exist_ok=True)
    customers,rows=generate(args.count);pd.DataFrame(rows).to_csv('data/synthetic/transactions.csv',index=False)
    initialize(args.count);print(f'Base inicializada; CSV com {len(rows)} transações sintéticas gerado.')
