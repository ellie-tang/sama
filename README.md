# SAMA

SAMA is a smart-glasses AI assistant project for dementia support. The current repository combines a Vuzix Blade 2 frontend, a FastAPI image-processing server, and a face-memory backend that recognizes people, recalls stored identity context, and pushes live prompts back to the glasses HUD.

`Vuzix Blade 2` | `FastAPI` | `InsightFace` | `OpenAI-backed memory layer`

## Overview

Dementia affects millions of individuals worldwide, often causing two major communication barriers: difficulty recognizing familiar faces and difficulty expressing speech clearly. SAMA explores how augmented reality glasses and adaptive AI can reduce that burden in daily life.

In this repository, the implemented stack is centered on:

- continuous image capture from AR glasses
- server-side face recognition and identity recall
- HUD display updates and optional text-to-speech prompts
- persistent face memory, conversation history, and summaries

The broader project vision also includes speech normalization and continuously improving ASR. That speech pipeline is part of the project concept, but the code currently in this repo is primarily the face-recognition and prompt-delivery path.

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
├── docs/
└── tests/
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

## Development Notes

- uploaded images are saved temporarily by the web server and then deleted after processing
- the web server wraps the legacy face-memory app instead of reimplementing recognition logic
- relationship values are currently placeholder mappings in `face_recognition_service.py`
- the current repo is strongest on face recognition and recall; speech support is still a project direction rather than a finished implementation here

## Research / Safety Note

SAMA should be treated as a research prototype, not a medical device. Any dementia-support workflow built on top of this code should include human oversight, privacy review, and explicit consent for image and conversation data handling.
