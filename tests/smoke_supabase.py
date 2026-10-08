"""Opt-in real auth/isolation check using two temporary confirmed test accounts; no email is sent."""
import os,secrets,uuid
import httpx
from dotenv import load_dotenv
load_dotenv()
url=os.getenv('SUPABASE_URL');public=os.getenv('SUPABASE_ANON_KEY');secret=os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not all((url,public,secret)):raise SystemExit('Not run: Supabase URL, public key and backend service-role key required.')
admin={'apikey':secret,'Authorization':'Bearer '+secret}
api=os.getenv('API_URL','http://127.0.0.1:8000')
users=[];workspaces=[]
with httpx.Client(timeout=30) as c:
    try:
        tokens=[]
        for _ in range(2):
            email='evidence-qa-'+uuid.uuid4().hex+'@example.com';password=secrets.token_urlsafe(28)
            r=c.post(url+'/auth/v1/admin/users',headers=admin,json={'email':email,'password':password,'email_confirm':True})
            if r.status_code not in (200,201):raise RuntimeError('Temporary Auth account setup failed (HTTP '+str(r.status_code)+').')
            users.append(r.json()['id'])
            r=c.post(url+'/auth/v1/token?grant_type=password',headers={'apikey':public},json={'email':email,'password':password})
            if r.status_code!=200:raise RuntimeError('Real password login failed (HTTP '+str(r.status_code)+').')
            tokens.append(r.json()['access_token'])
        owner={'Authorization':'Bearer '+tokens[0]};other={'Authorization':'Bearer '+tokens[1]}
        r=c.post(api+'/api/workspaces',headers=owner,json={'name':'Temporary account isolation test','industry':'Insurance','description':'Automated disposable test case'})
        assert r.status_code==201,'Authenticated workspace creation failed.'
        wid=r.json()['id'];workspaces.append((wid,owner))
        assert c.get(api+'/api/workspaces/'+wid,headers=owner).status_code==200
        assert c.get(api+'/api/workspaces/'+wid,headers=other).status_code==404
        assert c.post(api+'/api/workspaces/'+wid+'/ask',headers=other,json={'question':'Read another account?'}).status_code==404
        assert c.get(api+'/api/workspaces',headers={'Authorization':'Bearer invalid-test-token'}).status_code==401
        print('Live Supabase password login, token validation, owner access and cross-account denial passed.')
    finally:
        for wid,headers in workspaces:
            r=c.delete(api+'/api/workspaces/'+wid,headers=headers)
            if r.status_code!=200:print('Cleanup needs attention: temporary workspace deletion failed.')
        for user_id in users:
            r=c.delete(url+'/auth/v1/admin/users/'+user_id,headers=admin)
            if r.status_code not in (200,204):print('Cleanup needs attention: temporary test account deletion failed.')
