# Sarvam configuration

ClientPulse supports Sarvam for uploaded call transcription using the official Python SDK and Batch Speech-to-Text API. It preserves original-language transcript chunks, start/end timestamps and provider speaker labels. Speaker labels are not verified customer identities.

In the existing root `.env` (backend only):

```env
SPEECH_PROVIDER=sarvam
SARVAM_API_KEY=your_key_here
SARVAM_MODEL=saaras:v4
SARVAM_LANGUAGE=unknown
```

Restart API and worker after saving. Install requirements with `uv pip install --python .venv/Scripts/python.exe -r services/api/requirements.txt`. Never put this key in `NEXT_PUBLIC_*` variables or commit it.

`unknown` enables language detection. A supported explicit language such as `hi-IN` or `en-IN` can be configured. Transcription uses source-language output rather than silently replacing evidence with English translation. Gemini reasons over that transcript. Batch results supply chunk timestamps, not word timestamps. Processing remains queued and provider delays/failures are visible in the upload library.

To use Deepgram instead, set `SPEECH_PROVIDER=deepgram` and configure `DEEPGRAM_API_KEY`. The application does not silently send recordings to a second provider after failure.

Official reference: https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/batch-api
