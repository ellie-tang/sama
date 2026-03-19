from __future__ import annotations

from pathlib import Path
import re


CLIENT_PATH = Path(
    "src/Blade_2_Template_App/app/src/main/java/devkit/blade/vuzix/com/blade_template_app/FaceRecognitionApiClient.java"
)
RECEIVER_PATH = Path(
    "src/Blade_2_Template_App/app/src/main/java/devkit/blade/vuzix/com/blade_template_app/FaceRecognitionBroadcastReceiver.java"
)
ACTIVITY_PATH = Path(
    "src/Blade_2_Template_App/app/src/main/java/devkit/blade/vuzix/com/blade_template_app/center_content_template_activity.java"
)


def test_api_client_posts_to_process_image_endpoint():
    source = CLIENT_PATH.read_text(encoding="utf-8")

    assert 'private static final String PROCESS_IMAGE_ENDPOINT = BASE_URL + "/api/process-image";' in source
    assert '.addFormDataPart("file", filename' in source


def test_api_client_and_receiver_share_same_broadcast_action():
    client_source = CLIENT_PATH.read_text(encoding="utf-8")
    receiver_source = RECEIVER_PATH.read_text(encoding="utf-8")

    action_match = re.search(r'ACTION_FACE_RECOGNIZED = "([^"]+)"', receiver_source)
    assert action_match is not None
    action_name = action_match.group(1)
    assert action_name in client_source


def test_activity_requests_camera_permission_and_starts_capture_service():
    source = ACTIVITY_PATH.read_text(encoding="utf-8")

    assert "ActivityCompat.requestPermissions" in source
    assert "android.Manifest.permission.CAMERA" in source
    assert "new Intent(this, CameraCaptureService.class)" in source
    assert "startService(serviceIntent);" in source


def test_activity_registers_face_recognition_receiver():
    source = ACTIVITY_PATH.read_text(encoding="utf-8")

    assert "new FaceRecognitionBroadcastReceiver()" in source
    assert "registerReceiver(recognitionReceiver, filter);" in source
    assert "FaceRecognitionBroadcastReceiver.ACTION_FACE_RECOGNIZED" in source
