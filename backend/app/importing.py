"""Validação limitada de arquivos locais, sem avaliação de fórmulas."""
from io import BytesIO, StringIO
from datetime import datetime
import csv
import re
import zipfile
import pandas as pd

REQUIRED=['id','customer_id','timestamp','amount','city','state','category','kind','channel']
STATES=set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())

def preview(content, filename):
    if len(content)>5*1024*1024: raise ValueError('Limite de 5 MB excedido.')
    if filename.lower().endswith('.csv'):
        try: text=content.decode('utf-8-sig')
        except UnicodeDecodeError: raise ValueError('Salve o CSV com codificação UTF-8.')
        if not text.strip(): raise ValueError('O arquivo está vazio.')
        header_line=text.splitlines()[0]
        delimiter=';' if header_line.count(';')>header_line.count(',') else ','
        headers=next(csv.reader(StringIO(text),delimiter=delimiter))
        frame=pd.read_csv(StringIO(text),sep=delimiter,dtype=str,keep_default_na=False,nrows=5001)
    elif filename.lower().endswith('.xlsx'):
        with zipfile.ZipFile(BytesIO(content)) as z:
            if sum(i.file_size for i in z.infolist())>30*1024*1024: raise ValueError('Planilha descompactada excede 30 MB.')
        from openpyxl import load_workbook
        wb=load_workbook(BytesIO(content),read_only=True,data_only=False)
        try:
            ws=wb.active
            if (ws.max_column or 0)>50: raise ValueError('Limite de 50 colunas excedido.')
            if (ws.max_row or 0)>5001: raise ValueError('Limite de 5.000 linhas excedido.')
            values=[]
            for row in ws.iter_rows(max_col=min(ws.max_column or 50,50)):
                if any(c.data_type=='f' for c in row): raise ValueError('Fórmulas não são aceitas.')
                values.append([c.value for c in row])
                if len(values)>5001: raise ValueError('Limite de 5.000 linhas excedido.')
            if not values: raise ValueError('O arquivo está vazio.')
            headers=values[0]
            frame=pd.DataFrame(values[1:],columns=headers).fillna('').astype(str)
        finally: wb.close()
    else: raise ValueError('Envie CSV ou XLSX.')
    headers=[str(h).strip() for h in headers]
    if len(headers)>50: raise ValueError('Limite de 50 colunas excedido.')
    if len(set(headers))!=len(headers): raise ValueError('O arquivo contém colunas duplicadas.')
    frame.columns=headers
    missing=set(REQUIRED)-set(frame.columns)
    if missing: raise ValueError('Colunas ausentes: '+', '.join(sorted(missing)))
    if len(frame)>5000: raise ValueError('Limite de 5.000 linhas excedido.')
    valid=[]; errors=[]; seen=set()
    for index,row in enumerate(frame[REQUIRED].to_dict('records'),2):
        try:
            row={k:str(v).strip() for k,v in row.items()}
            if any(not v for v in row.values()): raise ValueError('Campos obrigatórios vazios')
            if any(v.startswith(('=','+','-','@')) for v in row.values()): raise ValueError('Conteúdo de fórmula não aceito')
            if any(len(v)>150 for v in row.values()): raise ValueError('Campo acima de 150 caracteres')
            for key in ['id','customer_id']:
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',row[key]): raise ValueError(f'{key}: use até 100 letras, números, hífen ou sublinhado')
            row['amount']=float(row['amount'].replace(',','.'))
            if not 0<row['amount']<=1e9: raise ValueError('Valor fora dos limites')
            t=datetime.fromisoformat(row['timestamp'])
            if t.tzinfo is not None: raise ValueError('Use data local sem fuso horário')
            if not 2000<=t.year<=2100: raise ValueError('A data deve estar entre 2000 e 2100')
            row['timestamp']=t.isoformat(); row['state']=row['state'].upper()
            if row['state'] not in STATES: raise ValueError('UF brasileira inválida')
            if row['id'] in seen: raise ValueError('ID duplicado no arquivo')
            seen.add(row['id']); row['label']=None; valid.append(row)
        except (ValueError,TypeError) as e: errors.append(dict(line=index,error=str(e)))
    return dict(rows=valid,errors=errors,total=len(frame),valid=len(valid))
