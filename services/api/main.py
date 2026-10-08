import os, json, shutil, logging, time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as Upload, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func, case
from services.api.db import Session, DATA, init_db, Workspace, File, Segment, Job, Message, Report, Audit, uid
from services.api.security import user, authorize, rate_limit
from services.worker.processors import validate
from services.worker.ai import available, provider_error
from services.api.intelligence import answer, citation, timeline, graph
from services.api.reports import make_report
from services.api import storage

@asynccontextmanager
async def lifespan(app):
    init_db(); yield
app=FastAPI(title='EVIDENCE.AI',version='1.0.0',lifespan=lifespan,dependencies=[Depends(rate_limit)])
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://127.0.0.1:3000']+os.getenv('WEB_ORIGINS','').split(','),allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])

@app.middleware('http')
async def request_timing(request,call_next):
    request_id=uid(); start=time.monotonic()
    response=await call_next(request)
    response.headers['X-Request-ID']=request_id
    logging.getLogger('uvicorn.error').info('request=%s method=%s path=%s status=%s elapsed=%.2fs',request_id,request.method,request.url.path,response.status_code,time.monotonic()-start)
    return response
def database():
    with Session() as db: yield db
def serialize(obj): return {c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name not in ('path','owner_id','synthetic')}
def log(db,u,w,action): db.add(Audit(user_id=u,workspace_id=w,action=action)); db.commit()
class CreateWorkspace(BaseModel):
    name: str=Field(min_length=2,max_length=160)
    description: str=Field(default='',max_length=3000)
    industry: Literal['Manufacturing','Education','Insurance','E-commerce']
class Question(BaseModel): question: str=Field(min_length=2,max_length=4000)
@app.get('/api/health')
def health(): return {'status':'ok','gemini':available(),'auth':bool(os.getenv('SUPABASE_URL')),'storage':'private local storage','retrieval':'hybrid semantic + keyword' if available() else 'keyword retrieval'}
@app.get('/api/workspaces')
def workspaces(u=Depends(user),db=Depends(database)):
    rows=list(db.scalars(select(Workspace).where(Workspace.owner_id==u).order_by(Workspace.created_at.desc())))
    counts={r[0]:r[1:] for r in db.execute(select(File.workspace_id,func.count(File.id),func.sum(case((File.status=='Ready',1),else_=0)),func.sum(case((File.status.in_(['Queued','Processing','Indexed']),1),else_=0))).join(Workspace,Workspace.id==File.workspace_id).where(Workspace.owner_id==u).group_by(File.workspace_id))}
    return [{**serialize(w),'file_count':counts.get(w.id,(0,0,0))[0],'ready_count':counts.get(w.id,(0,0,0))[1],'processing_count':counts.get(w.id,(0,0,0))[2]} for w in rows]
@app.post('/api/workspaces',status_code=201)
def create(body:CreateWorkspace,u=Depends(user),db=Depends(database)):
    w=Workspace(owner_id=u,**body.model_dump()); db.add(w); db.commit(); log(db,u,w.id,'workspace.created'); return serialize(w)
@app.get('/api/workspaces/{wid}')
def workspace(wid:str,u=Depends(user),db=Depends(database)):
    w=authorize(db,wid,u); data=serialize(w)
    files=list(db.scalars(select(File).where(File.workspace_id==wid).order_by(File.created_at.desc())))
    data['files']=[serialize(f) for f in files]
    by_id={f.id:f for f in files}
    data['segments']=[citation(db,s,by_id) for s in db.scalars(select(Segment).where(Segment.workspace_id==wid).limit(500))]
    return data
@app.patch('/api/workspaces/{wid}')
def update_workspace(wid:str,body:CreateWorkspace,u=Depends(user),db=Depends(database)):
    w=authorize(db,wid,u)
    for k,v in body.model_dump().items(): setattr(w,k,v)
    db.commit(); return serialize(w)
def remove_file(db,f):
    if f.meta.get('storage_key'): storage.remove(f.meta['storage_key'])
    db.execute(delete(Job).where(Job.file_id==f.id)); db.execute(delete(Segment).where(Segment.file_id==f.id)); Path(f.path).unlink(missing_ok=True); db.delete(f)
@app.delete('/api/workspaces/{wid}')
def delete_workspace(wid:str,u=Depends(user),db=Depends(database)):
    w=authorize(db,wid,u)
    if db.scalar(select(File).where(File.workspace_id==wid,File.status=='Processing')): raise HTTPException(409,'Wait for processing to finish before deleting.')
    for f in db.scalars(select(File).where(File.workspace_id==wid)): remove_file(db,f)
    for r in db.scalars(select(Report).where(Report.workspace_id==wid)): Path(r.path).unlink(missing_ok=True); db.delete(r)
    db.execute(delete(Message).where(Message.workspace_id==wid)); db.flush(); db.delete(w); db.commit(); return {'deleted':True}
@app.post('/api/workspaces/{wid}/files',status_code=201)
async def upload(wid:str,files:list[UploadFile]=Upload(...),u=Depends(user),db=Depends(database)):
    authorize(db,wid,u)
    if len(files)>20: raise HTTPException(400,'Upload at most 20 files at a time.')
    prepared=[]; limit=int(os.getenv('MAX_FILE_MB','25'))*1024*1024
    for f in files:
        data=await f.read(limit+1)
        try: mime=validate(data,f.filename or '')
        except ValueError as e: raise HTTPException(400,str(e))
        prepared.append((f,data,mime))
    out=[]; directory=DATA/'uploads'/wid; directory.mkdir(parents=True,exist_ok=True)
    for f,data,mime in prepared:
        fid=uid(); name=Path((f.filename or '').replace('\\','/')).name[:255]; path=directory/(fid+Path(name).suffix.lower())
        storage_key=f'{u}/{wid}/{fid}{Path(name).suffix.lower()}'
        try: storage.store(storage_key,data,mime)
        except ValueError as e: raise HTTPException(503,str(e))
        path.write_bytes(data)
        item=File(id=fid,workspace_id=wid,name=name,mime=mime,size=len(data),path=str(path),status='Queued',meta={'storage_key':storage_key} if storage.enabled() else {}); db.add(item); db.flush(); db.add(Job(file_id=fid)); out.append(serialize(item))
    db.commit(); log(db,u,wid,'files.uploaded'); return out
@app.get('/api/workspaces/{wid}/files')
def list_files(wid:str,offset:int=0,limit:int=50,u=Depends(user),db=Depends(database)):
    authorize(db,wid,u); return [serialize(f) for f in db.scalars(select(File).where(File.workspace_id==wid).offset(max(offset,0)).limit(min(max(limit,1),100)))]
def get_file(db,fid,u):
    f=db.get(File,fid)
    if not f: raise HTTPException(404,'File not found.')
    authorize(db,f.workspace_id,u); return f
@app.get('/api/files/{fid}')
def detail(fid:str,u=Depends(user),db=Depends(database)): return serialize(get_file(db,fid,u))
@app.get('/api/files/{fid}/content')
def content(fid:str,u=Depends(user),db=Depends(database)):
    f=get_file(db,fid,u)
    if f.meta.get('storage_key'):return RedirectResponse(storage.signed(f.meta['storage_key']))
    return FileResponse(f.path,media_type=f.mime,filename=f.name,content_disposition_type='inline',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store'})
@app.post('/api/files/{fid}/retry')
def retry(fid:str,u=Depends(user),db=Depends(database)):
    f=get_file(db,fid,u)
    if f.status not in ('Failed','Partially Processed'): raise HTTPException(409,'Only failed or partially processed files can be retried.')
    f.status='Queued'; f.error=None; db.add(Job(file_id=fid)); db.commit(); return serialize(f)
@app.delete('/api/files/{fid}')
def delete_file(fid:str,u=Depends(user),db=Depends(database)):
    f=get_file(db,fid,u)
    if f.status=='Processing': raise HTTPException(409,'Wait for processing to finish before deleting.')
    remove_file(db,f); db.commit(); return {'deleted':True}
@app.post('/api/workspaces/{wid}/ask')
def ask(wid:str,body:Question,u=Depends(user),db=Depends(database)):
    authorize(db,wid,u)
    try: result=answer(db,wid,body.question)
    except ValueError as e: raise HTTPException(502,str(e))
    except Exception as e:
        logging.getLogger(__name__).error('Answer failed (%s, code=%s)',type(e).__name__,getattr(e,'code',None))
        raise HTTPException(502,provider_error(e))
    db.add(Message(workspace_id=wid,role='user',content=body.question))
    msg=Message(workspace_id=wid,role='assistant',**result); db.add(msg); db.commit(); log(db,u,wid,'question.answered'); return serialize(msg)
@app.get('/api/workspaces/{wid}/messages')
def messages(wid:str,u=Depends(user),db=Depends(database)):
    authorize(db,wid,u); return [serialize(m) for m in db.scalars(select(Message).where(Message.workspace_id==wid).order_by(Message.created_at))]
@app.get('/api/workspaces/{wid}/timeline')
def get_timeline(wid:str,u=Depends(user),db=Depends(database)): authorize(db,wid,u); return timeline(db,wid)
@app.get('/api/workspaces/{wid}/graph')
def get_graph(wid:str,u=Depends(user),db=Depends(database)): authorize(db,wid,u); return graph(db,wid)
@app.get('/api/workspaces/{wid}/reports')
def reports(wid:str,u=Depends(user),db=Depends(database)):
    authorize(db,wid,u); return [serialize(r) for r in db.scalars(select(Report).where(Report.workspace_id==wid).order_by(Report.created_at.desc()))]
@app.post('/api/workspaces/{wid}/reports',status_code=201)
def report(wid:str,u=Depends(user),db=Depends(database)):
    w=authorize(db,wid,u); r=make_report(db,w); log(db,u,wid,'report.created'); return serialize(r)
@app.get('/api/reports/{rid}/download')
def download(rid:str,u=Depends(user),db=Depends(database)):
    r=db.get(Report,rid)
    if not r: raise HTTPException(404,'Report not found.')
    authorize(db,r.workspace_id,u); return FileResponse(r.path,media_type='application/pdf',filename='EvidenceAI-report.pdf')
@app.post('/api/workspaces/{wid}/study')
def study(wid:str,u=Depends(user),db=Depends(database)):
    from services.api.study import make_study
    authorize(db,wid,u)
    try: return make_study(db,wid)
    except ValueError as e: raise HTTPException(400,str(e))
    except Exception as e: raise HTTPException(502,provider_error(e))

