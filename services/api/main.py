import os, logging, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from services.api.db import init_db, uid
from services.api.security import rate_limit
from services.api.pulse import router
from services.worker.ai import available

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app=FastAPI(title='ClientPulse AI',version='2.0.0',lifespan=lifespan,dependencies=[Depends(rate_limit)])
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://127.0.0.1:3000']+[origin for origin in os.getenv('WEB_ORIGINS','').split(',') if origin],allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])

@app.exception_handler(Exception)
async def unexpected_error(request:Request,error:Exception):
    logging.getLogger('uvicorn.error').error('Request failed path=%s type=%s',request.url.path,type(error).__name__)
    return JSONResponse(status_code=500,content={'detail':'The server could not complete this request. Please retry or check backend configuration.'})

@app.middleware('http')
async def request_timing(request,call_next):
    request_id=uid();start=time.monotonic()
    response=await call_next(request)
    response.headers['X-Request-ID']=request_id
    logging.getLogger('uvicorn.error').info('request=%s method=%s path=%s status=%s elapsed=%.2fs',request_id,request.method,request.url.path,response.status_code,time.monotonic()-start)
    return response

@app.get('/api/health')
def health():return {'status':'ok','product':'ClientPulse AI','gemini':available(),'auth':bool(os.getenv('SUPABASE_URL'))}

app.include_router(router)
