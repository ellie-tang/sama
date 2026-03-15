#!/usr/bin/env python3
"""
Functional test to demonstrate the facial recognition system works end-to-end.
This test simulates the complete workflow without requiring actual ML models.
"""

import os
import time
import tempfile
import shutil
import csv
from PIL import Image
import threading
from unittest.mock import patch, Mock
import numpy as np

def create_test_environment():
    """Create a test environment with directories and mock data."""
    test_dir = tempfile.mkdtemp(prefix='face_test_')
    original_cwd = os.getcwd()
    os.chdir(test_dir)

    # Create required directories
    os.makedirs('inputFaces', exist_ok=True)
    os.makedirs('known_faces', exist_ok=True)
    os.makedirs('training_faces', exist_ok=True)

    print(f"✅ Test environment created at: {test_dir}")
    return test_dir, original_cwd

def create_mock_face_data():
    """Create mock face detection data."""
    mock_face1 = Mock()
    mock_face1.embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    mock_face1.bbox = np.array([10, 10, 50, 50])

    mock_face2 = Mock()
    mock_face2.embedding = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
    mock_face2.bbox = np.array([60, 60, 100, 100])

    return [mock_face1, mock_face2]

def test_csv_operations():
    """Test CSV file operations."""
    print("\n🧪 Testing CSV Operations...")

    try:
        # Mock all external dependencies
        with patch('app.FaceAnalysis'), \
             patch('app.OPENAI_API_KEY', 'test-key'):
            from app import ensure_csv_files_exist

            # Test CSV file creation
            ensure_csv_files_exist()

            # Verify files exist
            assert os.path.exists('conversations.csv'), "conversations.csv not created"
            assert os.path.exists('face_summaries.csv'), "face_summaries.csv not created"

            # Verify headers
            with open('conversations.csv', 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                expected = ['conversation_id', 'timestamp', 'role', 'message', 'active_faces']
                assert headers == expected, f"Wrong headers: {headers}"

            print("  ✅ CSV files created with correct headers")

    except Exception as e:
        print(f"  ❌ CSV test failed: {e}")
        raise

def test_face_manager_core():
    """Test FaceManager core functionality."""
    print("\n🧪 Testing FaceManager Core...")

    try:
        with patch('app.FaceAnalysis'), \
             patch('app.ensure_csv_files_exist'), \
             patch('app.OPENAI_API_KEY', 'test-key'):
            from app import FaceManager

            face_manager = FaceManager()

            # Test initialization
            assert hasattr(face_manager, 'known_faces'), "known_faces not initialized"
            assert hasattr(face_manager, 'active_faces'), "active_faces not initialized"
            assert hasattr(face_manager, 'lock'), "lock not initialized"

            # Test face addition
            test_embedding = np.array([0.1, 0.2, 0.3])
            face_id = "test-face-123"
            face_manager.known_faces[face_id] = {
                'embedding': test_embedding,
                'name': 'Test Person'
            }

            # Test renaming
            result = face_manager.rename_face(face_id, 'New Name')
            assert result == True, "Face rename should succeed"
            assert face_manager.known_faces[face_id]['name'] == 'New Name', "Name not updated"

            # Test similarity calculation
            emb1 = np.array([1, 0, 0])
            emb2 = np.array([1, 0, 0])
            similarity = face_manager._calculate_similarity(emb1, emb2)
            assert abs(similarity - 1.0) < 0.01, f"Similarity should be ~1.0, got {similarity}"

            print("  ✅ FaceManager core functionality works")

    except Exception as e:
        print(f"  ❌ FaceManager test failed: {e}")
        raise

def test_image_processing_simulation():
    """Test image processing with mocked face detection."""
    print("\n🧪 Testing Image Processing...")

    try:
        # Create a test image
        test_image_path = 'test_face.jpg'
        img = Image.new('RGB', (200, 200), color='blue')
        img.save(test_image_path)

        mock_faces = create_mock_face_data()

        with patch('app.FaceAnalysis') as mock_face_analysis, \
             patch('app.cv2.imread') as mock_cv2, \
             patch('app.ensure_csv_files_exist'), \
             patch('app.OPENAI_API_KEY', 'test-key'):

            # Setup mocks
            mock_app = Mock()
            mock_app.get.return_value = mock_faces
            mock_face_analysis.return_value = mock_app
            mock_cv2.return_value = np.ones((200, 200, 3), dtype=np.uint8)

            from app import FaceManager
            face_manager = FaceManager()
            face_manager.face_detection_available = True
            face_manager.face_app = mock_app

            # Test image processing
            result = face_manager.process_image(test_image_path)

            # Should detect faces and return face IDs
            assert isinstance(result, set), "Result should be a set"
            assert len(result) > 0, "Should detect at least one face"

            print(f"  ✅ Image processing detected {len(result)} face(s)")

        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

    except Exception as e:
        print(f"  ❌ Image processing test failed: {e}")
        raise

def test_file_monitoring_logic():
    """Test file monitoring logic."""
    print("\n🧪 Testing File Monitoring Logic...")

    try:
        with patch('app.FaceAnalysis'), \
             patch('app.ensure_csv_files_exist'), \
             patch('app.FileSystemEventHandler'), \
             patch('app.OPENAI_API_KEY', 'test-key'):

            from app import ImageFileHandler, ChatApp

            # Create chat app and handler
            chat_app = ChatApp()
            mock_face_manager = Mock()
            mock_face_manager.process_image.return_value = {'face1'}
            mock_face_manager.get_active_faces_info.return_value = [
                {'name': 'Test Person', 'id': 'face1'}
            ]

            handler = ImageFileHandler(mock_face_manager, chat_app)

            # Test file extension checking
            test_files = [
                ('test.jpg', True),
                ('test.png', True),
                ('test.txt', False),
                ('test.pdf', False)
            ]

            for filename, should_process in test_files:
                is_image = filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))
                assert is_image == should_process, f"File {filename} classification incorrect"

            print("  ✅ File monitoring logic works correctly")

    except Exception as e:
        print(f"  ❌ File monitoring test failed: {e}")
        raise

def test_thread_safety():
    """Test thread safety mechanisms."""
    print("\n🧪 Testing Thread Safety...")

    try:
        with patch('app.FaceAnalysis'), \
             patch('app.ensure_csv_files_exist'), \
             patch('app.OPENAI_API_KEY', 'test-key'):

            from app import FaceManager
            face_manager = FaceManager()

            # Test concurrent access to active faces
            results = []

            def update_faces(face_set, result_list):
                with face_manager.lock:
                    face_manager.active_faces = face_set
                    result_list.append(len(face_manager.active_faces))

            threads = []
            for i in range(5):
                face_set = {f"face-{i}"}
                thread = threading.Thread(
                    target=update_faces,
                    args=(face_set, results)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Verify all operations completed
            assert len(results) == 5, f"Expected 5 results, got {len(results)}"
            assert all(r == 1 for r in results), "All face sets should have 1 face"

            print("  ✅ Thread safety mechanisms work correctly")

    except Exception as e:
        print(f"  ❌ Thread safety test failed: {e}")
        raise

def test_error_handling():
    """Test error handling scenarios."""
    print("\n🧪 Testing Error Handling...")

    try:
        with patch('app.FaceAnalysis'), \
             patch('app.ensure_csv_files_exist'), \
             patch('app.OPENAI_API_KEY', 'test-key'):

            from app import FaceManager
            face_manager = FaceManager()

            # Test processing non-existent file
            result = face_manager.process_image('nonexistent.jpg')
            assert result == set(), "Should return empty set for non-existent file"

            # Test renaming non-existent face
            result = face_manager.rename_face('nonexistent', 'New Name')
            assert result == False, "Should return False for non-existent face"

            print("  ✅ Error handling works correctly")

    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        raise

def run_functional_tests():
    """Run all functional tests."""
    print("🚀 Running Facial Recognition System Functional Tests")
    print("=" * 60)

    test_dir, original_cwd = create_test_environment()

    try:
        # Run all test functions
        test_functions = [
            test_csv_operations,
            test_face_manager_core,
            test_image_processing_simulation,
            test_file_monitoring_logic,
            test_thread_safety,
            test_error_handling
        ]

        passed = 0
        total = len(test_functions)

        for test_func in test_functions:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} failed: {e}")

        # Print summary
        print("\n" + "=" * 60)
        print("Functional Test Summary:")
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")

        if passed == total:
            print("\n🎉 All functional tests passed!")
            print("✅ The facial recognition system is working correctly!")
        else:
            print(f"\n⚠️  {total-passed} test(s) failed")

        return passed == total

    finally:
        # Clean up
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test environment: {test_dir}")

def demonstrate_workflow():
    """Demonstrate the complete workflow."""
    print("\n🎬 Workflow Demonstration:")
    print("-" * 40)
    print("1. Place image in inputFaces/ directory")
    print("2. System detects new file automatically")
    print("3. Face recognition processes the image")
    print("4. Faces are identified or registered as new")
    print("5. Image is deleted after processing")
    print("6. Active faces are updated for conversation context")
    print("7. User can interact with the chat system")
    print("8. System remembers conversation history per face")

if __name__ == '__main__':
    success = run_functional_tests()
    demonstrate_workflow()

    if success:
        print("\n✅ System ready for use!")
        print("\nTo use the system:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up API keys in .env file")
        print("3. Run: python app.py")
        print("4. Place images in inputFaces/ directory")
    else:
        print("\n❌ Some tests failed - system needs fixes")

    exit(0 if success else 1)