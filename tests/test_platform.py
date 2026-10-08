import io, json
from pathlib import Path
import pytest
from sqlalchemy import select
from services.api.db import Session,Workspace,File,Segment,Job,uid
from services.worker.processors import validate,extract,process
from services.worker.main import run_once
from services.api.security import user
from services.api.main import app
from services.worker.ai import Extraction,ExtractedItem,Reasoning,Claim

def upload(client,w,data=b'Machine A belt wear recorded. Grinding noise needs inspection.',name='note.txt'):
    r=client.post(f'/api/workspaces/{w["id"]}/files',files={'files':(name,data)})
    assert r.status_code==201,r.text
    return r.json()[0]
def test_auth_required(client,monkeypatch):
    app.dependency_overrides.clear()
    assert client.get('/api/workspaces').status_code==401
def test_workspace_isolation(client,workspace):
    async def outsider():return 'another-user'
    app.dependency_overrides[user]=outsider
    try:
        assert client.get('/api/workspaces').json()==[]
        assert client.get('/api/workspaces/'+workspace['id']).status_code==404
        assert client.post('/api/workspaces/'+workspace['id']+'/ask',json={'question':'Machine A?'}).status_code==404
    finally:app.dependency_overrides.clear()
def test_create_validation(client):
    assert client.post('/api/workspaces',json={'name':'x','industry':'Other'}).status_code==422
@pytest.mark.parametrize('data,name',[(b'bad','bad.pdf'),(b'','empty.txt'),(b'MZbad','run.exe'),(b'bad','a.png'),(b'bad','a.wav'),(b'bad','a.mp3'),(b'bad','a.mp4'),(b'\x00','a.txt'),(b'bad','a.docx')])
def test_file_validation(data,name):
    with pytest.raises(ValueError):validate(data,name)
def test_upload_lifecycle(client,workspace):
    f=upload(client,workspace);assert f['status']=='Queued'
    assert run_once()
    detail=client.get('/api/files/'+f['id']).json();assert detail['status']=='Ready'
    w=client.get('/api/workspaces/'+workspace['id']).json();assert w['segments'][0]['file_id']==f['id']
    assert client.get('/api/files/'+f['id']+'/content').content.startswith(b'Machine A')
def test_pdf_page_citation(tmp_path):
    from reportlab.pdfgen.canvas import Canvas
    p=tmp_path/'sample.pdf';c=Canvas(str(p));c.drawString(40,750,'Machine A belt inspection');c.showPage();c.drawString(40,750,'Second page bearing observation');c.save()
    items,meta,partial=extract(p,'application/pdf');assert meta['pages']==2;assert {i['page'] for i in items}=={1,2};assert not partial
def test_csv_real_statistics_and_timeline(client,workspace):
    f=upload(client,workspace,b'timestamp,machine,value\n2026-10-04T11:20:00+05:30,Machine A,2\n2026-10-04T11:30:00+05:30,Machine A,8\n','sensors.csv');run_once()
    d=client.get('/api/files/'+f['id']).json();assert d['meta']['statistics']['value']['mean']==5
    t=client.get('/api/workspaces/'+workspace['id']+'/timeline').json();assert len(t)==2;assert t[0]['source']['row']==2;assert t[0]['source']['file_id']==f['id']
def test_retrieval_and_citations(client,workspace):
    f=upload(client,workspace);run_once()
    result=client.post('/api/workspaces/'+workspace['id']+'/ask',json={'question':'What does evidence say about Machine A belt wear?'}).json()
    assert result['citations'][0]['file_id']==f['id'];assert result['analysis']['mode']=='local_retrieval'
    assert len(client.get('/api/workspaces/'+workspace['id']+'/messages').json())==2
def test_insufficient_evidence(client,workspace):
    result=client.post('/api/workspaces/'+workspace['id']+'/ask',json={'question':'What happened?'}).json()
    assert not result['citations'];assert result['analysis']['mode']=='insufficient_evidence'
def test_graph_has_supporting_evidence(client,workspace):
    f=upload(client,workspace);run_once();g=client.get('/api/workspaces/'+workspace['id']+'/graph').json()
    assert g['edges'];assert g['edges'][0]['source']==f['id'];assert g['edges'][0]['evidence_id'];assert not g['edges'][0]['inferred']
def test_no_invented_timeline(client,workspace):
    upload(client,workspace);run_once();assert client.get('/api/workspaces/'+workspace['id']+'/timeline').json()==[]
def test_report_pdf(client,workspace):
    upload(client,workspace);run_once()
    r=client.post('/api/workspaces/'+workspace['id']+'/reports');assert r.status_code==201
    pdf=client.get('/api/reports/'+r.json()['id']+'/download');assert pdf.content.startswith(b'%PDF-')
    import pymupdf
    doc=pymupdf.open(stream=pdf.content,filetype='pdf');txt=''.join(p.get_text() for p in doc)
    assert 'Test investigation' in txt and 'note.txt' in txt and 'Machine A belt wear' in txt
def test_delete_cascades(client,workspace):
    f=upload(client,workspace);run_once();assert client.delete('/api/files/'+f['id']).status_code==200
    assert not client.get('/api/workspaces/'+workspace['id']).json()['segments']
    assert client.delete('/api/workspaces/'+workspace['id']).status_code==200
    assert client.get('/api/workspaces/'+workspace['id']).status_code==404
def test_retry_does_not_duplicate(client,workspace):
    f=upload(client,workspace);run_once()
    with Session() as db:item=db.get(File,f['id']);item.status='Failed';db.commit()
    assert client.post('/api/files/'+f['id']+'/retry').status_code==200;run_once()
    with Session() as db:assert len(list(db.scalars(select(Segment).where(Segment.file_id==f['id']))))==1
def test_media_missing_key_is_honest(client,workspace):
    from PIL import Image
    buf=io.BytesIO();Image.new('RGB',(10,10)).save(buf,format='PNG');f=upload(client,workspace,buf.getvalue(),'photo.png');run_once()
    d=client.get('/api/files/'+f['id']).json();assert d['status']=='Failed';assert 'Gemini' in d['error']
@pytest.mark.parametrize('mime',['image/png','audio/wav','video/mp4'])
def test_media_adapter_integration(tmp_path,monkeypatch,mime):
    import services.worker.processors as p
    monkeypatch.setattr(p,'available',lambda:True)
    monkeypatch.setattr(p,'analyze_media',lambda path,m:Extraction(items=[ExtractedItem(content='Source-grounded sample observation',timestamp=2 if m!='image/png' else None)],limitations=['Synthetic mocked provider']))
    monkeypatch.setattr(p.shutil,'which',lambda name:'ffprobe')
    from types import SimpleNamespace
    monkeypatch.setattr(p.subprocess,'run',lambda *a,**kw:SimpleNamespace(stdout='{"format":{"duration":"5"}}'))
    path=tmp_path/'media';path.write_bytes(b'sample')
    items,meta,_=extract(path,mime);assert items[0]['content'];assert 'Synthetic mocked provider' in meta['limitations']
def test_invalid_ai_citation_rejected(client,workspace,monkeypatch):
    upload(client,workspace);run_once()
    import services.api.intelligence as intelligence
    monkeypatch.setattr(intelligence,'available',lambda:True)
    monkeypatch.setattr(intelligence,'generate',lambda *args:Reasoning(summary='bad',observed_facts=[Claim(text='Claim',evidence_ids=['invented'])],possible_explanations=[],conflicting_information=[],missing_information=[],recommended_next_checks=[]))
    r=client.post('/api/workspaces/'+workspace['id']+'/ask',json={'question':'Machine A belt wear'});assert r.status_code==502
def test_removed_seed_endpoint(client):
    assert client.post("/api/demo").status_code == 404
