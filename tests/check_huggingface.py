"""Opt-in live smoke check: python -m tests.check_huggingface. Synthetic input only."""
import tempfile
import wave
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from services.worker import huggingface as hf


def main():
    load_dotenv()
    failures=[]
    with tempfile.TemporaryDirectory() as directory:
        audio=Path(directory)/'silence.wav'
        with wave.open(str(audio),'wb') as output:
            output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
            output.writeframes(b'\0\0'*16000)
        image=Path(directory)/'square.png'
        Image.new('RGB',(64,64),'red').save(image)
        checks={
            'BGE-M3':lambda: hf.embeddings(['Synthetic inspection record: belt wear.']),
            'Whisper':lambda: hf.transcribe(audio),
            'Qwen vision':lambda: hf.observe_image(image,'image/png'),
        }
        for name,call in checks.items():
            try:
                call(); print(name+': inference responded')
            except Exception as error:
                failures.append(name)
                print(name+': '+hf.safe_error(error))
    print('Silence and a square test provider access, not transcription/vision accuracy.')
    return 1 if failures else 0


if __name__=='__main__':
    raise SystemExit(main())
