from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from xml.sax.saxutils import escape

ROOT=Path(__file__).parent/'datasets'
def pdf(path,title,sections,table=None):
    styles=getSampleStyleSheet();story=[]
    def add(text,style='BodyText'):
        story.append(Paragraph(escape(text),styles[style]));story.append(Spacer(1,12))
    add('EVIDENCE.AI / SYNTHETIC DEMONSTRATION','Heading3');add(title,'Title')
    add('Fictional sample data. Not a real incident, invoice, or engineering record.','BodyText')
    for heading,text in sections:add(heading,'Heading2');add(text)
    if table:
        t=Table([[Paragraph(escape(str(c)),styles['BodyText']) for c in r] for r in table],colWidths=[240,230])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceaf2')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#aec5d5')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
        story.append(t)
    def footer(c,d):c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#668099'));c.drawString(40,25,'SYNTHETIC EVIDENCE | EVIDENCE.AI');c.drawRightString(A4[0]-40,25,str(d.page))
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=45,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
def generate():
    delivery=ROOT/'delivery';manufacturing=ROOT/'manufacturing'
    delivery.mkdir(parents=True,exist_ok=True);manufacturing.mkdir(parents=True,exist_ok=True)
    pdf(delivery/'sample-invoice.pdf','Invoice INV-1042',[('Order information','Order ORD-1042. Fictional vendor: Meridian Devices. Recipient: Demo Customer. Order date: 2026-10-02. Item: 14-inch laptop. One unit. Invoice value INR 64,900. The invoice establishes the item ordered and does not establish the condition at delivery.'),('Review notice','No warranty or insurance decision is implied by this sample document.')], [['Item','Amount'],['14-inch laptop / one unit','INR 64,900'],['Order reference','ORD-1042']])
    (delivery/'customer-statement.txt').write_text('SYNTHETIC DEMONSTRATION DATA\nCustomer statement for Order ORD-1042.\nI received the laptop package on 2026-10-03 at about 14:35. I noticed a crushed corner on the outer box. When I opened it, I saw a crack near the lower right of the screen. I took photographs after opening the package. I did not witness any handling in the warehouse or during transit. The damage may have occurred before delivery, but I do not know when.\n',encoding='utf-8')
    (delivery/'delivery-events.csv').write_text('timestamp,order,event,condition,source\n2026-10-03T08:10:00+05:30,ORD-1042,Packed,No damage recorded,Synthetic packing log\n2026-10-03T09:20:00+05:30,ORD-1042,Loaded,Condition not inspected,Synthetic dispatch log\n2026-10-03T11:05:00+05:30,ORD-1042,Transferred,Package condition unknown,Synthetic hub log\n2026-10-03T14:35:00+05:30,ORD-1042,Delivered,Marked intact by courier,Synthetic delivery log\n2026-10-03T14:55:00+05:30,ORD-1042,Complaint received,Crushed corner and cracked screen reported,Synthetic customer service log\n',encoding='utf-8')
    pdf(manufacturing/'maintenance-report.pdf','Machine A / Maintenance Record',[('Equipment','SYNTHETIC equipment: Machine A, conveyor drive CV-204. Review date 2026-10-01. No real equipment measurements are represented.'),('Maintenance observation','The fictional technician observed visible belt wear during a routine inspection. Belt replacement was recommended at the next scheduled stop. Bearing condition was not documented. This maintenance record alone does not prove the cause of a later stoppage.'),('Recommended verification','Qualified personnel should verify belt tension, inspect bearings after safe isolation, check the sensor calibration, and compare recorded conditions with operating specifications.')])
    (manufacturing/'technician-statement.txt').write_text('SYNTHETIC DEMONSTRATION DATA\nTechnician statement about Machine A CV-204. On 2026-10-04 around 11:25 I heard a grinding noise near the drive assembly. The conveyor stopped around 11:30. I did not inspect the internal bearings or measure the belt tension. A worn belt and a bearing issue are possibilities to investigate, not confirmed diagnoses. Please check the sensor log and maintenance report with qualified personnel.\n',encoding='utf-8')
    values=[(1.2,42),(1.3,43),(1.4,44),(1.5,45),(2.2,47),(2.9,49),(3.8,53),(5.2,57),(6.6,63),(8.1,69),(8.9,74),(0,73)]
    csv='timestamp,machine,vibration_mm_s,temperature_c,status\n'
    for i,(v,t) in enumerate(values):csv+=f'2026-10-04T11:{19+i:02}:00+05:30,Machine A,{v},{t},{"Stopped" if i==11 else "Running"}\n'
    (manufacturing/'sensor-trends.csv').write_text(csv,encoding='utf-8')
    print('Created two synthetic cases: two PDFs, two statements, and two CSV logs.')
if __name__=='__main__':generate()
