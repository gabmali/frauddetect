import os
from sqlalchemy import create_engine, Column, String, Float, Integer, JSON, ForeignKey, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base=declarative_base()
engine=create_engine(os.getenv('DATABASE_URL','sqlite:///./data/frauddetect.db'),connect_args={'check_same_thread':False})
Session=sessionmaker(bind=engine)

@event.listens_for(engine,'connect')
def foreign_keys(connection,record):
    connection.execute('PRAGMA foreign_keys=ON')

class Customer(Base):
    __tablename__='customers'
    id=Column(String,primary_key=True)
    data=Column(JSON,nullable=False)

class Transaction(Base):
    __tablename__='transactions'
    id=Column(String,primary_key=True)
    customer_id=Column(String,ForeignKey('customers.id'),index=True)
    timestamp=Column(String,index=True)
    amount=Column(Float)
    risk=Column(String,index=True)
    score=Column(Integer)
    data=Column(JSON,nullable=False)

class Alert(Base):
    __tablename__='alerts'
    id=Column(String,ForeignKey('transactions.id'),primary_key=True)
    status=Column(String,default='Pendente',index=True)
    note=Column(String,default='')

class History(Base):
    __tablename__='analysis_history'
    id=Column(Integer,primary_key=True)
    alert_id=Column(String,ForeignKey('alerts.id'),index=True)
    timestamp=Column(String)
    status=Column(String)
    note=Column(String)

class ModelResult(Base):
    __tablename__='model_results'
    id=Column(String,primary_key=True)
    data=Column(JSON)

class Setting(Base):
    __tablename__='settings'
    id=Column(String,primary_key=True)
    data=Column(JSON)

def initialize(count=20000):
    from .engine import generate,analyze,train,hybrid
    Base.metadata.create_all(engine)
    with Session() as s:
        if s.query(Transaction).first(): return
        customers,rows=generate(count); rows=analyze(rows)
        results=train(rows); rows=hybrid(rows)
        s.bulk_insert_mappings(Customer,[dict(id=c['id'],data=c) for c in customers])
        s.bulk_insert_mappings(Transaction,[transaction_mapping(r) for r in rows])
        s.bulk_insert_mappings(Alert,[dict(id=r['id'],status='Pendente',note='') for r in rows if r['score']>=30])
        for m in results: s.add(ModelResult(id=m['name'],data=m))
        s.commit()

def transaction_mapping(r):
    return dict(id=r['id'],customer_id=r['customer_id'],timestamp=r['timestamp'],amount=r['amount'],risk=r['risk'],score=r['score'],data=r)

def persist_analysis(s,rows,newids=None):
    newids=newids or set()
    s.bulk_update_mappings(Transaction,[transaction_mapping(r) for r in rows if r['id'] not in newids])
    s.bulk_insert_mappings(Transaction,[transaction_mapping(r) for r in rows if r['id'] in newids])
    existing_alerts={id for (id,) in s.query(Alert.id).all()}
    s.bulk_insert_mappings(Alert,[dict(id=r['id'],status='Pendente',note='') for r in rows if r['score']>=30 and r['id'] not in existing_alerts])
