# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a conversational AI system that integrates facial recognition with large language models. It maintains conversation history for each recognized face and generates contextual responses based on previous interactions.

## Key Architecture Components

### Core Application Files
- `app.py` - Main application using OpenAI GPT models
- `app_ASI.py` - Alternative version using ASI Mini API

Both files contain nearly identical `FaceManager` class implementations with the primary difference being the LLM API integration.

### FaceManager Class
The core component (`app.py:94`, `app_ASI.py:117`) handles:
- Face detection and recognition using InsightFace
- Conversation memory management with CSV storage
- Face summary generation and updates
- Training from image folders

### Data Storage
- `face_embeddings.pkl` - Facial recognition data
- `conversations.csv` - All conversation records
- `face_summaries.csv` - Auto-generated person summaries
- `training_faces/` - Directory structure for training images

## Common Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# OpenAI version
python app.py

# ASI Mini version
python app_ASI.py
```

### Environment Configuration
Create `.env` file with:
- `OPENAI_API_KEY=your_key` (for app.py)
- `ASI_API_KEY=your_key` (for app_ASI.py)

### Training Face Recognition
Place training images in: `training_faces/Person_Name/image1.jpg`

## Key Configuration Variables

- `embedding_threshold=0.2` - Face recognition similarity threshold
- `max_memories=5` - Maximum conversation memories per face
- `prompt` variable (`app.py:42`, `app_ASI.py:46`) - AI assistant personality

## Application Commands
- `/quit` - Exit application
- `/rename` - Rename detected face
- `/faces` - Show all known faces
- `/summary` - Show face summaries
- `/fix` - Fix CSV encoding issues

## Dependencies
Core dependencies: numpy, opencv-python, insightface, python-dotenv, openai