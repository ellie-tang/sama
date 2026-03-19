from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


MANIFEST_PATH = Path("src/Blade_2_Template_App/app/src/main/AndroidManifest.xml")
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


def _parse_manifest():
    return ET.parse(MANIFEST_PATH).getroot()


def test_manifest_declares_camera_and_network_permissions():
    root = _parse_manifest()
    permissions = {
        node.attrib.get(f"{ANDROID_NS}name")
        for node in root.findall("uses-permission")
    }

    assert "android.permission.CAMERA" in permissions
    assert "android.permission.INTERNET" in permissions
    assert "android.permission.ACCESS_NETWORK_STATE" in permissions


def test_manifest_registers_camera_capture_service():
    root = _parse_manifest()
    application = root.find("application")
    services = application.findall("service") if application is not None else []
    service_names = {
        node.attrib.get(f"{ANDROID_NS}name")
        for node in services
    }

    assert ".CameraCaptureService" in service_names


def test_manifest_uses_hud_theme_and_main_launcher_activity():
    root = _parse_manifest()
    application = root.find("application")
    assert application is not None
    assert application.attrib.get(f"{ANDROID_NS}theme") == "@style/HudTheme"

    activities = application.findall("activity")
    launcher = None
    for activity in activities:
        if activity.attrib.get(f"{ANDROID_NS}name") == ".center_content_template_activity":
            launcher = activity
            break

    assert launcher is not None
    categories = {
        node.attrib.get(f"{ANDROID_NS}name")
        for node in launcher.findall("./intent-filter/category")
    }
    assert "android.intent.category.LAUNCHER" in categories
