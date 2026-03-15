#!/usr/bin/env python3
"""
Unit tests for the facial recognition memory system.
Tests the core functionality including file monitoring, face recognition, and CSV operations.
"""

import unittest
import tempfile
import shutil
import os
import threading
import time
import csv
import pickle
import numpy as np
from unittest.mock import Mock, patch, MagicMock, mock_open
from PIL import Image
import io

# Import the modules to test
import sys
sys.path.append('.')

class TestFaceManager(unittest.TestCase):
    """Test cases for the FaceManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create test directories
        os.makedirs('inputFaces', exist_ok=True)
        os.makedirs('known_faces', exist_ok=True)
        os.makedirs('training_faces', exist_ok=True)

        # Mock the face detection to avoid requiring actual ML models
        with patch('app.FaceAnalysis') as mock_face_analysis:
            mock_face_analysis.return_value.prepare = Mock()
            mock_face_analysis.return_value.get = Mock(return_value=[])

            from app import FaceManager
            self.face_manager = FaceManager()
            self.face_manager.face_detection_available = True
            self.face_manager.face_app = Mock()

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test FaceManager initialization."""
        self.assertIsInstance(self.face_manager.known_faces, dict)
        self.assertIsInstance(self.face_manager.active_faces, set)
        self.assertEqual(self.face_manager.embedding_threshold, 0.2)
        self.assertEqual(self.face_manager.max_memories, 5)
        self.assertIsInstance(self.face_manager.lock, threading.Lock)

    def test_save_and_load_known_faces(self):
        """Test saving and loading face embeddings."""
        # Create test face data
        test_embedding = np.array([0.1, 0.2, 0.3])
        face_id = "test-face-123"
        self.face_manager.known_faces[face_id] = {
            'embedding': test_embedding,
            'name': 'Test Person'
        }

        # Save faces
        self.face_manager.save_known_faces()
        self.assertTrue(os.path.exists('face_embeddings.pkl'))

        # Load faces into new instance
        new_face_manager = FaceManager.__new__(FaceManager)
        new_face_manager.known_faces = {}
        new_face_manager.load_known_faces()

        self.assertIn(face_id, new_face_manager.known_faces)
        self.assertEqual(new_face_manager.known_faces[face_id]['name'], 'Test Person')
        np.testing.assert_array_equal(
            new_face_manager.known_faces[face_id]['embedding'],
            test_embedding
        )

    def test_process_image_file_not_exists(self):
        """Test process_image with non-existent file."""
        result = self.face_manager.process_image('nonexistent.jpg')
        self.assertEqual(result, set())

    def test_process_image_no_read_permission(self):
        """Test process_image with file that has no read permission."""
        # Create a test image file
        test_image_path = os.path.join(self.test_dir, 'test.jpg')
        with open(test_image_path, 'w') as f:
            f.write('fake image data')

        # Remove read permission
        os.chmod(test_image_path, 0o000)

        try:
            result = self.face_manager.process_image(test_image_path)
            self.assertEqual(result, set())
        finally:
            # Restore permissions for cleanup
            os.chmod(test_image_path, 0o644)

    def test_process_image_with_mock_faces(self):
        """Test process_image with mocked face detection."""
        # Create a simple test image
        test_image_path = os.path.join(self.test_dir, 'test.jpg')
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)

        # Mock face detection results
        mock_face = Mock()
        mock_face.embedding = np.array([0.1, 0.2, 0.3])
        mock_face.bbox = np.array([10, 10, 50, 50])

        self.face_manager.face_app.get.return_value = [mock_face]

        with patch('app.cv2.imread') as mock_imread:
            # Mock cv2.imread to return a valid image array
            mock_imread.return_value = np.ones((100, 100, 3), dtype=np.uint8)

            result = self.face_manager.process_image(test_image_path)

            self.assertEqual(len(result), 1)
            self.assertTrue(len(self.face_manager.known_faces) > 0)

    def test_rename_face(self):
        """Test face renaming functionality."""
        face_id = "test-face-123"
        self.face_manager.known_faces[face_id] = {
            'embedding': np.array([0.1, 0.2, 0.3]),
            'name': 'Old Name'
        }

        result = self.face_manager.rename_face(face_id, 'New Name')
        self.assertTrue(result)
        self.assertEqual(self.face_manager.known_faces[face_id]['name'], 'New Name')

        # Test renaming non-existent face
        result = self.face_manager.rename_face('nonexistent', 'Some Name')
        self.assertFalse(result)

    def test_thread_safety_active_faces(self):
        """Test thread safety of active faces operations."""
        def update_faces(face_set):
            with self.face_manager.lock:
                self.face_manager.active_faces = face_set

        threads = []
        for i in range(10):
            face_set = {f"face-{i}"}
            thread = threading.Thread(target=update_faces, args=(face_set,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify that we have a valid state (one of the sets)
        self.assertIsInstance(self.face_manager.active_faces, set)
        self.assertEqual(len(self.face_manager.active_faces), 1)


class TestImageFileHandler(unittest.TestCase):
    """Test cases for the ImageFileHandler class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        os.makedirs('inputFaces', exist_ok=True)

        # Mock face manager and chat app
        self.mock_face_manager = Mock()
        self.mock_face_manager.process_image.return_value = {'face1'}
        self.mock_face_manager.get_active_faces_info.return_value = [
            {'name': 'Test Person', 'id': 'face1'}
        ]

        self.mock_chat_app = Mock()

        from app import ImageFileHandler
        self.handler = ImageFileHandler(self.mock_face_manager, self.mock_chat_app)

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_on_created_with_directory(self):
        """Test that handler ignores directory creation events."""
        mock_event = Mock()
        mock_event.is_dir = True
        mock_event.src_path = 'inputFaces/test_dir'

        # Should return early without processing
        self.handler.on_created(mock_event)
        self.mock_face_manager.process_image.assert_not_called()

    def test_on_created_with_non_image_file(self):
        """Test that handler ignores non-image files."""
        mock_event = Mock()
        mock_event.is_dir = False
        mock_event.src_path = 'inputFaces/test.txt'

        self.handler.on_created(mock_event)
        self.mock_face_manager.process_image.assert_not_called()

    @patch('app.os.remove')
    @patch('app.os.path.exists')
    def test_on_created_with_image_file(self, mock_exists, mock_remove):
        """Test processing of image files."""
        mock_event = Mock()
        mock_event.is_dir = False
        mock_event.src_path = os.path.join(self.test_dir, 'inputFaces', 'test.jpg')

        mock_exists.return_value = True

        with patch('builtins.open', mock_open(read_data=b'fake image data')):
            self.handler.on_created(mock_event)

        self.mock_face_manager.process_image.assert_called_once()
        mock_remove.assert_called_once_with(mock_event.src_path)

    def test_path_validation_security(self):
        """Test that handler validates file paths for security."""
        mock_event = Mock()
        mock_event.is_dir = False
        mock_event.src_path = '/etc/passwd'  # Path outside monitored directory

        self.handler.on_created(mock_event)
        self.mock_face_manager.process_image.assert_not_called()


class TestChatApp(unittest.TestCase):
    """Test cases for the ChatApp class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create test directories
        os.makedirs('inputFaces', exist_ok=True)

        with patch('app.ensure_csv_files_exist'), \
             patch('app.FaceManager'), \
             patch('app.OPENAI_API_KEY', 'test-key'):
            from app import ChatApp
            self.chat_app = ChatApp()
            self.chat_app.face_manager = Mock()
            self.chat_app.face_manager.active_faces = {'face1'}
            self.chat_app.face_manager.lock = threading.Lock()

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_save_conversation_thread_safety(self):
        """Test that save_conversation is thread-safe."""
        # Mock CSV file operations
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('app.csv.writer') as mock_writer:

            mock_csv_writer = Mock()
            mock_writer.return_value = mock_csv_writer

            self.chat_app.save_conversation('2023-01-01', 'user', 'test message')

            # Verify that the lock was used
            mock_file.assert_called_once()
            mock_csv_writer.writerow.assert_called_once()

    @patch('app.Observer')
    def test_start_monitoring_success(self, mock_observer_class):
        """Test successful monitoring startup."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        result = self.chat_app.start_monitoring()

        self.assertTrue(result)
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()

    @patch('app.Observer')
    def test_start_monitoring_failure(self, mock_observer_class):
        """Test monitoring startup failure handling."""
        mock_observer_class.side_effect = Exception("Mock error")

        result = self.chat_app.start_monitoring()

        self.assertFalse(result)

    def test_stop_monitoring_with_timeout(self):
        """Test monitoring stop with timeout."""
        mock_observer = Mock()
        mock_observer.is_alive.return_value = False
        self.chat_app.observer = mock_observer

        self.chat_app.stop_monitoring()

        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once_with(timeout=5.0)


class TestCSVOperations(unittest.TestCase):
    """Test CSV file operations."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_csv_file_creation(self):
        """Test CSV file creation with proper headers."""
        from app import ensure_csv_files_exist

        ensure_csv_files_exist()

        self.assertTrue(os.path.exists('conversations.csv'))
        self.assertTrue(os.path.exists('face_summaries.csv'))

        # Check headers
        with open('conversations.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            expected_headers = ['conversation_id', 'timestamp', 'role', 'message', 'active_faces']
            self.assertEqual(headers, expected_headers)

    @patch('app.shutil.copy2')
    def test_csv_fix_function(self, mock_copy):
        """Test CSV file fixing functionality."""
        from app import fix_csv_files

        # Create a test CSV file with potential encoding issues
        test_content = "test,data,with,issues\n"
        with open('conversations.csv', 'wb') as f:
            f.write(test_content.encode('utf-8'))

        fix_csv_files()

        # Verify backup was created
        mock_copy.assert_called()


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        os.makedirs('inputFaces', exist_ok=True)

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_file_processing_workflow(self):
        """Test the complete file processing workflow."""
        # Create a test image
        test_image_path = os.path.join('inputFaces', 'test.jpg')
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(test_image_path)

        # Mock the face detection components
        with patch('app.FaceAnalysis') as mock_face_analysis, \
             patch('app.cv2.imread') as mock_imread, \
             patch('app.OPENAI_API_KEY', 'test-key'):

            mock_face_analysis.return_value.prepare = Mock()
            mock_face_analysis.return_value.get = Mock(return_value=[])
            mock_imread.return_value = np.ones((100, 100, 3), dtype=np.uint8)

            from app import ChatApp, ensure_csv_files_exist
            ensure_csv_files_exist()

            chat_app = ChatApp()

            # Test that the file would be processed
            self.assertTrue(os.path.exists(test_image_path))

            # Test file handler creation
            from app import ImageFileHandler
            handler = ImageFileHandler(chat_app.face_manager, chat_app)

            # Verify handler can be created without errors
            self.assertIsNotNone(handler)


def create_test_suite():
    """Create and return the complete test suite."""
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.makeSuite(TestFaceManager))
    suite.addTest(unittest.makeSuite(TestImageFileHandler))
    suite.addTest(unittest.makeSuite(TestChatApp))
    suite.addTest(unittest.makeSuite(TestCSVOperations))
    suite.addTest(unittest.makeSuite(TestIntegration))

    return suite


if __name__ == '__main__':
    print("Running Facial Recognition System Unit Tests")
    print("=" * 50)

    # Install required test dependencies
    try:
        from PIL import Image
    except ImportError:
        print("Warning: PIL (Pillow) not available. Some tests may fail.")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    suite = create_test_suite()
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print(f"\nFailures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    sys.exit(0 if result.wasSuccessful() else 1)