import asyncio
import base64
import json
import time

import httpx
import pytest
from fastapi import HTTPException
from services.api import security


def token(label):
    payload=base64.urlsafe_b64encode(json.dumps({'exp':time.time()+60}).encode()).decode().rstrip('=')
    return f'Bearer {label}.{payload}.test'


def test_concurrent_auth_requests_share_verification(monkeypatch):
    calls=[]
    async def verify(value):
        calls.append(value)
        await asyncio.sleep(0)
        return httpx.Response(200,json={'id':'verified-user'})
    monkeypatch.setattr(security,'auth_account',verify)
    security._auth_cache.clear()
    async def check():
        results=await asyncio.gather(*(security.user(token_value) for _ in range(8)))
        assert results==['verified-user']*8
        assert len(calls)==1
        assert await security.user(token_value)=='verified-user'
        assert len(calls)==1
        assert not security._auth_pending
    token_value=token('shared')
    asyncio.run(check())
    security._auth_cache.clear()


def test_invalid_session_is_not_cached(monkeypatch):
    calls=[]
    async def verify(value):
        calls.append(value)
        return httpx.Response(401,json={})
    monkeypatch.setattr(security,'auth_account',verify)
    security._auth_cache.clear()
    async def check():
        for _ in range(2):
            with pytest.raises(HTTPException) as error:await security.user(token_value)
            assert error.value.status_code==401
        assert len(calls)==2
        assert not security._auth_cache
        assert not security._auth_pending
    token_value=token('invalid')
    asyncio.run(check())


def test_different_sessions_do_not_share_identity(monkeypatch):
    async def verify(value):
        await asyncio.sleep(0)
        return httpx.Response(200,json={'id':value.split('.')[0]})
    monkeypatch.setattr(security,'auth_account',verify)
    security._auth_cache.clear()
    async def check():
        assert await asyncio.gather(security.user(token('alice')),security.user(token('bob')))==['Bearer alice','Bearer bob']
    asyncio.run(check())
    security._auth_cache.clear()
