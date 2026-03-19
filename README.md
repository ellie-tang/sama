# SAMA

SAMA is a smart-glasses AI assistant project for dementia support. The repository now contains four active workstreams:

- a Vuzix Blade 2 frontend for live HUD interaction
- a FastAPI image-processing server
- a face-memory backend for recognition and recall
- new audio-training and text-training subsystems for ASR improvement and speech normalization workflows

`Vuzix Blade 2` | `FastAPI` | `InsightFace` | `Whisper` | `Qwen3.5 9B`

## Overview

Dementia affects millions of individuals worldwide, often causing two major communication barriers: difficulty recognizing familiar faces and difficulty expressing speech clearly. SAMA explores how augmented reality glasses and adaptive AI can reduce that burden in daily life.

In this repository, the implemented stack is centered on:

- continuous image capture from AR glasses
- server-side face recognition and identity recall
- HUD display updates and optional text-to-speech prompts
- persistent face memory, conversation history, and summaries
- an audio self-training pipeline for disordered speech collection and Whisper retraining
- a text-training pipeline for prompt-based transcript correction experiments

The repo still ships the face-recognition path as the most directly integrated flow today, but it now also includes the first dedicated code for speech data collection, dataset growth, and model-training support.

## Latest Changes

Recent additions in this repo:

- `src/audio-training/` adds a Vuzix Blade 2 audio self-training subsystem with Android capture classes, a Python ingestion backend, Whisper ASR adapters, Qwen3.5 9B labeling logic, review-queue handling, and nightly CBA-Whisper retraining helpers.
- `src/audio-training/audio-training-plan-and-summary.txt` records the implementation plan, module map, and current status of the audio-training work.
- `src/text-training/` adds a text-training package for data preparation, prompt templating, tokenization, LoRA-oriented training/eval scripts, and example configuration.
- `tests/` is now the central test root for audio-training, text-training, backend webserver, and frontend app contract tests.

## Repository Layout

```text
sama/
├── src/
│   ├── Blade_2_Template_App/         # Android app for Vuzix Blade 2
│   │   ├── app/src/main/java/.../
│   │   │   ├── center_content_template_activity.java
│   │   │   ├── CameraCaptureService.java
│   │   │   ├── FaceRecognitionApiClient.java
│   │   │   └── FaceRecognitionBroadcastReceiver.java
│   │   └── client-server-api-spec.md
│   ├── audio-training/               # Audio self-training subsystem
│   │   ├── android/                  # Blade 2 microphone/camera collection path
│   │   ├── server/                   # FastAPI-style ingestion and training orchestration
│   │   ├── shared/                   # Shared contracts and prompts
│   │   ├── scripts/                  # Retraining / manifest helpers
│   │   └── audio-training-plan-and-summary.txt
│   └── aiserver/
│       ├── LLM_Facial_Memory_System/ # Face memory and conversation layer
│       │   ├── app.py
│       │   ├── training_faces/
│       │   ├── conversations.csv
│       │   └── face_summaries.csv
│       ├── webserver/                # FastAPI server for the glasses client
│       │   ├── main.py
│       │   ├── start_server.py
│       │   ├── api/endpoints.py
│       │   └── services/face_recognition_service.py
│       └── requirements.txt
│   └── text-training/                # Text normalization / LoRA training package
│       ├── text_training/
│       ├── configs/
│       └── scripts/
├── docs/
└── tests/
    ├── audio_training/
    ├── backend_webserver/
    ├── frontend_app/
    └── text_training/
```

## How It Works

### End-to-End Call Flow

1. `center_content_template_activity.java` launches on the Vuzix Blade 2 and starts `CameraCaptureService`.
2. `CameraCaptureService.java` captures a frame roughly every second, rotates it for Blade orientation, and converts it into in-memory JPEG bytes.
3. `FaceRecognitionApiClient.java` sends the frame to `POST /api/process-image` on the backend server.
4. `src/aiserver/webserver/api/endpoints.py` validates the upload, saves a temporary image, and forwards it to `FaceRecognitionService`.
5. `src/aiserver/webserver/services/face_recognition_service.py` initializes the legacy `FaceManager` from `LLM_Facial_Memory_System/app.py` and processes the image.
6. The face-memory layer compares embeddings against known faces, returns the active face info, and the web server formats a JSON response.
7. The Blade app receives the response, broadcasts the recognition result internally, updates the HUD banner, and optionally announces the recognized name with text-to-speech.

### Current Capabilities In This Repo

- real-time face recognition from smart glasses
- known-face memory backed by saved embeddings
- basic relationship labeling in server responses
- conversation and summary storage per recognized face
- HUD-first recognition feedback on Vuzix Blade 2
- optional TTS name announcements for recognized people
- audio conversation collection and labeling infrastructure for self-training
- dataset manifest generation and nightly retraining scaffolding for Whisper
- text-training utilities for transcript correction experiments with LoRA-style fine-tuning

## Preferred Setup

The simplest development setup is:

1. Run the Python backend on a laptop or desktop on the same network as the glasses.
2. Point the Blade app to that machine's local IP address.
3. Preload `training_faces/` with a few people you want the system to recognize.

## Backend Setup

### Prerequisites

- Python 3.x
- `pip`
- an `OPENAI_API_KEY` environment variable for the memory layer
- a machine with enough CPU/GPU support for InsightFace and `onnxruntime`

### Install

```bash
cd src/aiserver
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

Set your API key before starting the server:

```bash
export OPENAI_API_KEY=your_key_here
```

### Run

```bash
cd src/aiserver/webserver
python start_server.py
```

The default server address is `http://0.0.0.0:8000`, with the primary endpoint at `POST /api/process-image`.

## Blade 2 App Setup

### Prerequisites

- Android Studio
- a Vuzix Blade 2 device or compatible target environment
- the Blade device on the same network as the backend server

### Update the Server Address

The Android client is currently hard-coded to:

```java
private static final String SERVER_HOST = "192.168.1.201";
```

Before building, update:

- `src/Blade_2_Template_App/app/src/main/java/devkit/blade/vuzix/com/blade_template_app/FaceRecognitionApiClient.java`
- `src/Blade_2_Template_App/app/src/main/res/xml/network_security_config.xml`

Both files need the backend machine's actual LAN IP if you are using HTTP.

### Build

```bash
cd src/Blade_2_Template_App
./gradlew assembleDebug
```

Then install the generated APK from Android Studio or with your normal Vuzix deployment flow.

## Usage

### 1. Start the backend

```bash
cd src/aiserver/webserver
python start_server.py
```

### 2. Check health

```bash
curl http://localhost:8000/health
```

Expected response shape:

```json
{
  "status": "healthy",
  "face_recognition_available": true
}
```

### 3. Send an image manually

```bash
curl -X POST "http://localhost:8000/api/process-image" \
  -F "file=@/path/to/image.jpg"
```

Example response:

```json
{
  "success": true,
  "person_name": "John Doe",
  "relationship": "Friend",
  "confidence": 0.8,
  "faces_detected": 1,
  "message": "Image processed successfully"
}
```

### 4. Run the full glasses flow

1. Launch the Blade app.
2. Grant camera permission on first run.
3. The camera service starts capturing frames automatically.
4. Frames are posted to the FastAPI server.
5. The server returns the recognized name and relationship.
6. The HUD updates with the person prompt.
7. If enabled, the glasses announce the result through TTS.

## Training Known Faces

To preload people into the system, add labeled images under `src/aiserver/LLM_Facial_Memory_System/training_faces/` using one folder per person.

Example:

```text
training_faces/
├── Alice/
│   ├── alice_1.jpg
│   └── alice_2.jpg
└── Bob/
    ├── bob_1.jpg
    └── bob_2.jpg
```

The face-memory system uses these images to build and persist embeddings in `face_embeddings.pkl`.

## API Surface

The main endpoints exposed by the backend are:

- `GET /health`
- `POST /api/process-image`
- `GET /api/faces`
- `GET /api/system-status`

For more detail, see:

- `src/aiserver/CLIENT_API_SPECIFICATION.md`
- `src/Blade_2_Template_App/client-server-api-spec.md`

The new audio-training backend also exposes a separate API surface in `src/audio-training/server/router.py`, including:

- `POST /audio-training/ingest`
- `GET /audio-training/reviews`
- `POST /audio-training/reviews/{review_task_id}`
- `POST /audio-training/retrain`
- `GET /audio-training/health`

This router is implemented as a self-contained subsystem and is ready to be registered in the main FastAPI service or run as a dedicated process.

## Testing

Repository test coverage is now grouped under `tests/`:

- `tests/frontend_app/` validates Blade app source and manifest contracts
- `tests/backend_webserver/` validates the FastAPI webserver helpers, config, schemas, and service formatting behavior
- `tests/audio_training/` covers the new audio-training pipeline logic
- `tests/text_training/` covers the text-training package

Some tests are source-contract tests rather than runtime instrumentation tests. In this environment, `compileall` verification was completed, but running the full Python test suite still depends on local installation of `pytest`, `fastapi`, and `pydantic`.

## Development Notes

- uploaded images are saved temporarily by the web server and then deleted after processing
- the web server wraps the legacy face-memory app instead of reimplementing recognition logic
- relationship values are currently placeholder mappings in `face_recognition_service.py`
- `src/audio-training/` contains the new speech self-training code but is not yet wired into the existing Android manifest or the active `src/aiserver/webserver/main.py` app
- `src/text-training/` is currently a standalone training package and script set, not yet integrated into a deployed runtime path
- the face-recognition flow remains the most integrated end-to-end path in the repo today

## Research / Safety Note

SAMA should be treated as a research prototype, not a medical device. Any dementia-support workflow built on top of this code should include human oversight, privacy review, and explicit consent for image and conversation data handling.
