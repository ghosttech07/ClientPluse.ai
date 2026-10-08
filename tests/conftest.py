import os
from uuid import uuid4
from pathlib import Path
root=Path('data')/('tests-'+str(uuid4()))
root=root.resolve();root.mkdir(parents=True,exist_ok=True)
os.environ['DATA_DIR']=str(root)
os.environ['DATABASE_URL']='sqlite:///'+str(root/'tests.db')
os.environ['GEMINI_API_KEY']=''
os.environ['HF_ENABLED']='false'
os.environ['STORAGE_PROVIDER']='local'
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.db import Base,engine
from services.api.security import user
@pytest.fixture
def client():
    from services.api.security import _requests
    _requests.clear()
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    async def test_user(): return 'test-owner'
    app.dependency_overrides[user]=test_user
    try:
        with TestClient(app) as c:yield c
    finally: app.dependency_overrides.clear()
