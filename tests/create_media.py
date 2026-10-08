"""Generate clearly synthetic integration fixtures, never presented as real-world evidence."""
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw
from services.worker.processors import binary
ROOT=Path('data/qa-media');ROOT.mkdir(parents=True,exist_ok=True)
im=Image.new('RGB',(1000,620),'#edf4f8');d=ImageDraw.Draw(im)
d.text((35,30),'SYNTHETIC QA - EVIDENCE.AI',fill='#163c57',font_size=34)
d.rectangle((180,150,820,520),outline='#426e8c',width=5)
d.text((220,230),'ORD-1042',fill='#163c57',font_size=48)
d.text((220,330),'TEST LABEL: PACKAGE CORNER BENT',fill='#163c57',font_size=26)
d.line((760,150,700,220,820,220),fill='#ae4747',width=9)
im.save(ROOT/'synthetic-package.png')
ffmpeg=binary('ffmpeg')
if not ffmpeg:raise SystemExit('FFmpeg not available.')
subprocess.run([ffmpeg,'-y','-loop','1','-i',str(ROOT/'synthetic-package.png'),'-t','4','-r','10','-vf','scale=640:398,format=yuv420p','-c:v','libx264',str(ROOT/'synthetic-package.mp4')],check=True,capture_output=True)
print('Synthetic image and four-second video created for live processing QA.')
