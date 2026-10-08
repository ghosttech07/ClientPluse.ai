"""Explicitly reviewed draft sending via Resend; no browser API secrets."""
import os,re
from email.utils import parseaddr
from datetime import datetime,timezone,timedelta
import httpx
from fastapi import Depends,HTTPException
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from services.api import pulse_models as m
from services.api.security import verified_email
from services.api.pulse import router,tenant,database,get


def valid_email(value):
    return bool(re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+",value)) and '\r' not in value and '\n' not in value


def sender():
    value=os.getenv('RESEND_FROM_EMAIL','').strip()
    address=parseaddr(value)[1]
    if not os.getenv('RESEND_API_KEY','').startswith('re_') or not valid_email(address) or any(word in address for word in ['yourdomain','your-actual-domain']) or '\n' in value or '\r' in value:
        raise HTTPException(503,'Email sending is not configured. Add a verified Resend sender address in the backend environment.')
    return value


class SendDraft(BaseModel):
    model_config={'extra':'forbid'}
    recipient:str=Field(min_length=3,max_length=254)
    content:str=Field(min_length=2,max_length=30000)
    @field_validator('recipient')
    @classmethod
    def email(cls,value):
        value=value.strip()
        if not valid_email(value):raise ValueError('Enter one valid recipient email address.')
        return value


@router.get('/email/config')
def config(org=Depends(tenant),reply=Depends(verified_email)):
    try:from_address=sender();ready=True;message=None
    except HTTPException as error:from_address=None;ready=False;message=error.detail
    return {'configured':ready,'from_email':from_address,'reply_to':reply,'message':message}


@router.get('/drafts/{did}/delivery')
def delivery(did:str,org=Depends(tenant),db=Depends(database)):
    get(db,m.Draft,did,org)
    row=db.scalar(select(m.EmailDelivery).where(m.EmailDelivery.draft_id==did,m.EmailDelivery.organization_id==org))
    return None if not row else {'status':row.status,'recipient':row.payload['to'][0],'provider_id':row.provider_id}


@router.post('/drafts/{did}/send')
def send(did:str,body:SendDraft,org=Depends(tenant),reply=Depends(verified_email),db=Depends(database)):
    draft=get(db,m.Draft,did,org)
    existing=db.scalar(select(m.EmailDelivery).where(m.EmailDelivery.draft_id==did,m.EmailDelivery.organization_id==org))
    if existing and existing.status=='Accepted':
        if existing.payload['to']!=[body.recipient] or existing.payload['text']!=body.content:raise HTTPException(409,'This draft has already been sent. Generate a new draft for another email.')
        return {'status':'Accepted','recipient':body.recipient,'provider_id':existing.provider_id}
    if draft.status!='Approved':raise HTTPException(409,'Approve the draft before sending it.')
    if draft.content!=body.content:raise HTTPException(409,'Save and approve your latest edits before sending.')
    if draft.kind!='Follow-up email':raise HTTPException(400,'Only follow-up email drafts can be sent to customers.')
    from_address=sender()
    subject=draft.title.replace('\r',' ').replace('\n',' ')
    payload={'from':from_address,'to':[body.recipient],'reply_to':reply,'subject':subject,'text':draft.content}
    if existing and existing.payload!=payload:raise HTTPException(409,'A send attempt already exists with different details. Keep the original recipient and content for a safe retry.')
    if existing and datetime.fromisoformat(existing.created_at.replace('Z','+00:00')).replace(tzinfo=timezone.utc)<datetime.now(timezone.utc)-timedelta(hours=23):
        raise HTTPException(409,'This send attempt is too old to retry safely. Check its status in Resend before taking further action.')
    if not existing:
        existing=m.EmailDelivery(organization_id=org,draft_id=did,payload=payload,status='Pending');db.add(existing)
        try:db.commit()
        except IntegrityError:db.rollback();raise HTTPException(409,'Another send request is in progress. Refresh the draft before retrying.')
    try:
        response=httpx.post('https://api.resend.com/emails',headers={'Authorization':'Bearer '+os.getenv('RESEND_API_KEY',''),'Idempotency-Key':'clientpulse-draft-'+existing.id},json=existing.payload,timeout=25)
    except httpx.HTTPError:raise HTTPException(502,'Resend could not confirm this send. Retry with the same recipient and draft; duplicate protection is enabled.')
    if response.status_code not in (200,201):
        if response.status_code in (401,403):message='Resend rejected the sender or key. Ask your administrator to verify the sending domain and API permissions.'
        elif response.status_code==429:message='Resend sending limit reached. Wait and retry the same draft.'
        else:message='Resend did not accept the email. Check the sending configuration and retry the same draft.'
        raise HTTPException(502,message)
    provider_id=response.json().get('id')
    if not provider_id:raise HTTPException(502,'Resend did not return a message reference. Retry the same draft.')
    existing.status='Accepted';existing.provider_id=provider_id;db.commit()
    return {'status':'Accepted','recipient':body.recipient,'provider_id':provider_id}
