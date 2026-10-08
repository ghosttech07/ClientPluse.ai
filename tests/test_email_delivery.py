import httpx
import pytest
from sqlalchemy import select
from services.api.main import app
from services.api.db import Session
from services.api import pulse_models as m
from services.api.security import verified_email

@pytest.fixture
def mail_setup(client,monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY','re_test_configuration_only')
    monkeypatch.setenv('RESEND_FROM_EMAIL','ClientPulse <support@verified.example>')
    app.dependency_overrides[verified_email]=lambda:'owner@example.com'
    with Session() as db:
        org=db.scalar(select(m.Organization).where(m.Organization.owner_id=='test-owner'))
        row=m.Draft(organization_id=org.id,kind='Follow-up email',title='Your support case',content='We have reviewed the recorded issue.',status='Approved',citations=[])
        db.add(row);db.commit();did=row.id
    return client,did

def test_send_acceptance_and_duplicate_protection(mail_setup,monkeypatch):
    client,did=mail_setup;calls=[]
    def post(url,**kwargs):calls.append(kwargs);return httpx.Response(200,json={'id':'provider-message-1'})
    monkeypatch.setattr('services.api.email_delivery.httpx.post',post)
    body={'recipient':'customer@example.com','content':'We have reviewed the recorded issue.'}
    first=client.post('/api/v1/drafts/'+did+'/send',json=body)
    assert first.status_code==200 and first.json()['status']=='Accepted'
    assert calls[0]['json']['reply_to']=='owner@example.com'
    assert calls[0]['json']['from']=='ClientPulse <support@verified.example>'
    assert calls[0]['json']['text']==body['content']
    assert calls[0]['headers']['Idempotency-Key'].startswith('clientpulse-draft-')
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==200
    assert len(calls)==1
    assert client.post('/api/v1/drafts/'+did+'/send',json={**body,'recipient':'other@example.com'}).status_code==409
    assert client.patch('/api/v1/drafts/'+did,json={'content':'Changed message','status':'Approved'}).status_code==409

def test_send_requires_approval_and_saved_content(mail_setup,monkeypatch):
    client,did=mail_setup
    monkeypatch.setattr('services.api.email_delivery.httpx.post',lambda *a,**k:pytest.fail('Unexpected send'))
    body={'recipient':'customer@example.com','content':'Unsaved edits'}
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==409
    with Session() as db:row=db.get(m.Draft,did);row.status='Draft';db.commit()
    body['content']='We have reviewed the recorded issue.'
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==409

def test_send_rejects_invalid_recipient_and_forged_reply(mail_setup):
    client,did=mail_setup
    assert client.post('/api/v1/drafts/'+did+'/send',json={'recipient':'bad-address','content':'Reviewed content'}).status_code==422
    assert client.post('/api/v1/drafts/'+did+'/send',json={'recipient':'customer@example.com','content':'Reviewed content','reply_to':'attacker@example.com'}).status_code==422

def test_pending_retry_reuses_key_and_payload(mail_setup,monkeypatch):
    client,did=mail_setup;calls=[]
    def post(url,**kwargs):
        calls.append(kwargs)
        if len(calls)==1:raise httpx.ReadTimeout('Timeout')
        return httpx.Response(200,json={'id':'provider-message-2'})
    monkeypatch.setattr('services.api.email_delivery.httpx.post',post)
    body={'recipient':'customer@example.com','content':'We have reviewed the recorded issue.'}
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==502
    assert client.post('/api/v1/drafts/'+did+'/send',json={**body,'recipient':'different@example.com'}).status_code==409
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==200
    assert calls[0]['headers']['Idempotency-Key']==calls[1]['headers']['Idempotency-Key']
    assert calls[0]['json']==calls[1]['json']

def test_missing_sender_and_cross_tenant_protection(mail_setup,monkeypatch):
    client,did=mail_setup
    monkeypatch.setenv('RESEND_FROM_EMAIL','')
    monkeypatch.setattr('services.api.email_delivery.httpx.post',lambda *a,**k:pytest.fail('Unexpected send'))
    body={'recipient':'customer@example.com','content':'We have reviewed the recorded issue.'}
    assert client.post('/api/v1/drafts/'+did+'/send',json=body).status_code==503
    with Session() as db:
        org=m.Organization(owner_id='other-owner',name='Other',settings={'onboarding_completed':True});db.add(org);db.flush()
        draft=m.Draft(organization_id=org.id,kind='Follow-up email',title='Private',content=body['content'],status='Approved');db.add(draft);db.commit();other=draft.id
    assert client.post('/api/v1/drafts/'+other+'/send',json=body).status_code==404
