from types import SimpleNamespace

from services.worker import huggingface as hf


def test_hf_embedding_dispatch(monkeypatch):
    from services.worker import ai
    monkeypatch.setenv('HF_ENABLED', 'true')
    monkeypatch.setenv('HF_TOKEN', 'test-not-a-real-token')
    monkeypatch.setattr(hf, 'embeddings', lambda texts: [[1., 2.] for _ in texts])
    assert ai.embed(['evidence']) == [[1., 2.]]


def test_incompatible_embeddings_do_not_affect_ranking(monkeypatch):
    from services.api import intelligence
    monkeypatch.setenv('HF_ENABLED', 'true')
    monkeypatch.setenv('HF_TOKEN', 'test-not-a-real-token')
    row=SimpleNamespace(content='fuse evidence', embedding=[1., 0.], meta={'embedding_model':'gemini:gemini-embedding-001'})
    monkeypatch.setattr(intelligence, 'embed', lambda *args: (_ for _ in ()).throw(AssertionError('must not query incompatible vectors')))
    db=SimpleNamespace(scalars=lambda *args:[row])
    assert intelligence.retrieve(db, 'test', 'fuse') == [row]


def test_audio_hf_extraction_has_honest_provenance(tmp_path, monkeypatch):
    from services.worker import processors
    monkeypatch.setenv('HF_ENABLED', 'true')
    monkeypatch.setenv('HF_TOKEN', 'test-not-a-real-token')
    monkeypatch.setattr(hf, 'transcribe', lambda path:'The inspection found belt wear.')
    path=tmp_path/'audio.wav'
    items, meta, partial=processors.extract(path,'audio/wav')
    assert items[0]['content']=='The inspection found belt wear.'
    assert 'Hugging Face' in meta['extraction']
    assert 'timestamp' not in items[0]


def test_hf_failure_keeps_gemini_workflow(tmp_path, monkeypatch):
    from services.worker import processors
    from services.worker.ai import Extraction
    monkeypatch.setenv('HF_ENABLED','true')
    monkeypatch.setenv('HF_TOKEN','test-not-a-real-token')
    monkeypatch.setattr(hf,'transcribe',lambda path: (_ for _ in ()).throw(RuntimeError('not available')))
    monkeypatch.setattr(processors,'available',lambda:True)
    monkeypatch.setattr(processors,'analyze_media',lambda *args:Extraction(items=[{'content':'Fallback observation'}]))
    items, meta, _=processors.extract(tmp_path/'audio.wav','audio/wav')
    assert items[0]['content']=='Fallback observation'
    assert 'Gemini was used instead' in meta['limitations'][0]


def test_billing_error_is_safe():
    error=SimpleNamespace(response=SimpleNamespace(status_code=402))
    assert 'credits' in hf.safe_error(error)
