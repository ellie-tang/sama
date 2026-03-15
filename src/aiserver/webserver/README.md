# to start server:
source venv/bin/activate
cd webserver
python start_server.py
# Vuzix Blade II Face Recognition Web Server

A FastAPI-based web server that integrates with the existing LLM_Facial_Memory_System to provide REST API services for the Vuzix Blade II Glass. The server receives images from the glass every 0.5 seconds, performs face recognition, and returns the person's name and relationship information.

## Features

- **REST API**: FastAPI-based server with automatic OpenAPI documentation
- **Image Processing**: Accepts images via POST requests and saves them locally
- **Face Recognition**: Integrates with existing LLM_Facial_Memory_System
- **Real-time Processing**: Designed to handle images every 0.5 seconds from Vuzix Blade II
- **Comprehensive Error Handling**: Proper error responses and logging
- **Health Monitoring**: Health check and system status endpoints

## Project Structure

```
webserver/
├── api/                    # API endpoints
│   ├── __init__.py
│   └── endpoints.py       # Main API routes
├── models/                # Data models
│   ├── __init__.py
│   └── schemas.py         # Pydantic models
├── services/              # Business logic
│   ├── __init__.py
│   └── face_recognition_service.py  # Face recognition integration
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   └── error_handlers.py  # Error handling
├── images/                # Image storage
│   └── uploads/           # Uploaded images from Vuzix Blade II
├── main.py                # FastAPI application
├── start_server.py        # Server startup script
├── test_server.py         # Test suite
├── .env.example           # Environment configuration template
└── README.md              # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_webserver.txt
   ```

2. **Install Face Recognition System Dependencies**:
   ```bash
   cd LLM_Facial_Memory_System
   pip install -r requirements.txt
   ```

3. **Configuration**:
   ```bash
   cd webserver
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Edit the `.env` file with your settings:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes

# Face Recognition Settings
FACE_RECOGNITION_TIMEOUT=30.0

# Logging
LOG_LEVEL=INFO

# OpenAI API Key (for the face recognition system)
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Server

### Option 1: Using the start script
```bash
cd webserver
python start_server.py
```

### Option 2: Direct execution
```bash
cd webserver
python main.py
```

### Option 3: Using uvicorn directly
```bash
cd webserver
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Main Endpoint for Vuzix Blade II

**POST `/api/process-image`**
- Receives image from Vuzix Blade II Glass
- Performs face recognition
- Returns person name and relationship

**Request**:
```bash
curl -X POST "http://localhost:8000/api/process-image" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@image.jpg"
```

**Response**:
```json
{
  "success": true,
  "person_name": "John Doe",
  "relationship": "Friend",
  "confidence": 0.85,
  "faces_detected": 1,
  "message": "Image processed successfully",
  "timestamp": "2023-12-07T10:30:45.123456"
}
```

### Health and Management Endpoints

**GET `/health`** - Health check
**GET `/api/system-status`** - Detailed system status
**GET `/api/faces`** - List known faces

## Testing

Run the test suite to verify the server is working:

```bash
cd webserver
python test_server.py
```

The test will:
- Check health endpoints
- Test image processing with a sample image
- Verify system status
- List known faces

## Vuzix Blade II Integration

The server is designed to work with Vuzix Blade II Glass sending images every 0.5 seconds:

1. **Vuzix Blade II** captures camera input
2. **Glass** sends image via POST to `/api/process-image`
3. **Server** saves image to `webserver/images/uploads/`
4. **Server** calls existing face recognition system
5. **Server** returns JSON response with person name and relationship
6. **Glass** receives and displays the information

### Expected Client Implementation (Vuzix Blade II)

```python
import requests
import time

def send_image_to_server(image_data, server_url):
    """Send image to the web server for processing"""
    try:
        files = {'file': ('camera_image.jpg', image_data, 'image/jpeg')}
        response = requests.post(
            f"{server_url}/api/process-image",
            files=files,
            timeout=5.0
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('person_name'), result.get('relationship')
        else:
            print(f"Server error: {response.status_code}")
            return None, None

    except Exception as e:
        print(f"Error sending image: {e}")
        return None, None

# Main loop for Vuzix Blade II
while True:
    # Capture image from camera
    image_data = capture_camera_image()

    # Send to server
    person_name, relationship = send_image_to_server(image_data, "http://server:8000")

    # Display results on glass
    if person_name:
        display_on_glass(f"{person_name} - {relationship}")

    # Wait 0.5 seconds before next capture
    time.sleep(0.5)
```

## Performance Considerations

- **Async Processing**: Uses FastAPI's async capabilities for concurrent request handling
- **Background Tasks**: Automatic cleanup of old uploaded images
- **Thread Safety**: Safe integration with the existing face recognition system
- **Error Recovery**: Comprehensive error handling for production use

## Monitoring and Logging

- Structured logging with configurable levels
- Health check endpoint for monitoring systems
- System status endpoint with detailed information
- Request/response logging for debugging

## Security Notes

- File validation to prevent malicious uploads
- Path traversal protection
- Configurable file size limits
- CORS configuration (configure for production use)

## Troubleshooting

1. **Server won't start**: Check dependencies and .env configuration
2. **Face recognition fails**: Verify LLM_Facial_Memory_System is properly set up
3. **Image upload fails**: Check file size limits and format support
4. **Performance issues**: Monitor logs and consider increasing timeouts

## API Documentation

When the server is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
