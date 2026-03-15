# Face Recognition Web Server - Client API Specification

## Overview

This document provides complete specifications for client applications to interact with the Face Recognition Web Server. This API is designed for devices like Vuzix Blade II Glass to send images and receive face recognition results.

**Base URL**: `http://<server-host>:<server-port>`
**Default Server**: `http://localhost:8000`
**API Version**: 1.0.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Client Implementation Guide](#client-implementation-guide)
7. [Best Practices](#best-practices)

---

## Quick Start

### Minimum Working Example (Python)

```python
import requests

# Server configuration
SERVER_URL = "http://localhost:8000"

# Send an image for face recognition
with open("image.jpg", "rb") as image_file:
    files = {"file": ("image.jpg", image_file, "image/jpeg")}
    response = requests.post(
        f"{SERVER_URL}/api/process-image",
        files=files,
        timeout=10.0
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Person: {result.get('person_name')}")
        print(f"Relationship: {result.get('relationship')}")
        print(f"Faces detected: {result.get('faces_detected')}")
    else:
        print(f"Error: {response.status_code}")
```

---

## Authentication

**Current Version**: No authentication required
**Future Versions**: May include API key or token-based authentication

---

## API Endpoints

### 1. Process Image (Main Endpoint)

**Purpose**: Send an image for face recognition processing

**Endpoint**: `POST /api/process-image`

**Content-Type**: `multipart/form-data`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Image file (JPG, JPEG, PNG, BMP, TIFF, WEBP) |

#### File Constraints

- **Maximum file size**: 10 MB (10,485,760 bytes)
- **Allowed formats**: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`
- **Recommended format**: JPEG for optimal balance of quality and size
- **Image dimensions**: No specific requirements, but reasonable resolutions (640x480 to 1920x1080) work best

#### Request Example (cURL)

```bash
curl -X POST "http://localhost:8000/api/process-image" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg" \
  -w "\nHTTP Status: %{http_code}\n"
```

#### Request Example (Python - requests)

```python
import requests

url = "http://localhost:8000/api/process-image"

# From file path
with open("image.jpg", "rb") as f:
    files = {"file": ("image.jpg", f, "image/jpeg")}
    response = requests.post(url, files=files, timeout=10.0)

# From bytes in memory
image_bytes = b"..."  # Your image data
files = {"file": ("camera.jpg", image_bytes, "image/jpeg")}
response = requests.post(url, files=files, timeout=10.0)
```

#### Response Model

**Success Response** (HTTP 200):

```json
{
  "success": true,
  "person_name": "John Doe",
  "relationship": "Friend",
  "confidence": 0.85,
  "faces_detected": 1,
  "message": "Image processed successfully",
  "timestamp": "2025-11-09T15:30:45.123456"
}
```

**No Face Detected** (HTTP 200):

```json
{
  "success": true,
  "person_name": null,
  "relationship": null,
  "confidence": null,
  "faces_detected": 0,
  "message": "No faces detected in the image",
  "timestamp": "2025-11-09T15:30:45.123456"
}
```

**Unknown Person Detected** (HTTP 200):

```json
{
  "success": true,
  "person_name": "Unknown Person",
  "relationship": "Unknown",
  "confidence": 0.0,
  "faces_detected": 1,
  "message": "Face detected but not recognized",
  "timestamp": "2025-11-09T15:30:45.123456"
}
```

#### Response Fields

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `success` | boolean | Yes | Whether processing was successful |
| `person_name` | string or null | Yes | Name of recognized person, null if none detected |
| `relationship` | string or null | Yes | Relationship info (e.g., "Friend", "Family") |
| `confidence` | float or null | Yes | Recognition confidence (0.0 to 1.0), null if no face |
| `faces_detected` | integer | Yes | Number of faces detected in image |
| `message` | string | Yes | Human-readable status message |
| `timestamp` | string (ISO 8601) | Yes | Server processing timestamp |

#### Error Responses

**400 Bad Request** - Invalid file format or size:
```json
{
  "detail": "Invalid image file"
}
```

**408 Request Timeout** - Processing took too long (>30 seconds):
```json
{
  "detail": "Face recognition processing timeout"
}
```

**413 Payload Too Large** - File exceeds 10MB:
```json
{
  "detail": "File too large"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "detail": "Internal server error during image processing"
}
```

---

### 2. Health Check

**Purpose**: Check if server is running and healthy

**Endpoint**: `GET /health`

**Authentication**: None required

#### Request Example

```bash
curl http://localhost:8000/health
```

#### Response (HTTP 200)

```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T15:30:45.123456",
  "face_recognition_available": true
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Server health status: "healthy" or "unhealthy" |
| `timestamp` | string | Current server timestamp (ISO 8601) |
| `face_recognition_available` | boolean | Whether face recognition system is available |

---

### 3. System Status

**Purpose**: Get detailed system configuration and status

**Endpoint**: `GET /api/system-status`

**Authentication**: None required

#### Request Example

```bash
curl http://localhost:8000/api/system-status
```

#### Response (HTTP 200)

```json
{
  "face_recognition_available": true,
  "upload_directory": "/path/to/webserver/images/uploads",
  "face_system_directory": "/path/to/LLM_Facial_Memory_System",
  "max_file_size": 10485760,
  "allowed_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"],
  "timestamp": "2025-11-09T15:30:45.123456"
}
```

---

### 4. List Known Faces

**Purpose**: Retrieve all known faces in the system

**Endpoint**: `GET /api/faces`

**Authentication**: None required

#### Request Example

```bash
curl http://localhost:8000/api/faces
```

#### Response (HTTP 200)

```json
{
  "success": true,
  "faces": [
    {
      "face_id": "abc123-def456-ghi789",
      "name": "John Doe",
      "last_seen": "2025-11-09T14:25:30.123456"
    },
    {
      "face_id": "xyz789-uvw456-rst123",
      "name": "Jane Smith",
      "last_seen": "2025-11-08T10:15:20.987654"
    }
  ],
  "total_count": 2,
  "timestamp": "2025-11-09T15:30:45.123456"
}
```

---

## Data Models

### FaceRecognitionResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| success | boolean | Yes | Processing success status |
| person_name | string \| null | Yes | Recognized person's name |
| relationship | string \| null | Yes | Person's relationship label |
| confidence | float \| null | Yes | Recognition confidence (0.0-1.0) |
| faces_detected | integer | Yes | Count of faces found |
| message | string | Yes | Status message |
| timestamp | datetime | Yes | ISO 8601 timestamp |

### HealthResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | Yes | Health status |
| timestamp | datetime | Yes | ISO 8601 timestamp |
| face_recognition_available | boolean | Yes | Face system availability |

### FaceInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| face_id | string | Yes | Unique face identifier |
| name | string | Yes | Person's name |
| last_seen | datetime \| null | No | Last detection timestamp |

### KnownFacesResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| success | boolean | Yes | Request success status |
| faces | Array<FaceInfo> | Yes | List of known faces |
| total_count | integer | Yes | Total face count |
| timestamp | datetime | Yes | ISO 8601 timestamp |

---

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid file format, missing file, invalid parameters |
| 408 | Request Timeout | Face recognition processing exceeded 30 seconds |
| 413 | Payload Too Large | File size exceeds 10MB limit |
| 422 | Unprocessable Entity | Validation error in request format |
| 500 | Internal Server Error | Server-side error during processing |
| 503 | Service Unavailable | Face recognition system unavailable |

### Error Response Format

All errors return JSON with a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Handling Errors in Client Code

```python
import requests

def send_image(image_data, server_url):
    try:
        files = {"file": ("image.jpg", image_data, "image/jpeg")}
        response = requests.post(
            f"{server_url}/api/process-image",
            files=files,
            timeout=10.0
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print("Invalid image file")
        elif response.status_code == 408:
            print("Processing timeout - try again")
        elif response.status_code == 413:
            print("Image file too large (max 10MB)")
        elif response.status_code == 500:
            print("Server error - contact administrator")
        else:
            print(f"Unexpected error: {response.status_code}")

        return None

    except requests.exceptions.Timeout:
        print("Network timeout - server not responding")
        return None
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

---

## Client Implementation Guide

### Complete Python Client Example

```python
import requests
import time
from typing import Optional, Dict, Any
from pathlib import Path

class FaceRecognitionClient:
    """Client for Face Recognition Web Server API"""

    def __init__(self, server_url: str = "http://localhost:8000", timeout: float = 10.0):
        """
        Initialize the client

        Args:
            server_url: Base URL of the server (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Optional[Dict[str, Any]]:
        """
        Check server health status

        Returns:
            Health status dict or None on error
        """
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None

    def process_image(self, image_data, filename: str = "image.jpg") -> Optional[Dict[str, Any]]:
        """
        Send an image for face recognition processing

        Args:
            image_data: Image data (bytes or file-like object)
            filename: Name to use for the uploaded file

        Returns:
            Recognition results dict or None on error
        """
        try:
            files = {"file": (filename, image_data, "image/jpeg")}
            response = requests.post(
                f"{self.server_url}/api/process-image",
                files=files,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Server error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("Request timeout - server took too long to respond")
            return None
        except requests.exceptions.ConnectionError:
            print("Connection error - cannot reach server")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def process_image_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process an image from a file path

        Args:
            file_path: Path to image file

        Returns:
            Recognition results dict or None on error
        """
        try:
            with open(file_path, "rb") as f:
                return self.process_image(f, Path(file_path).name)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def get_known_faces(self) -> Optional[Dict[str, Any]]:
        """
        Get list of all known faces

        Returns:
            Known faces dict or None on error
        """
        try:
            response = requests.get(
                f"{self.server_url}/api/faces",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get known faces: {e}")
            return None

    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """
        Get system status information

        Returns:
            System status dict or None on error
        """
        try:
            response = requests.get(
                f"{self.server_url}/api/system-status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get system status: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = FaceRecognitionClient(server_url="http://localhost:8000")

    # Check server health
    health = client.check_health()
    if health:
        print(f"Server status: {health['status']}")
        print(f"Face recognition available: {health['face_recognition_available']}")

    # Process an image from file
    result = client.process_image_file("test_image.jpg")
    if result:
        if result["success"]:
            if result["faces_detected"] > 0:
                print(f"Recognized: {result['person_name']}")
                print(f"Relationship: {result['relationship']}")
                print(f"Confidence: {result['confidence']:.2f}")
            else:
                print("No faces detected")
        else:
            print("Processing failed")

    # Get known faces
    faces = client.get_known_faces()
    if faces:
        print(f"Total known faces: {faces['total_count']}")
        for face in faces['faces']:
            print(f"  - {face['name']} (ID: {face['face_id']})")
```

### Continuous Monitoring Example (Vuzix Blade II)

```python
import cv2
import time
from face_recognition_client import FaceRecognitionClient

def capture_frame_from_camera() -> bytes:
    """Capture a frame from camera and return as JPEG bytes"""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if ret:
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buffer.tobytes()
    return None

def main():
    # Initialize client
    client = FaceRecognitionClient(
        server_url="http://192.168.1.100:8000",
        timeout=5.0
    )

    # Check server availability
    if not client.check_health():
        print("Server not available!")
        return

    print("Starting continuous face recognition...")

    # Continuous monitoring loop
    while True:
        try:
            # Capture image from camera
            image_data = capture_frame_from_camera()

            if image_data:
                # Send to server for processing
                result = client.process_image(image_data, "camera_frame.jpg")

                if result and result["success"]:
                    if result["faces_detected"] > 0:
                        person = result["person_name"] or "Unknown"
                        relationship = result["relationship"] or "Unknown"
                        print(f">>> {person} - {relationship}")
                        # Display on Vuzix Blade II screen here
                    else:
                        print("No face detected")
                else:
                    print("Processing error")

            # Wait 0.5 seconds before next capture
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1.0)  # Wait before retry

if __name__ == "__main__":
    main()
```

---

## Best Practices

### 1. Connection Management

- **Reuse connections**: Use a session object for multiple requests
- **Set appropriate timeouts**: 5-10 seconds for normal operations
- **Implement retry logic**: Retry failed requests with exponential backoff

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create a requests session with retry logic"""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
```

### 2. Image Optimization

- **Compress images**: Use JPEG with 80-85% quality
- **Resize large images**: Target 640x480 to 1280x720 for optimal performance
- **Limit file size**: Keep under 1-2 MB when possible

```python
from PIL import Image
import io

def optimize_image(image_data: bytes, max_size: tuple = (1280, 720)) -> bytes:
    """Optimize image for transmission"""
    img = Image.open(io.BytesIO(image_data))

    # Resize if too large
    img.thumbnail(max_size, Image.LANCZOS)

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Save as JPEG with 85% quality
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()
```

### 3. Error Handling

- **Always check HTTP status**: Don't assume 200 OK
- **Handle network errors**: Timeout, connection errors, etc.
- **Implement graceful degradation**: Continue operation even if server is temporarily unavailable

### 4. Rate Limiting

- **Respect server capacity**: Don't exceed 2 requests/second continuously
- **Implement backoff**: Slow down if server returns errors
- **Queue requests**: If capturing faster than processing, queue and throttle

```python
import time
from collections import deque

class RateLimitedClient:
    def __init__(self, client, max_rate: float = 2.0):
        self.client = client
        self.min_interval = 1.0 / max_rate
        self.last_request = 0

    def process_image(self, image_data, filename: str):
        # Enforce rate limit
        now = time.time()
        time_since_last = now - self.last_request
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)

        self.last_request = time.time()
        return self.client.process_image(image_data, filename)
```

### 5. Logging and Monitoring

- **Log all requests**: Track request/response for debugging
- **Monitor success rate**: Alert if success rate drops
- **Track latency**: Monitor processing time

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

def process_with_logging(client, image_data):
    start_time = time.time()
    result = client.process_image(image_data)
    elapsed = time.time() - start_time

    if result:
        logger.info(f"Processed in {elapsed:.2f}s: {result.get('faces_detected')} faces")
    else:
        logger.error(f"Processing failed after {elapsed:.2f}s")

    return result
```

---

## Testing Your Client

### 1. Test Server Connectivity

```python
client = FaceRecognitionClient("http://localhost:8000")
health = client.check_health()
assert health is not None
assert health["status"] == "healthy"
print("✓ Server connectivity OK")
```

### 2. Test Image Upload

```python
# Create a test image
from PIL import Image
import io

img = Image.new('RGB', (640, 480), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

result = client.process_image(img_bytes.getvalue(), "test.jpg")
assert result is not None
assert result["success"] == True
print("✓ Image upload OK")
```

### 3. Test Error Handling

```python
# Test with invalid data
result = client.process_image(b"not an image", "test.txt")
assert result is None  # Should handle error gracefully
print("✓ Error handling OK")
```

---

## API Changelog

### Version 1.0.0 (Current)
- Initial release
- Face recognition via `/api/process-image`
- Health check endpoint
- System status endpoint
- Known faces listing

---

## Support and Contact

For issues, questions, or feature requests:
- Check server logs for detailed error information
- Verify server is running: `curl http://server:8000/health`
- Review this documentation for proper usage
- Check network connectivity between client and server

---

## License

This API specification is provided as-is for integration with the Face Recognition Web Server.

