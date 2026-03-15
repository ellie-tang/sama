#!/usr/bin/env python3
"""
Test script for the Vuzix Blade II Face Recognition Web Server
"""

import os
import sys
import requests
import time
from pathlib import Path
from PIL import Image
import io

def create_test_image():
    """Create a simple test image for testing"""
    # Create a simple RGB image
    img = Image.new('RGB', (640, 480), color='blue')

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return img_bytes


def test_health_endpoint(base_url):
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['status']}")
            print(f"  Face recognition available: {data['face_recognition_available']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


def test_system_status(base_url):
    """Test the system status endpoint"""
    print("Testing system status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/system-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ System status check passed")
            print(f"  Face recognition available: {data['face_recognition_available']}")
            print(f"  Upload directory: {data['upload_directory']}")
            return True
        else:
            print(f"✗ System status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ System status error: {e}")
        return False


def test_image_processing(base_url):
    """Test the image processing endpoint"""
    print("Testing image processing endpoint...")
    try:
        # Create test image
        test_image = create_test_image()

        # Send POST request
        files = {'file': ('test_image.jpg', test_image, 'image/jpeg')}
        response = requests.post(f"{base_url}/api/process-image", files=files)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Image processing passed")
            print(f"  Success: {data['success']}")
            print(f"  Faces detected: {data['faces_detected']}")
            print(f"  Person name: {data.get('person_name', 'None')}")
            print(f"  Relationship: {data.get('relationship', 'None')}")
            print(f"  Message: {data['message']}")
            return True
        else:
            print(f"✗ Image processing failed: {response.status_code}")
            if response.text:
                print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Image processing error: {e}")
        return False


def test_known_faces(base_url):
    """Test the known faces endpoint"""
    print("Testing known faces endpoint...")
    try:
        response = requests.get(f"{base_url}/api/faces")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Known faces check passed")
            print(f"  Total faces: {data['total_count']}")
            if data['faces']:
                print("  Sample faces:")
                for face in data['faces'][:3]:  # Show first 3
                    print(f"    - {face['name']} (ID: {face['face_id'][:8]}...)")
            return True
        else:
            print(f"✗ Known faces check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Known faces error: {e}")
        return False


def main():
    """Main test function"""
    print("Vuzix Blade II Face Recognition Web Server - Test Suite")
    print("=" * 60)

    # Server configuration
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8000"))
    base_url = f"http://{host}:{port}"

    print(f"Testing server at: {base_url}")
    print()

    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)

    # Run tests
    tests = [
        ("Health Check", lambda: test_health_endpoint(base_url)),
        ("System Status", lambda: test_system_status(base_url)),
        ("Image Processing", lambda: test_image_processing(base_url)),
        ("Known Faces", lambda: test_known_faces(base_url)),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        print()

    # Summary
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Server is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the server configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())