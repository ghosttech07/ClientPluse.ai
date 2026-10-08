"""Run after uploading synthetic fixtures in the website; validates actual stored results without substitutes."""
import os,httpx
from dotenv import load_dotenv
load_dotenv()
BASE=os.getenv('API_URL','http://127.0.0.1:8000')
with httpx.Client(timeout=180) as c:
    cases=c.get(BASE+'/api/workspaces').json()
    w=next((x for x in cases if x['name']=='Live multimodal upload check'),None)
    if not w:raise SystemExit('Not run: create the Live multimodal upload check workspace and upload fixtures first.')
    detail=c.get(BASE+'/api/workspaces/'+w['id']).json()
    statuses={f['name']:f['status'] for f in detail['files']};print('Actual upload statuses:',statuses)
    if any(s!='Ready' for s in statuses.values()):raise SystemExit('Not complete: wait for worker or resolve Failed statuses.')
    modalities={s['modality'] for s in detail['segments']}
    assert {'image','video','audio','document','data'}<=modalities
    assert any('bent' in s['content'].lower() and s['modality']=='audio' for s in detail['segments']), 'Actual speech was not transcribed.'
    r=c.post(BASE+'/api/workspaces/'+w['id']+'/ask',json={'question':'Compare the package label, video, narrated statement, invoice and delivery log. What is directly observed and what remains unknown?'})
    assert r.status_code==200,'Live grounded reasoning failed.'
    result=r.json();assert result['analysis']['mode']=='gemini'
    valid={s['id'] for s in detail['segments']}
    for citation in result['citations']:assert citation['id'] in valid
    assert result['analysis']['observed_facts']
    report=c.post(BASE+'/api/workspaces/'+w['id']+'/reports');assert report.status_code==201
    pdf=c.get(BASE+'/api/reports/'+report.json()['id']+'/download');assert pdf.content.startswith(b'%PDF-')
    from pathlib import Path
    output=Path('data/qa-media/live-evidence-report.pdf');output.write_bytes(pdf.content)
    print('Live five-modality extraction, speech transcription, source-ID validation, grounded reasoning and PDF report passed.')
