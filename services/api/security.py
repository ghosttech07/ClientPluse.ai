import os, hashlib, base64, json
from collections import defaultdict, deque
from time import monotonic
import httpx
from fastapi import Header, HTTPException, Request

_auth_cache = {}

async def user(authorization: str | None = Header(None)):
    if authorization and authorization.startswith('Bearer '):
        cache_key=hashlib.sha256(authorization.encode()).hexdigest()
        cached=_auth_cache.get(cache_key)
        if cached and cached[1]>monotonic():return cached[0]
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        if not url or not key: raise HTTPException(503, 'Supabase authentication is not configured.')
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(f'{url}/auth/v1/user', headers={'Authorization': authorization, 'apikey': key})
        except httpx.HTTPError: raise HTTPException(503,'Authentication service is unavailable. Please retry shortly.')
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
