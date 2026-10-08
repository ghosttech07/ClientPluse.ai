import os
from collections import defaultdict, deque
from time import monotonic
import httpx
from fastapi import Header, HTTPException, Request
from services.api.db import Workspace

async def user(authorization: str | None = Header(None)):
    if authorization and authorization.startswith('Bearer '):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        if not url or not key: raise HTTPException(503, 'Supabase authentication is not configured.')
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(f'{url}/auth/v1/user', headers={'Authorization': authorization, 'apikey': key})
        except httpx.HTTPError: raise HTTPException(503,'Authentication service is unavailable. Please retry shortly.')
        if r.status_code != 200: raise HTTPException(401, 'Your session expired. Please sign in again.')
        return r.json()['id']
    raise HTTPException(401, 'Sign in to access this workspace.')
def authorize(db, workspace_id, user_id):
    w = db.get(Workspace, workspace_id)
    if not w or w.owner_id != user_id: raise HTTPException(404, 'Workspace not found.')
    return w
_requests = defaultdict(deque)
def rate_limit(request: Request):
    key = request.client.host if request.client else 'unknown'
    q = _requests[key]; t = monotonic()
    while q and q[0] < t - 60: q.popleft()
    if len(q) >= 90: raise HTTPException(429, 'Too many requests. Please wait a minute.')
    q.append(t)
