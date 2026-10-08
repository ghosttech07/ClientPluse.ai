"""Sarvam batch transcription, preserving original-language evidence."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory


def transcript_items(result):
    entries=(result.get('diarized_transcript') or {}).get('entries') or []
    items=[{'content':e['transcript'],'timestamp':e.get('start_time_seconds'),
            'meta':{'speaker':e.get('speaker_id'),'end_seconds':e.get('end_time_seconds')}}
           for e in entries if str(e.get('transcript','')).strip()]
    if not items:
        times=result.get('timestamps') or {}
        for index,text in enumerate(times.get('chunks') or []):
            starts=times.get('start_time_seconds') or [];ends=times.get('end_time_seconds') or []
            if str(text).strip():items.append({'content':text,'timestamp':starts[index] if index<len(starts) else None,
                                              'meta':{'end_seconds':ends[index] if index<len(ends) else None}})
    if not items and str(result.get('transcript','')).strip():items=[{'content':result['transcript']}]
    if not items:raise ValueError('Sarvam returned no readable speech. Check the recording and language setting.')
    return items


def transcribe(path):
    key=os.getenv('SARVAM_API_KEY')
    if not key:raise ValueError('Add SARVAM_API_KEY to the backend environment for Sarvam audio transcription.')
    from sarvamai import SarvamAI
    model=os.getenv('SARVAM_MODEL','saaras:v4')
    if model not in ('saaras:v3','saaras:v4'):raise ValueError('SARVAM_MODEL must be saaras:v3 or saaras:v4.')
    client=SarvamAI(api_subscription_key=key,timeout=90)
    job=client.speech_to_text_job.create_job(model=model,mode='transcribe',language_code=os.getenv('SARVAM_LANGUAGE','unknown'),with_diarization=True,with_timestamps=True)
    job.upload_files(file_paths=[str(Path(path).resolve())]);job.start()
    # Bound processing within the queue's 15-minute lease.
    job.wait_until_complete(poll_interval=3,timeout=480)
    outcomes=job.get_file_results()
    if outcomes.get('failed') or not outcomes.get('successful'):
        raise ValueError('Sarvam could not transcribe this recording. Check audio format, language, provider quota and retry.')
    with TemporaryDirectory(prefix='clientpulse-sarvam-') as output:
        if not job.download_outputs(output_dir=output):raise ValueError('Sarvam transcript download failed. Please retry.')
        results=list(Path(output).glob('*.json'))
        if len(results)!=1:raise ValueError('Sarvam returned an unexpected number of transcript files.')
        result=json.loads(results[0].read_text(encoding='utf-8'))
    return transcript_items(result),{'extraction':'Sarvam '+model,'language':result.get('language_code'),
            'limitations':['Speaker labels are not verified customer or employee identities. Timestamps are chunk-level.']},False
