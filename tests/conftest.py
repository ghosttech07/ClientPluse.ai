import os
from uuid import uuid4
from pathlib import Path
root=Path('data')/('tests-'+str(uuid4()))
root=root.resolve();root.mkdir(parents=True,exist_ok=True)
os.environ['DATA_DIR']=str(root)
os.environ['DATABASE_URL']='sqlite:///'+str(root/'tests.db')
os.environ['DEMO_MODE']='true'
os.environ['GEMINI_API_KEY']=''
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.db import Base,engine
@pytest.fixture
def client():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    with TestClient(app) as c:yield c
@pytest.fixture
def workspace(client):
    return client.post('/api/workspaces',json={'name':'Test investigation','industry':'Manufacturing','description':'Test source-grounded flow'}).json()
