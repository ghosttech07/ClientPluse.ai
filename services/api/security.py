import os, hashlib, base64, json, asyncio
from contextlib import asynccontextmanager
from collections import defaultdict, deque
from time import monotonic
import httpx
from fastapi import Header, HTTPException, Request

_auth_cache = {}
_auth_pending = {}
_auth_client = None

@asynccontextmanager
async def auth_transport():
    global _auth_client
    _auth_client = httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
    try:
        yield
    finally:
        pending=list(_auth_pending.values())
        for task in pending:task.cancel()
        if pending:await asyncio.gather(*pending,return_exceptions=True)
        _auth_pending.clear()
        await _auth_client.aclose()
        _auth_client=None

async def auth_account(authorization):
    url=os.getenv('SUPABASE_URL');key=os.getenv('SUPABASE_ANON_KEY')
    if not url or not key:raise HTTPException(503,'Supabase authentication is not configured.')
    try:
        if _auth_client is not None:
            return await _auth_client.get(f'{url}/auth/v1/user',headers={'Authorization':authorization,'apikey':key})
        async with httpx.AsyncClient(timeout=15) as client:
            return await client.get(f'{url}/auth/v1/user',headers={'Authorization':authorization,'apikey':key})
    except httpx.HTTPError:raise HTTPException(503,'Authentication service is unavailable. Please retry shortly.')

async def user(authorization: str | None = Header(None)):
    if authorization and authorization.startswith('Bearer '):
        cache_key=hashlib.sha256(authorization.encode()).hexdigest()
        cached=_auth_cache.get(cache_key)
        if cached and cached[1]>monotonic():return cached[0]
        task=_auth_pending.get(cache_key)
        if task is None:
            task=asyncio.create_task(auth_account(authorization));_auth_pending[cache_key]=task
        try:r=await asyncio.shield(task)
        finally:
            if task.done() and _auth_pending.get(cache_key) is task:_auth_pending.pop(cache_key,None)
        if r.status_code != 200: raise HTTPException(401, 'Your session expired. Please sign in again.')
        identity=r.json()['id']
        if len(_auth_cache)>512:_auth_cache.clear()
        # Cache only successfully verified sessions, briefly. Never log tokens.
        ttl=10
        try:
            from time import time
            encoded=authorization.split('.')[1]
            payload=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
            ttl=min(ttl,max(0,payload['exp']-time()))
        except (ValueError,KeyError,IndexError):ttl=0
        _auth_cache[cache_key]=(identity,monotonic()+ttl)
        return identity
    raise HTTPException(401, 'Sign in to access this workspace.')
_requests = defaultdict(deque)
def rate_limit(request: Request):
    key = request.client.host if request.client else 'unknown'
    q = _requests[key]; t = monotonic()
    while q and q[0] < t - 60: q.popleft()
    if len(q) >= 90: raise HTTPException(429, 'Too many requests. Please wait a minute.')
    q.append(t)


async def verified_email(authorization: str | None = Header(None)):
    """Read reply-to from the authenticated provider, never from a form or JWT claim."""
    identity=await user(authorization)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response=await client.get(os.getenv('SUPABASE_URL','')+'/auth/v1/user',headers={'Authorization':authorization,'apikey':os.getenv('SUPABASE_ANON_KEY','')})
        if response.status_code!=200:raise HTTPException(401,'Your session expired. Please sign in again.')
        account=response.json()
        if account.get('id')!=identity or not account.get('email') or not account.get('email_confirmed_at'):
            raise HTTPException(403,'Verify your account email before sending customer email.')
        return account['email']
    except httpx.HTTPError:raise HTTPException(503,'Unable to verify your reply address. Please retry.')
