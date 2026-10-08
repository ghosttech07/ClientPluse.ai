"""Opt-in real auth, private storage, Gemini and browser verification using synthetic inputs."""
import json
import os
import secrets
import time
from pathlib import Path
from uuid import uuid4
import httpx
from dotenv import load_dotenv


def main():
    load_dotenv();api=os.getenv('QA_API_BASE','http://127.0.0.1:3000');url=os.environ['SUPABASE_URL'];admin_key=os.environ['SUPABASE_SERVICE_ROLE_KEY'];anon=os.environ['SUPABASE_ANON_KEY']
    admin={'apikey':admin_key,'Authorization':'Bearer '+admin_key};created=[];customers=[];owner_ids=[];auth=None
    auth_path=Path('data/clientpulse-qa-auth.json');done=Path('data/clientpulse-qa-done')
    with httpx.Client(timeout=170,follow_redirects=True) as client:
        try:
            ready=time.monotonic()+60
            while time.monotonic()<ready:
                try:
                    if client.get(api+'/api/health').status_code==200:break
                except httpx.RequestError:pass
                time.sleep(1)
            else:raise AssertionError('API did not become ready before live verification.')
            for index in range(2):
                email=f'clientpulse-qa-{uuid4().hex}@example.com';password=secrets.token_urlsafe(24)
                result=client.post(url+'/auth/v1/admin/users',headers=admin,json={'email':email,'password':password,'email_confirm':True});result.raise_for_status();owner_ids.append(result.json()['id'])
                token=client.post(url+'/auth/v1/token?grant_type=password',headers={'apikey':anon},json={'email':email,'password':password});token.raise_for_status();created.append({'Authorization':'Bearer '+token.json()['access_token']})
                setup=client.post(api+'/api/v1/onboarding',headers=created[-1],json={'name':'Synthetic QA company'});setup.raise_for_status()
                if index==0:auth={'email':email,'password':password}
            owner,outsider=created
            result=client.post(api+'/api/v1/customers',headers=owner,json={'name':'SYNTHETIC QA Acme Retail','email':'customer0@clientpulse.example','account_ref':'QA-ACME'});result.raise_for_status();cid=result.json()['id'];customers.append(cid);auth['customer_id']=cid
            root=Path('fixtures/clientpulse');specs=[('call-01-transcript.txt','2026-10-03T10:00:00+00:00'),('email-01.eml','2026-10-05T10:00:00+00:00'),('chat-01.png','2026-10-07T10:00:00+00:00')]
            audio_key='SARVAM_API_KEY' if os.getenv('SPEECH_PROVIDER','deepgram')=='sarvam' else 'DEEPGRAM_API_KEY'
            if os.getenv(audio_key):specs[0]=('call-01.wav','2026-10-03T10:00:00+00:00')
            else:print('Speech provider key missing: spoken audio is NOT verified. Using the labelled transcript fixture for correlation QA.',flush=True)
            for filename,date in specs:
                result=client.post(api+'/api/v1/uploads',headers=owner,data={'customer_id':cid,'communication_at':date},files={'files':(filename,(root/filename).read_bytes())});result.raise_for_status()
                fid=result.json()[0]['id'];deadline=time.monotonic()+240
                while time.monotonic()<deadline:
                    detail=client.get(api+'/api/v1/uploads/'+fid,headers=owner);detail.raise_for_status();file=detail.json()
                    if file['status']=='Failed':raise AssertionError(file['error'])
                    if file['status']=='Ready':break
                    time.sleep(2)
                else:raise AssertionError('Processing timed out.')
                assert file['evidence'];source=client.get(api+'/api/v1/uploads/'+fid+'/content',headers=owner);source.raise_for_status();assert source.content
                assert client.get(api+'/api/v1/uploads/'+fid+'/content',headers=outsider).status_code==404
                print(filename+': Ready, private original accessible only to owner',flush=True)
            profile=client.get(api+'/api/v1/customers/'+cid,headers=owner);profile.raise_for_status();profile=profile.json()
            assert len(profile['complaints'])==1,[(case['category'],case['reference']) for case in profile['complaints']]
            assert profile['complaints'][0]['interaction_count']==3
            print('Synthetic QA risk:',profile['risk']['score'],profile['risk']['category'],flush=True)
            print('Synthetic QA finding signals:',[{key:f.get(key) for key in ('actor','severity','cancellation','follow_up','status')} for f in profile['complaints'][0]['findings']],flush=True)
            assert profile['risk']['category'] in ('High','Critical')
            assert any(a['kind']=='Cancellation' for a in client.get(api+'/api/v1/alerts',headers=owner).json()), 'Explicit conditional cancellation threat was not surfaced.'
            valid={e['id'] for e in client.get(api+'/api/v1/customers/'+cid+'/timeline',headers=owner).json()}
            began=time.monotonic();answer=client.post(api+'/api/v1/intelligence/query',headers=owner,json={'customer_id':cid,'question':'Why does this customer need attention? Cite the recurring delivery issue and cancellation statement.'});answer.raise_for_status();answer=answer.json()
            assert answer['citations'] and all(e['id'] in valid for e in answer['citations']);print('Cited assistant answer:',round(time.monotonic()-began,1),'seconds',flush=True)
            result=client.post(api+'/api/v1/drafts',headers=owner,json={'customer_id':cid,'kind':'Follow-up email'});result.raise_for_status();draft=result.json();assert draft['status']=='Draft' and draft['citations']
            report=client.get(api+'/api/v1/drafts/'+draft['id']+'/download',headers=owner);report.raise_for_status();assert report.content.startswith(b'%PDF')
            assert client.get(api+'/api/v1/customers/'+cid,headers=outsider).status_code==404
            print('Correlated case, explained risk, alert, cited answer, draft and PDF verified.',flush=True)
            if os.getenv('QA_BROWSER_HOLD')=='1':
                auth_path.write_text(json.dumps(auth),encoding='utf-8');print('Browser QA ready; credentials are in an ignored local file.',flush=True)
                deadline=time.monotonic()+600
                while not done.exists() and time.monotonic()<deadline:time.sleep(1)
        finally:
            auth_path.unlink(missing_ok=True);done.unlink(missing_ok=True)
            if created:
                for cid in customers:
                    result=client.delete(api+'/api/v1/customers/'+cid,headers=created[0])
                    if result.status_code not in (200,404):print('Customer cleanup requires attention:',result.status_code)
            for owner_id in owner_ids:
                response=client.delete(url+'/auth/v1/admin/users/'+owner_id,headers=admin);response.raise_for_status()
            from services.api.db import Session
            from services.api.pulse_models import Organization
            from sqlalchemy import select
            with Session() as db:
                for organization in db.scalars(select(Organization).where(Organization.owner_id.in_(owner_ids))):db.delete(organization)
                db.commit()
            print('Temporary QA accounts and tenant records removed.',flush=True)


if __name__=='__main__':main()
