"""Optional private Supabase mirror. Local files are the shared API/worker processing cache."""
import os
from urllib.parse import quote
import httpx

def enabled():return os.getenv('STORAGE_PROVIDER','local')=='supabase'
def settings():
    url=os.getenv('SUPABASE_URL');key=os.getenv('SUPABASE_SERVICE_ROLE_KEY');bucket=os.getenv('SUPABASE_STORAGE_BUCKET','evidence')
    if not url or not key:raise ValueError('Supabase storage requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the backend.')
    return url,{'apikey':key,'Authorization':'Bearer '+key},bucket
def store(key,data,mime):
    if not enabled():return
    url,headers,bucket=settings()
    with httpx.Client(timeout=60) as c:
        r=c.post(f'{url}/storage/v1/object/{bucket}/{quote(key)}',content=data,headers={**headers,'Content-Type':mime,'x-upsert':'false'})
        if r.status_code not in (200,201):raise ValueError('Private storage upload failed. Check bucket and service credentials.')
def signed(key):
    url,headers,bucket=settings()
    with httpx.Client(timeout=15) as c:
        r=c.post(f'{url}/storage/v1/object/sign/{bucket}/{quote(key)}',json={'expiresIn':120},headers=headers);r.raise_for_status()
    path=r.json()['signedURL'];return url+'/storage/v1'+path if path.startswith('/object/') else url+path
def remove(key):
    url,headers,bucket=settings()
    with httpx.Client(timeout=15) as c:
        r=c.request('DELETE',f'{url}/storage/v1/object/{bucket}',json={'prefixes':[key]},headers=headers)
        r.raise_for_status()
