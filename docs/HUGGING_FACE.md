# Hugging Face integration

Backend connections added:

| Model | Trigger | Deployment |
| --- | --- | --- |
| BAAI/bge-m3 | Index new files and search compatible indexed passages | HF Inference |
| openai/whisper-large-v3-turbo | Uploaded MP3/WAV | HF Inference |
| Qwen/Qwen3-VL-8B-Instruct | Uploaded PNG/JPG/WEBP | Configurable conversational provider; verify multimodal support |
| BAAI/bge-reranker-v2-m3 | Rerank retrieved passages, if endpoint configured | Private Text Embeddings Inference deployment with `/rerank` |

Gemini continues reasoning, video analysis and scanned-PDF OCR. HF image/audio failures fall back to Gemini with recorded limitations. Embedding failures preserve text search. Reranker failures retain retrieval ordering. Model output still requires source verification. Audio timestamps are not invented.

## Configuration

Put HF_TOKEN only in the backend environment, never a frontend variable or committed template. The token needs Inference Providers permission. Authentication alone does not prove inference access or available credits.

Install `services/api/requirements.txt` on both API and worker hosts. Set the model variables shown in `.env.example` on both. Run `python -m tests.check_huggingface` using the deployment environment, then enable `HF_ENABLED=true` only after successful inference and representative accuracy tests. API and worker must use identical embedding settings. Restart both after changes.

HF_ENABLED defaults to false. On 2026-10-08 the saved account returned HTTP 402 for BGE and reranker probes. This is not a successful live HF deployment. Resolve billing/credits or deploy your own inference infrastructure; no subscription or paid endpoint was provisioned automatically.

Existing Gemini vectors remain tagged or treated as legacy Gemini vectors. They are never compared with BGE vectors. Existing files continue lexical search after switching until explicitly reprocessed through the existing retry flow. No original files or user evidence are deleted by this integration.

For the optional reranker, deploy BAAI/bge-reranker-v2-m3 on a private compatible TEI server and put its HTTPS base URL in HF_RERANK_URL. Confirm a real `/rerank` response before enabling. This endpoint is not provisioned by the code.

PaddleOCR-VL, RT-DETR, SAM and forecasting are not connected. PaddleOCR currently has no shared hosted provider listed. Defect detection needs defined component/product classes, labelled examples, custom training and held-out expert validation. A generic detector cannot diagnose failed fuses. Qwen provider discovery alone does not guarantee support for image inputs; the smoke check must succeed.

## Verification

`python -m pytest tests -q` checks routing, embedding compatibility, extraction provenance, and fallback behaviour without sending private evidence externally. The opt-in live check uses synthetic inputs and prints only safe status messages. It is an access check, not an accuracy benchmark.

Latest verification: 38 backend tests passed. Synthetic live checks for BGE-M3, Whisper and Qwen each returned HTTP 402. None is claimed as working live.
