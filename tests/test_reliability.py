import httpx
from types import SimpleNamespace
from sqlalchemy import select
from services.api.db import Session, Segment
from services.worker.main import run_once
from services.worker.ai import Extraction, provider_error
from tests.test_platform import upload


def test_embedding_failure_preserves_extracted_text(client, workspace, monkeypatch):
    import services.worker.processors as processor
    monkeypatch.setattr(processor, 'available', lambda: True)
    def unavailable(*args):
        raise httpx.ReadTimeout('test provider timeout')
    monkeypatch.setattr(processor, 'embed', unavailable)
    file = upload(client, workspace)
    run_once()
    detail = client.get('/api/files/' + file['id']).json()
    assert detail['status'] == 'Ready'
    assert detail['meta']['semantic_indexing'] == 'unavailable'
    assert 'searchable by text' in detail['meta']['limitations'][0]
    assert client.get('/api/workspaces/' + workspace['id']).json()['segments']


def test_query_embedding_failure_uses_existing_evidence(client, workspace, monkeypatch):
    from services.api import intelligence
    upload(client, workspace)
    run_once()
    with Session() as db:
        row = db.scalar(select(Segment))
        row.embedding = [0.2, 0.5]
        db.commit()
    monkeypatch.setattr(intelligence, 'available', lambda: True)
    def unavailable(*args):
        raise httpx.ReadTimeout('test provider timeout')
    monkeypatch.setattr(intelligence, 'embed', unavailable)
    with Session() as db:
        rows = intelligence.retrieve(db, workspace['id'], 'Summarize this source')
        assert rows and 'Machine A' in rows[0].content


def test_workspace_summary_counts(client, workspace):
    file = upload(client, workspace)
    summary = client.get('/api/workspaces').json()[0]
    assert summary['file_count'] == 1 and summary['processing_count'] == 1
    run_once()
    summary = client.get('/api/workspaces').json()[0]
    assert summary['ready_count'] == 1 and summary['processing_count'] == 0
    assert client.get('/api/files/' + file['id']).headers.get('X-Request-ID')


def test_missing_model_tries_configured_fallback(monkeypatch):
    import services.worker.ai as ai
    from google.genai import errors
    called = []
    def generate_content(**kwargs):
        called.append(kwargs['model'])
        if len(called) == 1:
            raise errors.ClientError(404, {'error': {'message': 'missing test model'}})
        return SimpleNamespace(text='{"items":[{"content":"A real supplied observation"}],"limitations":[]}')
    monkeypatch.setattr(ai, 'client', lambda: SimpleNamespace(models=SimpleNamespace(generate_content=generate_content), close=lambda: None))
    monkeypatch.setenv('GEMINI_MODEL', 'missing-test-model')
    monkeypatch.setenv('GEMINI_FALLBACK_MODELS', 'available-test-model')
    assert ai.generate('source', Extraction).items
    assert called == ['missing-test-model', 'available-test-model']


def test_provider_errors_are_actionable():
    assert 'too long' in provider_error(httpx.ReadTimeout('timeout'))
    assert 'connect' in provider_error(httpx.ConnectError('unavailable'))
