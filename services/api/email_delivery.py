"""Explicitly reviewed draft sending via Resend; no browser API secrets."""
import os,re,smtplib,ssl,base64
from email.message import EmailMessage
from email.utils import make_msgid
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
    if os.getenv('EMAIL_PROVIDER','resend').strip().lower()=='gmail_api':
        address=os.getenv('GMAIL_EMAIL','').strip()
        if not valid_email(address) or not all(os.getenv(key,'').strip() for key in ('GMAIL_CLIENT_ID','GMAIL_CLIENT_SECRET','GMAIL_REFRESH_TOKEN')):
            raise HTTPException(503,'Complete Gmail API authorization: configure GMAIL_EMAIL, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN on the backend.')
        return address
    if os.getenv('EMAIL_PROVIDER','resend').strip().lower()=='gmail':
        address=os.getenv('GMAIL_EMAIL','').strip()
        if not valid_email(address) or not os.getenv('GMAIL_APP_PASSWORD','').strip():
            raise HTTPException(503,'Configure GMAIL_EMAIL and GMAIL_APP_PASSWORD in the backend .env.')
        return address
    value=os.getenv('RESEND_FROM_EMAIL','').strip()
    address=parseaddr(value)[1]
    if not os.getenv('RESEND_API_KEY','').startswith('re_') or not valid_email(address) or any(word in address for word in ['yourdomain','your-actual-domain']) or '\n' in value or '\r' in value:
        raise HTTPException(503,'Email sending is not configured. Add a verified Resend sender address in the backend environment.')
    return value


def gmail_access_token():
    """Validate OAuth before attempting delivery; never expose provider secrets."""
    credentials={key:os.getenv(key,'').strip().strip('"\'') for key in ('GMAIL_CLIENT_ID','GMAIL_CLIENT_SECRET','GMAIL_REFRESH_TOKEN')}
    if any(any(character.isspace() for character in value) for value in credentials.values()):
        raise HTTPException(503,'Gmail OAuth credentials contain spaces or line breaks. Paste each complete value on one line in Render.')
    try:
        response=httpx.post('https://oauth2.googleapis.com/token',data={
            'client_id':credentials['GMAIL_CLIENT_ID'],
            'client_secret':credentials['GMAIL_CLIENT_SECRET'],
            'refresh_token':credentials['GMAIL_REFRESH_TOKEN'],
            'grant_type':'refresh_token',
        },timeout=20)
        data=response.json()
    except (httpx.HTTPError,ValueError):
        raise HTTPException(503,'Unable to reach Google authorization. Please retry shortly; no email was sent.')
    if response.status_code!=200:
        reasons={
            'invalid_client':'Google rejected the OAuth client ID or client secret. Use the matching credentials from the same Google Cloud client.',
            'invalid_grant':'Google rejected the refresh token. It may be expired, revoked, or issued to a different OAuth client. Generate a new token using the exact client ID and secret configured in Render.',
            'unauthorized_client':'This OAuth client is not authorized for token refresh. Check its Google Cloud OAuth configuration.',
        }
        raise HTTPException(503,reasons.get(data.get('error'),'Google token refresh failed. Check the Gmail OAuth configuration.'))
    access_token=data.get('access_token')
    if not access_token:
        raise HTTPException(503,'Google did not return an access token. Reconnect the Gmail account.')
    return access_token


def gmail_api_send(message):
    """Refresh server-only OAuth credentials and send over HTTPS, without retries."""
    access_token=gmail_access_token()
    try:
        response=httpx.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers={'Authorization':'Bearer '+access_token},
            json={'raw':base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')},timeout=25)
        if response.status_code!=200:
            raise HTTPException(502,'Google did not accept the email. Check Gmail API access, send permission and account sending limits. Check Sent before creating another draft.')
        provider_id=response.json().get('id')
        if not provider_id:
            raise HTTPException(502,'Google did not confirm the message reference. Check Sent before creating another draft.')
        return provider_id
    except (httpx.HTTPError,ValueError):
        raise HTTPException(502,'Gmail API could not confirm the send. Check Sent before creating another draft to avoid duplicates.')


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
    try:
        from_address=sender();ready=True;message=None
        if os.getenv('EMAIL_PROVIDER','resend').strip().lower()=='gmail_api':gmail_access_token()
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
    provider=os.getenv('EMAIL_PROVIDER','resend').strip().lower()
    gmail=provider in ('gmail','gmail_api')
    if gmail and existing:
        raise HTTPException(409,'This draft already has a send attempt. Check your Sent folder before generating a new draft; automatic retries could send duplicates.')
    subject=draft.title.replace('\r',' ').replace('\n',' ')
    payload={'from':from_address,'to':[body.recipient],'reply_to':reply,'subject':subject,'text':draft.content}
    if existing and existing.payload!=payload:raise HTTPException(409,'A send attempt already exists with different details. Keep the original recipient and content for a safe retry.')
    if existing and datetime.fromisoformat(existing.created_at.replace('Z','+00:00')).replace(tzinfo=timezone.utc)<datetime.now(timezone.utc)-timedelta(hours=23):
        raise HTTPException(409,'This send attempt is too old to retry safely. Check its status in Resend before taking further action.')
    if not existing:
        existing=m.EmailDelivery(organization_id=org,draft_id=did,payload=payload,status='Pending');db.add(existing)
        try:db.commit()
        except IntegrityError:db.rollback();raise HTTPException(409,'Another send request is in progress. Refresh the draft before retrying.')
    if gmail:
        message=EmailMessage()
        message['From']=from_address
        message['To']=body.recipient
        message['Reply-To']=reply
        message['Subject']=subject
        message['Message-ID']=make_msgid()
        message.set_content(draft.content)
        if provider=='gmail_api':
            existing.provider_id=gmail_api_send(message)
            existing.status='Accepted';db.commit()
            return {'status':'Accepted','recipient':body.recipient,'provider_id':existing.provider_id}
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com',465,context=ssl.create_default_context(),timeout=25) as smtp:
                smtp.login(from_address,os.getenv('GMAIL_APP_PASSWORD','').replace(' ',''))
                smtp.send_message(message)
                existing.status='Accepted';existing.provider_id=str(message['Message-ID']);db.commit()
        except smtplib.SMTPAuthenticationError:
            raise HTTPException(502,'Gmail rejected the credentials. Check the Gmail address and app password, then generate a new draft.')
        except (smtplib.SMTPException,OSError):
            if existing.status!='Accepted':
                raise HTTPException(502,'Gmail could not confirm the send. Check your Sent folder before generating another draft to avoid duplicates.')
        return {'status':'Accepted','recipient':body.recipient,'provider_id':existing.provider_id}
    try:
        response=httpx.post('https://api.resend.com/emails',headers={'Authorization':'Bearer '+os.getenv('RESEND_API_KEY',''),'Idempotency-Key':'clientpulse-draft-'+existing.id},json=existing.payload,timeout=25)
    except httpx.HTTPError:raise HTTPException(502,'Resend could not confirm this send. Retry with the same recipient and draft; duplicate protection is enabled.')
    if response.status_code not in (200,201):
        if response.status_code in (401,403):
            message='Resend rejected the sender or key. Ask your administrator to verify the sending domain and API permissions.'
            try:provider_message=response.json().get('message','')
            except ValueError:provider_message=''
            if isinstance(provider_message,str) and provider_message.startswith('You can only send testing emails to your own email address'):
                match=re.search(r'\(([^()]+)\)',provider_message)
                account=match.group(1) if match and valid_email(match.group(1)) else None
                message='Resend test mode allows sending only to '+(account or 'the email registered with your Resend account')+'. Generate a new draft for that recipient, or verify your own sending domain to email customers.'
        elif response.status_code==429:message='Resend sending limit reached. Wait and retry the same draft.'
        else:message='Resend did not accept the email. Check the sending configuration and retry the same draft.'
        raise HTTPException(502,message)
    provider_id=response.json().get('id')
    if not provider_id:raise HTTPException(502,'Resend did not return a message reference. Retry the same draft.')
    existing.status='Accepted';existing.provider_id=provider_id;db.commit()
    return {'status':'Accepted','recipient':body.recipient,'provider_id':provider_id}
