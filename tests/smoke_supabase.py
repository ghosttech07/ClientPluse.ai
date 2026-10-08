"""Opt-in real auth/isolation check using two temporary confirmed test accounts; no email is sent."""
import os,secrets,uuid,time,io,tempfile,wave,subprocess,math,struct
import httpx
from dotenv import load_dotenv
load_dotenv()
url=os.getenv('SUPABASE_URL');public=os.getenv('SUPABASE_ANON_KEY');secret=os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not all((url,public,secret)):raise SystemExit('Not run: Supabase URL, public key and backend service-role key required.')
admin={'apikey':secret,'Authorization':'Bearer '+secret}
api=os.getenv('QA_API_BASE',os.getenv('API_URL','http://127.0.0.1:8000'))
users=[];workspaces=[];credentials=[]
with httpx.Client(timeout=180) as c:
    try:
        tokens=[]
        for _ in range(2):
            email='evidence-qa-'+uuid.uuid4().hex+'@example.com';password=secrets.token_urlsafe(28)
            credentials.append({'email':email,'password':password})
            r=c.post(url+'/auth/v1/admin/users',headers=admin,json={'email':email,'password':password,'email_confirm':True})
            if r.status_code not in (200,201):raise RuntimeError('Temporary Auth account setup failed (HTTP '+str(r.status_code)+').')
            users.append(r.json()['id'])
            r=c.post(url+'/auth/v1/token?grant_type=password',headers={'apikey':public},json={'email':email,'password':password})
            if r.status_code!=200:raise RuntimeError('Real password login failed (HTTP '+str(r.status_code)+').')
            tokens.append(r.json()['access_token'])
        owner={'Authorization':'Bearer '+tokens[0]};other={'Authorization':'Bearer '+tokens[1]}
        r=c.post(api+'/api/workspaces',headers=owner,json={'name':'Temporary account isolation test','industry':'Education','description':'Automated disposable test case'})
        assert r.status_code==201,'Authenticated workspace creation failed.'
        wid=r.json()['id'];workspaces.append((wid,owner))
        assert c.get(api+'/api/workspaces/'+wid,headers=owner).status_code==200
        assert c.get(api+'/api/workspaces/'+wid,headers=other).status_code==404
        assert c.post(api+'/api/workspaces/'+wid+'/ask',headers=other,json={'question':'Read another account?'}).status_code==404
        assert c.get(api+'/api/workspaces',headers={'Authorization':'Bearer invalid-test-token'}).status_code==401
        print('Live Supabase password login, token validation, owner access and cross-account denial passed.')
        if os.getenv('QA_FULL_PIPELINE')=='1':
            from PIL import Image,ImageDraw
            from reportlab.pdfgen.canvas import Canvas
            from docx import Document
            from pathlib import Path
            from services.worker.processors import binary
            with tempfile.TemporaryDirectory(prefix='evidence-qa-') as directory:
                root=Path(directory)
                (root/'note.txt').write_text('Synthetic test: Machine A inspection recorded belt wear. The cause is unknown.',encoding='utf-8')
                (root/'measurements.csv').write_text('timestamp,machine,value\n2026-10-08T10:00:00Z,Machine A,2\n2026-10-08T10:10:00Z,Machine A,8\n',encoding='utf-8')
                pdf=Canvas(str(root/'inspection.pdf'));pdf.drawString(40,750,'Synthetic inspection: Machine A belt wear recorded. Cause unknown.');pdf.save()
                document=Document();document.add_paragraph('Synthetic maintenance record: Machine A requires belt inspection.');document.save(root/'maintenance.docx')
                image=Image.new('RGB',(640,400),'white');draw=ImageDraw.Draw(image);draw.text((30,80),'SYNTHETIC QA: MACHINE A - INSPECT BELT',fill='black',font_size=22);image.save(root/'label.png')
                with wave.open(str(root/'tone.wav'),'wb') as wav:
                    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b''.join(struct.pack('<h',int(12000*math.sin(2*math.pi*440*i/16000))) for i in range(32000)))
                subprocess.run([binary('ffmpeg'),'-y','-loop','1','-i',str(root/'label.png'),'-t','2','-r','10','-pix_fmt','yuv420p',str(root/'label.mp4')],check=True,capture_output=True)
                uploaded=c.post(api+'/api/workspaces/'+wid+'/files',headers=owner,files=[('files',(p.name,p.read_bytes())) for p in root.iterdir()])
                assert uploaded.status_code==201,uploaded.text
                start=time.monotonic();last=None
                while time.monotonic()-start<600:
                    detail=c.get(api+'/api/workspaces/'+wid,headers=owner).json()
                    statuses={f['name']:f['status'] for f in detail['files']}
                    if statuses!=last:print('Live processing:',statuses,flush=True);last=statuses
                    assert not any(f['status']=='Failed' for f in detail['files']),[(f['name'],f['error']) for f in detail['files'] if f['status']=='Failed']
                    if all(s in ('Ready','Partially Processed') for s in statuses.values()):break
                    time.sleep(4)
                else:raise AssertionError('Live processing did not finish within the test deadline.')
                assert {'document','data','image','audio','video'}<={s['modality'] for s in detail['segments']}
                assert next(f for f in detail['files'] if f['name']=='measurements.csv')['meta']['statistics']['value']['mean']==5
                began=time.monotonic()
                answer=c.post(api+'/api/workspaces/'+wid+'/ask',headers=owner,json={'question':'Summarize what the sources say about Machine A and belt inspection. Distinguish observations from unknown causes.'})
                assert answer.status_code==200,answer.text
                result=answer.json();assert result['analysis']['mode']=='gemini' and result['analysis']['observed_facts']
                valid={s['id'] for s in detail['segments']};assert all(s['id'] in valid for s in result['citations'])
                print('Live cited answer succeeded in %.1fs'%(time.monotonic()-began),flush=True)
                assert len(c.get(api+'/api/workspaces/'+wid+'/messages',headers=owner).json())==2
                assert c.get(api+'/api/workspaces/'+wid+'/graph',headers=owner).json()['nodes']
                assert len(c.get(api+'/api/workspaces/'+wid+'/timeline',headers=owner).json())>=2
                study=c.post(api+'/api/workspaces/'+wid+'/study',headers=owner);assert study.status_code==200,study.text;assert study.json()['flashcards']
                report=c.post(api+'/api/workspaces/'+wid+'/reports',headers=owner);assert report.status_code==201,report.text
                downloaded=c.get(api+'/api/reports/'+report.json()['id']+'/download',headers=owner);assert downloaded.content.startswith(b'%PDF-')
                first=detail['files'][0]['id'];assert c.get(api+'/api/files/'+first+'/content',headers=owner).status_code==200
                assert c.get(api+'/api/files/'+first+'/content',headers=other).status_code==404
                assert c.get(api+'/api/reports/'+report.json()['id']+'/download',headers=other).status_code==404
                print('Live seven-format uploads, five modalities, cited answer, history, graph, timeline, study, PDF and private access passed.',flush=True)
        if os.getenv('QA_BROWSER_HOLD')=='1':
            import json
            from pathlib import Path
            state=Path('data/browser-qa-auth.json');done=Path('data/browser-qa-done')
            done.unlink(missing_ok=True)
            c.post(api+'/api/workspaces/'+wid+'/files',headers=owner,files={'files':('browser-check.txt',b'Synthetic browser QA: Machine A belt wear was recorded during inspection. The cause is unknown.')}).raise_for_status()
            state.write_text(json.dumps({**credentials[0],'workspace_id':wid}),encoding='utf-8')
            print('Temporary browser test is ready; cleanup follows browser completion.',flush=True)
            deadline=time.monotonic()+300
            while not done.exists() and time.monotonic()<deadline:time.sleep(2)
            state.unlink(missing_ok=True);done.unlink(missing_ok=True)
    finally:
        for wid,headers in workspaces:
            r=c.delete(api+'/api/workspaces/'+wid,headers=headers)
            deadline=time.monotonic()+180
            while r.status_code==409 and time.monotonic()<deadline:
                time.sleep(4)
                r=c.delete(api+'/api/workspaces/'+wid,headers=headers)
            if r.status_code!=200:print('Cleanup needs attention: temporary workspace deletion failed.')
        for user_id in users:
            r=c.delete(url+'/auth/v1/admin/users/'+user_id,headers=admin)
            if r.status_code not in (200,204):print('Cleanup needs attention: temporary test account deletion failed.')
