"""Generate labelled synthetic input files. No stored AI results or seeded risk scores."""
import json
import subprocess
from pathlib import Path
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]/'fixtures'/'clientpulse'
CUSTOMERS=['Acme Retail','Northstar Analytics','Willow Logistics','Beacon Software','Lumen Design','Cedar Networks','Harbor Commerce','Atlas Systems','Spruce Media','Orchid Labs','Silverline Digital','Pinecrest Studio']


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    clients=[{'name':name,'email':f'customer{i}@clientpulse.example','account_ref':f'SYN-{i:03}','synthetic':True} for i,name in enumerate(CUSTOMERS)]
    manifest={'label':'SYNTHETIC DEMONSTRATION DATA — fictional customers and communications','customers':clients,'files':[]}
    def record(name,customer,date,channel):manifest['files'].append({'name':name,'customer':customer,'communication_at':date+'T10:00:00+00:00','channel':channel})
    def text(i,stage=0):
        if i==0:
            return ['Customer Acme Retail: shipment ORD-1042 has not arrived. It was due yesterday. Please investigate.','Customer Acme Retail: following up on ORD-1042. The shipment still has not arrived. This is the same unresolved delivery problem.','Customer Acme Retail: ORD-1042 still has not arrived. I will cancel our account if this delivery issue is not resolved. Please escalate.'][stage%3]
        if i in (1,2):return f'Customer {CUSTOMERS[i]}: following up on invoice INV-{100+i}. We were charged twice and the billing issue is still unresolved. Please refund the duplicate charge.'
        if i==3:return 'Customer Beacon Software: ticket TECH-103 is now fixed. We tested the login and confirm it works. This issue is resolved.'
        if i==4:return 'Customer Lumen Design: technical issue TECH-104 remains unresolved. I want to cancel our subscription.'
        if i==5:return 'Customer Cedar Networks: device DEF-105 arrived damaged. Please arrange a replacement. Employee support: we will investigate, but no completion date is confirmed.'
        if i in (10,11):return f'Customer {CUSTOMERS[i]}: thank you for the update. No concerns were reported in this communication.'
        return f'Customer {CUSTOMERS[i]}: support ticket SUP-{100+i} remains open. We have followed up and need a response.'
    for n in range(20):
        i=n%10;name=f'ticket-{n+1:02}.txt';date=f'2026-10-{3+n%5:02}'
        (ROOT/name).write_text('SYNTHETIC SUPPORT TICKET\n'+text(i,n%3),encoding='utf-8');record(name,CUSTOMERS[i],date,'Ticket')
    for i in range(12):
        email=EmailMessage();email['From']=clients[i]['email'];email['To']='support@clientpulse.example';email['Subject']='[SYNTHETIC] '+('ORD-1042 delivery follow-up' if i==0 else 'Customer account update');email['Date']='Mon, 05 Oct 2026 10:00:00 +0000';email.set_content('SYNTHETIC FICTIONAL EMAIL\n'+text(i,1));name=f'email-{i+1:02}.eml';(ROOT/name).write_bytes(email.as_bytes());record(name,CUSTOMERS[i],'2026-10-05','Email')
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    except OSError:font=ImageFont.load_default()
    for i in range(8):
        image=Image.new('RGB',(1000,440),'#f5f6fa');draw=ImageDraw.Draw(image);draw.text((30,25),'SYNTHETIC CHAT — '+CUSTOMERS[i],fill='#202738',font=font);draw.rounded_rectangle((25,100,970,395),radius=16,fill='white',outline='#dfe3ed')
        import textwrap
        content=text(i,2);draw.multiline_text((50,125),'Customer • 07 Oct 2026, 10:00 UTC\n\n'+'\n'.join(textwrap.wrap(content,75)),fill='#202738',font=font,spacing=12)
        name=f'chat-{i+1:02}.png';image.save(ROOT/name);record(name,CUSTOMERS[i],'2026-10-07','Screenshot')
    for i in range(5):
        name=f'account-note-{i+1:02}.pdf';pdf=canvas.Canvas(str(ROOT/name),pagesize=A4);pdf.setTitle('Synthetic customer account note');pdf.setFont('Helvetica-Bold',18);pdf.drawString(45,795,'SYNTHETIC CUSTOMER ACCOUNT NOTE');pdf.setFont('Helvetica',12);pdf.drawString(45,755,CUSTOMERS[i]);pdf.drawString(45,735,'Communication date: 2026-10-06')
        import textwrap
        for line,content in enumerate(textwrap.wrap(text(i,1),78)):pdf.drawString(45,690-line*20,content)
        pdf.save();record(name,CUSTOMERS[i],'2026-10-06','Document')
    # Windows local speech synthesis produces actual spoken, labelled fixtures.
    audio_specs=[{'path':str(ROOT/f'call-{i+1:02}.wav'),'text':'This is a synthetic fictional customer call. '+text(i,0)} for i in range(5)]
    specs=ROOT/'audio-generation.json';specs.write_text(json.dumps(audio_specs),encoding='utf-8')
    ps="Add-Type -AssemblyName System.Speech; $specs=Get-Content -LiteralPath '"+str(specs).replace("'","''")+"' -Raw | ConvertFrom-Json; foreach($item in $specs){$voice=New-Object System.Speech.Synthesis.SpeechSynthesizer;$voice.SetOutputToWaveFile($item.path);$voice.Speak($item.text);$voice.Dispose()}"
    result=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,timeout=120)
    for i in range(5):
        name=f'call-{i+1:02}.wav'
        if (ROOT/name).exists():record(name,CUSTOMERS[i],'2026-10-03','Audio')
        (ROOT/f'call-{i+1:02}-transcript.txt').write_text(audio_specs[i]['text'],encoding='utf-8')
    specs.unlink(missing_ok=True)
    manifest['audio_generation']='Local Windows text-to-speech' if result.returncode==0 else 'Audio generation failed; labelled transcript fixtures remain'
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (ROOT/'README.md').write_text('All records in this directory are fictional and labelled SYNTHETIC. No analysis results, risk scores or complaints are seeded. Upload these files to exercise the real pipeline. Acme: call-01.wav on Oct 3, email-01.eml on Oct 5, chat-01.png on Oct 7 share ORD-1042. Manifest supplies exact account assignments and timestamps. Windows speech is artificial, not a real customer recording. Two neutral accounts have insufficient complaint evidence.\n',encoding='utf-8')
    print('Generated synthetic input fixtures:',len(manifest['files']))
    print('Audio fixtures:',sum(f['channel']=='Audio' for f in manifest['files']))


if __name__=='__main__':main()
