from pathlib import Path
from sqlalchemy import select
from services.api.db import Workspace,File,Job,DATA,uid
from services.worker.processors import validate
from demo.generate import generate,ROOT

def create_demo(db,user_id):
    generate();out=[]
    cases=[('delivery','Damaged laptop delivery','E-commerce','Order ORD-1042. Connect the invoice, delivery log, and customer statement. All evidence is fictional.'),('manufacturing','Machine A — Failure investigation','Manufacturing','Conveyor CV-204. Compare sensor trends, maintenance history, and technician observations. All evidence is fictional.')]
    for folder,name,industry,description in cases:
        w=db.scalar(select(Workspace).where(Workspace.owner_id==user_id,Workspace.name==name,Workspace.synthetic==True))
        if not w:
            w=Workspace(owner_id=user_id,name=name,industry=industry,description=description,synthetic=True);db.add(w);db.flush()
            directory=DATA/'uploads'/w.id;directory.mkdir(parents=True,exist_ok=True)
            for path in (ROOT/folder).iterdir():
                if path.suffix.lower() not in ('.pdf','.txt','.csv'):continue
                data=path.read_bytes();mime=validate(data,path.name);fid=uid();target=directory/(fid+path.suffix);target.write_bytes(data)
                f=File(id=fid,workspace_id=w.id,name=path.name,mime=mime,size=len(data),path=str(target),status='Queued');db.add(f);db.flush();db.add(Job(file_id=fid))
        out.append({c.name:getattr(w,c.name) for c in w.__table__.columns if c.name!='owner_id'})
    db.commit();return out
