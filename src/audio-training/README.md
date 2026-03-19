# Audio Training Subsystem

This directory contains a self-contained audio self-training subsystem for SAMA.

It is designed around the pipeline requested for Vuzix Blade 2:

- collect disordered speech audio from the Blade 2 microphone
- attach low-rate camera context from the Blade 2 camera pipeline
- transcribe utterances with Whisper
- merge multiple utterances into a conversation window
- use Qwen3.5 9B reasoning to decide whether the sample is labelable
- discard weak samples, queue low-confidence samples for review, and persist strong samples
- generate CBA-Whisper manifests and launch nightly retraining

## Layout

```text
audio-training/
├── android/        Blade 2-side Java services and client logic
├── server/         FastAPI router, ingestion services, and training orchestration
├── shared/         Shared constants, contracts, and prompt builders
├── scripts/        Entry points for nightly retraining and manifest backfill
└── tests/          Unit tests for the Python backend
```

## Backend model configuration

The Python backend defaults to safe local fallbacks so the logic is testable without heavyweight model runtimes.

- Whisper model name defaults to `whisper-large-v3`
- Qwen model name defaults to `qwen3.5-9b`
- Whisper backend defaults to `hint`
- Qwen backend defaults to `heuristic`

For a real deployment, set environment variables so the backend calls local model runners:

```bash
export AUDIO_TRAINING_ROOT=/absolute/path/to/src/audio-training
export AUDIO_TRAINING_WHISPER_BACKEND=cli
export AUDIO_TRAINING_WHISPER_CLI=whisper
export AUDIO_TRAINING_WHISPER_MODEL=whisper-large-v3
export AUDIO_TRAINING_QWEN_BACKEND=openai_compatible
export AUDIO_TRAINING_QWEN_API_BASE=http://127.0.0.1:8001/v1
export AUDIO_TRAINING_QWEN_API_KEY=dummy
export AUDIO_TRAINING_QWEN_MODEL=qwen3.5-9b
export AUDIO_TRAINING_CBA_COMMAND="/path/to/cba-whisper-train"
```

## Running the backend app

From the repository root:

```bash
cd src/audio-training
python3 -m uvicorn server.router:app --reload --port 8010
```

## Integration notes

All new code lives under this directory, per request. To fully activate it in the existing app/server, the following external integration points are still needed later:

- register the router from `server/router.py` in the existing FastAPI app, or run it as a dedicated service
- add `RECORD_AUDIO` and related runtime permission flow in the Android app manifest/activity
- either wire `android/BladeContextFrameCollector.java` to the existing camera service or add the package as a Gradle source set
