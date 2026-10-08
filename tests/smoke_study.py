"""Opt-in source-grounded education smoke with synthetic uploaded material."""
import httpx,time
BASE='http://127.0.0.1:8000'
material='''SYNTHETIC EDUCATION QA NOTES
Database normalization organizes relational tables to reduce repeated information and update anomalies.
First normal form uses atomic values and avoids repeating groups.
Second normal form requires first normal form and no partial dependency on a composite candidate key.
Third normal form requires second normal form and no transitive dependency of a non-key attribute on a key.
An update anomaly can occur when the same customer address is repeated in several order rows and only some copies are updated.
A study example separates Customers(customer_id, address) from Orders(order_id, customer_id).
A foreign key connects the order to the customer. This example is instructional, not a production schema recommendation.
'''
with httpx.Client(timeout=180) as c:
    r=c.post(BASE+'/api/workspaces',json={'name':'Synthetic learning QA','industry':'Education','description':'Temporary source-grounded quiz test'});r.raise_for_status();wid=r.json()['id']
    try:
        r=c.post(BASE+'/api/workspaces/'+wid+'/files',files={'files':('study-notes.txt',material.encode(),'text/plain')});r.raise_for_status()
        for _ in range(50):
            w=c.get(BASE+'/api/workspaces/'+wid).json()
            if w['files'][0]['status']=='Ready':break
            if w['files'][0]['status']=='Failed':raise RuntimeError('Education source ingestion failed.')
            time.sleep(1)
        assert w['files'][0]['status']=='Ready'
        r=c.post(BASE+'/api/workspaces/'+wid+'/study');r.raise_for_status();result=r.json();ids={s['id'] for s in w['segments']}
        assert result['questions'] and result['flashcards']
        for q in result['questions']:assert q['evidence_id'] in ids and len(q['options'])==4 and q['correct_index'] in range(4)
        for card in result['flashcards']:assert card['evidence_id'] in ids
        print('Live study guide, flashcards, quiz format and source citations passed.')
    finally:
        r=c.delete(BASE+'/api/workspaces/'+wid)
        if r.status_code!=200:print('Temporary study workspace remains; check processing status before cleanup.')
