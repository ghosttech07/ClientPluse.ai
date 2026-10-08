from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from sqlalchemy import select
from services.api.db import DATA, File, Segment, Message, Report, now
from services.api.intelligence import timeline

def make_report(db,w):
    report=Report(workspace_id=w.id,name=w.name+' — evidence report',path='')
    db.add(report); db.flush()
    directory=DATA/'reports'; directory.mkdir(exist_ok=True)
    path=directory/f'{report.id}.pdf'; report.path=str(path)
    styles=getSampleStyleSheet(); story=[]
    def p(text,style='BodyText'): story.append(Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])); story.append(Spacer(1,9))
    p('EVIDENCE.AI','Title'); p('Investigation evidence report','Heading1'); p(w.name,'Heading2')
    p(f'Industry: {w.industry} | Workspace: {w.id} | Generated: {now()}')
    p('1. Case information','Heading2'); p(w.description or 'No case description supplied.')
    p('2. Executive summary','Heading2')
    messages=list(db.scalars(select(Message).where(Message.workspace_id==w.id,Message.role=='assistant').order_by(Message.created_at)))
    p('This report inventories the stored evidence and saved analyses. It does not establish causation or make an authorized final decision.')
    p('3. Evidence inventory','Heading2')
    files=list(db.scalars(select(File).where(File.workspace_id==w.id)))
    for f in files: p(f'{f.name} | {f.mime} | {f.status} | {f.size} bytes')
    p('4. Key findings and possible explanations','Heading2')
    if not messages: p('No analysis has been saved. Ask the workspace assistant a question to include findings.')
    for m in messages[-3:]:
        for line in m.content.splitlines():
            line=line.strip()
            if not line:continue
            if line.startswith('## '):p(line[3:],'Heading3')
            else:p(line.replace('**',''))
        for i,c in enumerate(m.citations): p(f'[{i+1}] Source: {c["file_name"]} | page {c.get("page") or "n/a"} | seconds {c.get("timestamp") if c.get("timestamp") is not None else "n/a"} | row {c.get("row") or "n/a"} | evidence {c["id"]}')
    p('5. Chronological timeline','Heading2')
    events=timeline(db,w.id)
    if not events: p('No dated or timestamped evidence. Event times have not been inferred.')
    for e in events: p(f'{e["time"] or str(e["seconds"])+" seconds"}: {e["description"]} [source: {e["source"]["file_name"]}; {e["id"]}]')
    p('6. Supporting evidence','Heading2')
    for s in db.scalars(select(Segment).where(Segment.workspace_id==w.id).limit(50)):
        f=db.get(File,s.file_id); p(f'[{s.id}] {f.name}'+(f' / page {s.page}' if s.page else '')); p(s.content[:1800])
    for title,key in [('7. Potential inconsistencies','conflicting_information'),('8. Possible explanations','possible_explanations'),('9. Missing information','missing_information'),('10. Recommended next steps','recommended_next_checks')]:
        p(title,'Heading2'); values=messages[-1].analysis.get(key,[]) if messages else []
        for v in values: p(v.get('text','') if isinstance(v,dict) else v)
        if not values: p('No structured finding recorded for this section.')
    p('11. Limitations and human review','Heading2'); p('Uploaded evidence is untrusted. Model observations can be inaccurate. Correlation is not proof of causation. Sparse video sampling is incomplete. Verify engineering interventions with qualified personnel. Insurance, legal and financial decisions require an authorized human reviewer. This report is limited to indexed sources in this workspace.')
    def footer(canvas,doc):
        canvas.setFillColor(colors.HexColor('#64748b')); canvas.setFont('Helvetica',8); canvas.drawString(36,22,'EVIDENCE.AI • Traceable intelligence'); canvas.drawRightString(A4[0]-36,22,f'Page {doc.page}')
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=45,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
    db.commit(); return report

