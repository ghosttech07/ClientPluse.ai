import io
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from PIL import Image
from services.api.db import Session
from services.api import pulse_models as m
from services.api.security import user
from services.api.main import app
from services.worker import pulse as worker
from services.worker.ai import Extraction


@pytest.fixture
def customer(client):
    response=client.post('/api/v1/customers',json={'name':'Acme Retail','email':'buyer@acme.example','account_ref':'ACME-001'})
    assert response.status_code==201,response.text
    return response.json()


def finding(evidence,status='Open',follow=False,cancel=False,reference='ORD-1042'):
    return worker.Findings(findings=[worker.Finding(category='Delivery delay',description='Shipment ORD-1042 has not arrived',evidence_ids=[evidence[0].id],reference=reference,severity='High',actor='Customer',status=status,follow_up=follow,cancellation=cancel,escalation=cancel,uncertainty='Source statement, delivery not independently verified.')])


def ticket(client,customer,text='Customer: order ORD-1042 is delayed.',days=5):
    response=client.post('/api/v1/tickets',json={'customer_id':customer['id'],'subject':'Shipment ORD-1042','content':text,'communication_at':(datetime.now(timezone.utc)-timedelta(days=days)).isoformat()})
    assert response.status_code==201,response.text
    return response.json()


def test_acme_three_channels_one_case(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'audio_extract',lambda path:([{'content':'Customer: shipment ORD-1042 has not arrived.','timestamp':1.2}],{'extraction':'Mock Deepgram'},False))
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    audio=b'RIFF'+b'\0'*4+b'WAVE'+b'\0'*100
    date=(datetime.now(timezone.utc)-timedelta(days=5)).isoformat()
    result=client.post('/api/v1/uploads',data={'customer_id':customer['id'],'communication_at':date},files={'files':('call.wav',audio,'audio/wav')})
    assert result.status_code==201,result.text
    assert worker.run_once()
    message=EmailMessage();message['From']='buyer@acme.example';message['To']='support@vendor.example';message['Subject']='ORD-1042 still delayed';message['Date']='Mon, 05 Oct 2026 10:00:00 +0000';message.set_content('Customer: order ORD-1042 still has not arrived. Following up.')
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence,follow=True))
    response=client.post('/api/v1/uploads',files={'files':('followup.eml',message.as_bytes(),'message/rfc822')})
    assert response.status_code==201
    assert worker.run_once()
    with Session() as db:
        email=db.get(m.Upload,response.json()[0]['id']);assert email.customer_id==customer['id']
    image=io.BytesIO();Image.new('RGB',(100,100),'white').save(image,format='PNG')
    import services.worker.ai as ai
    monkeypatch.setattr(worker,'generate',lambda *args:Extraction(items=[{'content':'Customer: ORD-1042 still missing. I will cancel if this is not fixed.'}]))
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence,follow=True,cancel=True))
    response=client.post('/api/v1/uploads',data={'customer_id':customer['id'],'communication_at':datetime.now(timezone.utc).isoformat()},files={'files':('chat.png',image.getvalue(),'image/png')})
    assert response.status_code==201
    assert worker.run_once()
    profile=client.get('/api/v1/customers/'+customer['id']).json()
    assert len(profile['complaints'])==1
    case=profile['complaints'][0]
    assert case['interaction_count']==3 and len(case['evidence'])==3
    assert profile['risk']['category']=='Critical'
    assert profile['risk']['score']>=80
    assert all(factor['evidence_ids'] for factor in profile['risk']['factors'])
    assert len(client.get('/api/v1/customers/'+customer['id']+'/timeline').json())==3
    assert any(alert['kind']=='Cancellation' for alert in client.get('/api/v1/alerts').json())
    assert client.post('/api/v1/uploads/'+response.json()[0]['id']+'/retry').status_code==409


def test_resolution_is_not_future_promise(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    ticket(client,customer);worker.run_once()
    ticket(client,customer,'Employee: We promise to resolve ORD-1042 tomorrow.',days=2);worker.run_once()
    assert client.get('/api/v1/customers/'+customer['id']).json()['complaints'][0]['status']=='Open'
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence,status='Resolved'))
    ticket(client,customer,'Customer: ORD-1042 arrived and the issue is resolved.',days=0);worker.run_once()
    profile=client.get('/api/v1/customers/'+customer['id']).json()
    assert profile['complaints'][0]['status']=='Resolved' and profile['risk']['score']==0


def test_unrelated_order_and_customer_not_merged(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    ticket(client,customer);worker.run_once()
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence,reference='ORD-9999'))
    ticket(client,customer,'Customer: ORD-9999 is delayed.');worker.run_once()
    assert len(client.get('/api/v1/customers/'+customer['id']).json()['complaints'])==2
    other=client.post('/api/v1/customers',json={'name':'Acme Retail Similar'}).json()
    ticket(client,other);worker.run_once()
    assert len(client.get('/api/v1/customers/'+other['id']).json()['complaints'])==1


def test_identity_unknown_and_duplicate_alias(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    response=client.post('/api/v1/uploads',files={'files':('unknown.txt',b'Customer named Acme has a concern.','text/plain')})
    worker.run_once()
    assert client.get('/api/v1/uploads/'+response.json()[0]['id']).json()['status']=='Needs review'
    response=client.post('/api/v1/customers',json={'name':'Another company','email':'buyer@acme.example'})
    assert response.status_code==409


def test_tenant_isolation_and_citation_filter(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    upload=ticket(client,customer);worker.run_once()
    from services.api.pulse import query_evidence
    with Session() as db:
        org=db.get(m.Customer,customer['id']).organization_id
        assert query_evidence(db,org,'delivery',customer['id'])
        assert not query_evidence(db,'another-organization','delivery')
    async def outsider():return 'another-owner'
    app.dependency_overrides[user]=outsider
    assert client.post('/api/v1/onboarding',json={'name':'Other company'}).status_code==200
    assert client.get('/api/v1/customers/'+customer['id']).status_code==404
    assert client.get('/api/v1/uploads/'+upload['id']+'/content').status_code==404
    assert client.get('/api/v1/customers').json()==[]


def test_email_parser_and_schema(tmp_path):
    email=tmp_path/'message.eml';email.write_text('From: buyer@acme.example\nTo: support@example.com\nSubject: Invoice\nDate: Mon, 05 Oct 2026 10:00:00 +0000\n\nPlease check invoice INV-32.')
    items,metadata,_=worker.parse_email(email)
    assert metadata['addresses']==['buyer@acme.example','support@example.com']
    assert metadata['date'].startswith('2026-10-05')
    assert 'INV-32' in items[0]['content']
    email.write_text('From: buyer@acme.example\nTo: support@example.com\nMIME-Version: 1.0\nContent-Type: multipart/alternative; boundary="test"\n\n--test\nContent-Type: text/html\n\n<p>Invoice &amp; refund INV-33</p><script>ignore-me</script>\n--test--')
    items,_,_=worker.parse_email(email)
    assert 'Invoice & refund INV-33' in items[0]['content'] and 'ignore-me' not in items[0]['content']
    with pytest.raises(ValueError):worker.Findings(findings=[{'category':'Invented'}])


def test_failure_visible_and_insufficient_risk(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    item=ticket(client,customer);worker.run_once()
    assert client.get('/api/v1/uploads/'+item['id']).json()['status']=='Failed'
    risk=client.get('/api/v1/customers/'+customer['id']+'/risk').json()
    assert risk['score'] is None and risk['category']=='Insufficient evidence'
    assert client.post('/api/v1/uploads',files={'files':('unsafe.exe',b'data','application/octet-stream')}).status_code==400


def test_neutral_evidence_and_human_resolution(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:worker.Findings(findings=[]))
    ticket(client,customer,'Customer: thank you for the update.');worker.run_once()
    assert client.get('/api/v1/complaints').json()==[]
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    ticket(client,customer);worker.run_once()
    case=client.get('/api/v1/complaints').json()[0]
    assert client.patch('/api/v1/complaints/'+case['id'],json={'status':'Resolved','note':'Verified delivery with customer'}).status_code==200
    assert client.get('/api/v1/customers/'+customer['id']+'/risk').json()['score']==0


def test_customer_delete_cascades(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    item=ticket(client,customer);worker.run_once()
    assert client.delete('/api/v1/customers/'+customer['id']).status_code==200
    assert client.get('/api/v1/uploads/'+item['id']).status_code==404
    assert client.get('/api/v1/complaints').json()==[]
    assert client.get('/api/v1/alerts').json()==[]


def test_invalid_ai_citations_rejected(monkeypatch):
    evidence=SimpleNamespace(id='real-id',content='Customer issue',occurred_at=None,page=None,timestamp=None)
    monkeypatch.setattr(worker,'available',lambda:True)
    monkeypatch.setattr(worker,'generate',lambda *args:worker.Findings(findings=[worker.Finding(category='Other',description='Issue',evidence_ids=['fake-id'],severity='Low',actor='Unknown',uncertainty='Unknown context')]))
    with pytest.raises(ValueError,match='invalid source'):worker.analyse([evidence])


def test_pdf_page_references_and_file_validation(tmp_path):
    from reportlab.pdfgen import canvas
    from services.worker.processors import extract
    from services.api.pulse import file_validation
    path=tmp_path/'note.pdf';document=canvas.Canvas(str(path));document.drawString(30,700,'Customer: shipment ORD-1042 has not arrived.');document.save()
    assert file_validation(path.read_bytes(),'note.pdf')=='application/pdf'
    items,meta,_=extract(path,'application/pdf')
    assert items[0]['page']==1 and 'ORD-1042' in items[0]['content']
    with pytest.raises(ValueError):file_validation(b'fake','note.pdf')
    with pytest.raises(ValueError):file_validation(b'not an email','note.eml')


def test_deepgram_preserves_segments_and_speaker_numbers(tmp_path,monkeypatch):
    import httpx
    monkeypatch.setenv('SPEECH_PROVIDER','deepgram')
    monkeypatch.setenv('DEEPGRAM_API_KEY','synthetic-test-key')
    real_client=httpx.Client
    def respond(request):
        assert request.headers['Authorization']=='Token synthetic-test-key'
        return httpx.Response(200,json={'results':{'utterances':[{'transcript':'Customer: the order is late.','start':2.1,'speaker':0}]}})
    monkeypatch.setattr(worker.httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(respond)))
    path=tmp_path/'call.wav';path.write_bytes(b'RIFF-test')
    items,meta,_=worker.audio_extract(path)
    assert items[0]['timestamp']==2.1 and items[0]['meta']['speaker']==0
    assert 'not verified identities' in meta['limitations'][0]


def test_sarvam_preserves_timestamp_speaker_and_requires_key(tmp_path,monkeypatch):
    from services.worker.sarvam import transcript_items
    items=transcript_items({'diarized_transcript':{'entries':[{'transcript':'The order is delayed.','speaker_id':'1','start_time_seconds':2.2,'end_time_seconds':5.0}]}})
    assert items[0]['timestamp']==2.2 and items[0]['meta']=={'speaker':'1','end_seconds':5.0}
    assert transcript_items({'transcript':'Readable speech'})[0]['content']=='Readable speech'
    with pytest.raises(ValueError):transcript_items({'transcript':''})
    monkeypatch.setenv('SPEECH_PROVIDER','sarvam');monkeypatch.delenv('SARVAM_API_KEY',raising=False)
    with pytest.raises(ValueError,match='SARVAM_API_KEY'):worker.audio_extract(tmp_path/'call.wav')


def test_spoken_order_normalization_requires_explicit_label(monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:True)
    def generated(*args):return worker.Findings(findings=[worker.Finding(category='Delivery delay',description='Delayed shipment',evidence_ids=['source'],reference='1042',severity='Moderate',actor='Customer',deadline='2026-10-02',uncertainty='Reported customer statement')])
    monkeypatch.setattr(worker,'generate',generated)
    source=SimpleNamespace(id='source',content='Shipment order 1042 has not arrived.',occurred_at=None,page=None,timestamp=None)
    result=worker.analyse([source]).findings[0]
    assert result.reference=='ORD-1042' and result.deadline is None
    source.content='Invoice 1042 is disputed.'
    assert worker.analyse([source]).findings[0].reference=='1042'


def test_assistant_rejects_unrelated_customer_citation(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    ticket(client,customer);worker.run_once()
    from services.api import pulse
    monkeypatch.setattr(pulse,'available',lambda:True)
    monkeypatch.setattr(pulse,'generate',lambda *args:pulse.Answer(claims=[{'text':'Unsupported answer','evidence_ids':['another-customer-id']}],limitations=[]))
    result=client.post('/api/v1/intelligence/query',json={'customer_id':customer['id'],'question':'Why is this customer at risk?'})
    assert result.status_code==502 and 'invalid customer citation' in result.json()['detail']


def test_retry_does_not_duplicate_case(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    item=ticket(client,customer);worker.run_once()
    assert client.get('/api/v1/uploads/'+item['id']).json()['status']=='Failed'
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    assert client.post('/api/v1/uploads/'+item['id']+'/retry').status_code==200
    worker.run_once()
    assert len(client.get('/api/v1/complaints').json())==1
    assert client.post('/api/v1/uploads/'+item['id']+'/retry').status_code==409


def test_unauthenticated_access_denied(client):
    app.dependency_overrides.pop(user)
    assert client.get('/api/v1/customers').status_code==401


def test_settings_validation_and_real_dashboard(client,customer):
    summary=client.get('/api/v1/dashboard/summary').json()
    assert summary['total_customers']==1 and summary['high_risk_customers']==0
    assert summary['risk_distribution']['Insufficient evidence']==1
    assert client.patch('/api/v1/settings',json={'name':'My organization','risk_weights':{'invalid':9}}).status_code==422


def test_company_setup_required_before_workspace_access(client):
    with Session() as db:
        org=db.scalar(select(m.Organization).where(m.Organization.owner_id=='test-owner'))
        org.settings={};db.commit()
    assert client.get('/api/v1/customers').status_code==403
    assert client.get('/api/v1/settings').json()['onboarding_required'] is True
    assert client.post('/api/v1/onboarding',json={'name':'  '}).status_code==422
    assert client.post('/api/v1/onboarding',json={'name':'  Acme Ltd  '}).json()['name']=='Acme Ltd'
    assert client.get('/api/v1/customers').status_code==200
    assert client.get('/api/v1/settings').json()['onboarding_required'] is False


def test_manual_processing_success(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    item=ticket(client,customer,'Customer: order ORD-1042 was delayed.',days=1)
    fid=item['id']
    # Verify initial status is Queued
    assert client.get(f'/api/v1/uploads/{fid}').json()['status']=='Queued'
    # Manually process via FastAPI endpoint without worker
    res=client.post(f'/api/v1/uploads/{fid}/process')
    assert res.status_code==200, res.text
    assert res.json()['status']=='Ready'
    # Verify evidence and complaints were extracted
    detail=client.get(f'/api/v1/uploads/{fid}').json()
    assert len(detail['evidence'])>=1
    profile=client.get('/api/v1/customers/'+customer['id']).json()
    assert len(profile['complaints'])==1
    assert profile['complaints'][0]['category']=='Delivery delay'


def test_manual_processing_duplicate_protection(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    item=ticket(client,customer,'Customer: order ORD-1042 was delayed.')
    fid=item['id']
    # First manual process
    res=client.post(f'/api/v1/uploads/{fid}/process')
    assert res.status_code==200
    # Duplicate processing on Ready file rejected with 409
    dup=client.post(f'/api/v1/uploads/{fid}/process')
    assert dup.status_code==409
    assert 'already been processed' in dup.json()['detail']
    # Processing an in-flight job also rejected with 409
    item2=ticket(client,customer,'Customer: order ORD-1043 is delayed.')
    fid2=item2['id']
    with Session() as db:
        up=db.get(m.Upload,fid2)
        up.status='Processing'
        up.lease_at=datetime.now(timezone.utc).isoformat()
        db.commit()
    in_flight=client.post(f'/api/v1/uploads/{fid2}/process')
    assert in_flight.status_code==409
    assert 'currently being processed' in in_flight.json()['detail']


def test_manual_processing_failure_and_retry(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    item=ticket(client,customer)
    fid=item['id']
    # Processing fails because Gemini analysis not available
    fail_res=client.post(f'/api/v1/uploads/{fid}/process')
    assert fail_res.status_code==422
    assert client.get(f'/api/v1/uploads/{fid}').json()['status']=='Failed'
    # Provide working mock and retry via process
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    retry_res=client.post(f'/api/v1/uploads/{fid}/process')
    assert retry_res.status_code==200
    assert retry_res.json()['status']=='Ready'


def test_manual_processing_cross_tenant_denied(client,customer):
    with Session() as db:
        other_org=m.Organization(owner_id='other-owner',name='Other Corp',settings={'onboarding_completed':True})
        db.add(other_org);db.flush()
        other_upload=m.Upload(id='other-upload-1',organization_id=other_org.id,name='secret.txt',mime='text/plain',source_type='Document',path='dummy',size=10,status='Queued')
        db.add(other_upload);db.commit()
    # Attempting to process other tenant's upload must return 404
    assert client.post('/api/v1/uploads/other-upload-1/process').status_code==404


def test_process_queued_batch(client,customer,monkeypatch):
    monkeypatch.setattr(worker,'available',lambda:False)
    monkeypatch.setattr(worker,'analyse',lambda evidence:finding(evidence))
    t1=ticket(client,customer,'Customer: issue one')
    t2=ticket(client,customer,'Customer: issue two')
    batch_res=client.post('/api/v1/uploads/process-queued?limit=5')
    assert batch_res.status_code==200
    assert batch_res.json()['processed_count']==2
    assert client.get(f'/api/v1/uploads/{t1["id"]}').json()['status']=='Ready'
    assert client.get(f'/api/v1/uploads/{t2["id"]}').json()['status']=='Ready'
