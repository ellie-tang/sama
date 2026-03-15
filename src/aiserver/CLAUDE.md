# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the LLM Facial Memory System - a conversational AI that integrates facial recognition with large language models. The system monitors a directory for images, performs face recognition, maintains conversation history for each recognized face, and generates contextual responses based on previous interactions.

## Architecture

### Core Components

**FaceManager Class** (`app.py:98`, `app_ASI.py:117`)
- Handles face detection and recognition using InsightFace
- Manages face embeddings and similarity matching (`embedding_threshold=0.2`)
- Maintains conversation memory with CSV storage
- Generates and updates face summaries automatically
- Supports training from organized image directories

**ImageFileHandler Class** (`app.py:612`)
- Extends `FileSystemEventHandler` for directory monitoring
- Processes new images automatically when added to `inputFaces/`
- Validates file security and prevents path traversal attacks
- Handles file cleanup after processing

**ChatApp Class** (`app.py:736`, `app_ASI.py:577`)
- Main application coordinator
- Manages OpenAI/ASI API integration
- Handles conversation flow and memory management
- Provides CLI interface with commands

### Data Storage

- `face_embeddings.pkl` - Face recognition embeddings and metadata
- `conversations.csv` - Complete conversation history with face associations
- `face_summaries.csv` - Auto-generated summaries for each recognized person
- `inputFaces/` - Directory monitored for new image processing
- `training_faces/Person_Name/` - Training images organized by person folders

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
```

### Running Applications
```bash
# OpenAI version (requires OPENAI_API_KEY)
python app.py

# ASI Mini version (requires ASI_API_KEY)
python app_ASI.py
```

### Testing
```bash
# Run comprehensive unit tests
python test_app.py

# Run minimal tests (no external dependencies)
python test_app_minimal.py

# Run functional tests
python functional_test.py
```

### Environment Configuration
Create `.env` file with:
- `OPENAI_API_KEY=your_key` (for app.py)
- `ASI_API_KEY=your_key` (for app_ASI.py)

## Application Usage

### CLI Commands
- `/quit` - Exit application
- `/rename` - Rename detected face
- `/faces` - Show all known faces
- `/summary` - Show face summaries for active faces
- `/fix` - Fix CSV encoding issues

### Image Processing Workflow
1. Place images in `inputFaces/` directory
2. System automatically detects and processes images
3. Face recognition runs on detected faces
4. Conversation context updated with recognized faces
5. Images preserved after processing

### Training Face Recognition
Create directory structure: `training_faces/Person_Name/image1.jpg`
System automatically processes training images on startup.

## Key Configuration

### FaceManager Settings
- `embedding_threshold=0.2` - Face similarity threshold for recognition
- `max_memories=5` - Maximum conversation memories retained per face

### LLM Integration
- `prompt` variable (`app.py:44`, `app_ASI.py:46`) - Assistant personality configuration
- Models: gpt-4o-mini (OpenAI) or asi1-mini (ASI)

## Dependencies

**Core Requirements:**
- numpy - Array operations for embeddings
- opencv-python - Image processing
- insightface - Face detection and recognition
- python-dotenv - Environment variable management
- openai - OpenAI API integration (app.py only)
- watchdog - Directory monitoring
- onnxruntime, pillow - Supporting libraries

## Testing Strategy

**Unit Tests** (`test_app.py`, `test_app_minimal.py`)
- Mock external dependencies (cv2, insightface, openai)
- Test core logic, thread safety, error handling
- 100% pass rate for isolated component testing

**Functional Tests** (`functional_test.py`)
- End-to-end system integration testing
- Requires full dependency installation

## Security Considerations

- Path validation prevents directory traversal attacks
- File permission checking before processing
- Thread-safe operations with proper locking
- Input validation for all file operations