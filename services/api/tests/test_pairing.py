from fastapi.testclient import TestClient

from app import main
from app.contracts import ScannerErrorCode
from app.sessions import SessionStore


def client(capture_root=None) -> TestClient:
    main.store = SessionStore(capture_root=capture_root or "captures/test")
    return TestClient(main.app)


def capability_payload(**overrides):
    values = {
        "device_model": "Redmi Note 14 5G",
        "arcore_supported": True,
        "depth_supported": True,
        "raw_depth_available": True,
        "confidence_available": True,
        "tracking_available": True,
        "camera_permission": True,
        "network_paired": True,
        "can_scan": False,
    }
    values.update(overrides)
    return values


def telemetry_payload(**overrides):
    values = {
        "frame_index": 0,
        "tracking_state": "APP_HEARTBEAT",
        "monotonic_timestamp_ms": 1000,
        "camera_position_m": None,
        "camera_rotation_quaternion": None,
        "depth_frame_available": False,
        "confidence_frame_available": False,
    }
    values.update(overrides)
    return values


def frame_payload(**overrides):
    values = {
        "frame_index": 0,
        "tracking_state": "APP_HEARTBEAT",
        "monotonic_timestamp_ms": 1000,
        "camera_position_m": None,
        "camera_rotation_quaternion": None,
        "depth_frame_available": True,
        "confidence_frame_available": True,
        "color_image_filename": None,
        "depth_filename": None,
        "confidence_filename": None,
    }
    values.update(overrides)
    return values


def test_valid_pairing_moves_session_to_device_checking():
    api = client()
    created = api.post("/sessions").json()

    response = api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "DEVICE_CHECKING"
    assert snapshot["network_paired"] is True
    assert snapshot["last_error"] is None
    assert snapshot["network_config"]["api_base_url"] == created["network_config"]["api_base_url"]


def test_session_creation_includes_configured_lan_api_url(monkeypatch):
    monkeypatch.setenv("ROOM_SCANNER_PUBLIC_API_URL", "http://192.168.1.20:8000/")
    api = client()

    created = api.post("/sessions").json()

    assert created["network_config"] == {
        "api_base_url": "http://192.168.1.20:8000",
        "websocket_base_url": "ws://192.168.1.20:8000",
        "host": "192.168.1.20",
        "port": 8000,
        "detected_interface": "configured",
        "is_loopback": False,
    }


def test_invalid_pairing_token_fails_clearly():
    api = client()
    created = api.post("/sessions").json()

    response = api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": "wrong-token"},
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "FAILED"
    assert snapshot["network_paired"] is False
    assert snapshot["last_error"]["code"] == ScannerErrorCode.NETWORK_PAIRING_FAILED
    assert snapshot["last_error"]["stage"] == "pairing"


def test_capabilities_cannot_self_assert_network_pairing():
    api = client()
    created = api.post("/sessions").json()

    response = api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=True),
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "FAILED"
    assert snapshot["network_paired"] is False
    assert snapshot["capability_report"]["network_paired"] is False
    assert snapshot["last_error"]["code"] == ScannerErrorCode.NETWORK_PAIRING_FAILED


def test_paired_capability_report_marks_session_ready():
    api = client()
    created = api.post("/sessions").json()
    api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )

    response = api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=False, can_scan=False),
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "READY"
    assert snapshot["network_paired"] is True
    assert snapshot["capability_report"]["network_paired"] is True
    assert snapshot["capability_report"]["can_scan"] is True
    assert snapshot["last_error"] is None


def test_scan_start_is_blocked_until_session_is_ready():
    api = client()
    created = api.post("/sessions").json()

    response = api.post(f"/sessions/{created['session_id']}/scan/start")

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "CREATED"
    assert snapshot["last_error"]["code"] == ScannerErrorCode.SESSION_NOT_READY_FOR_SCAN
    assert snapshot["last_error"]["stage"] == "scan_start"
    assert snapshot["last_error"]["recoverable"] is True
    assert snapshot["last_error"]["details"]["capability_report_received"] is False


def test_scan_start_moves_ready_session_to_scanning():
    api = client()
    created = api.post("/sessions").json()
    api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )
    api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=False, can_scan=False),
    )

    response = api.post(f"/sessions/{created['session_id']}/scan/start")

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "SCANNING"
    assert snapshot["network_paired"] is True
    assert snapshot["capability_report"]["can_scan"] is True
    assert snapshot["last_error"] is None


def test_telemetry_is_blocked_until_session_is_scanning():
    api = client()
    created = api.post("/sessions").json()

    response = api.post(
        f"/sessions/{created['session_id']}/telemetry",
        json=telemetry_payload(),
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "CREATED"
    assert snapshot["telemetry"]["frame_count"] == 0
    assert snapshot["telemetry"]["latest_sample"] is None
    assert snapshot["last_error"]["code"] == ScannerErrorCode.SESSION_NOT_SCANNING_FOR_TELEMETRY
    assert snapshot["last_error"]["stage"] == "telemetry"
    assert snapshot["last_error"]["recoverable"] is True
    assert snapshot["last_error"]["details"]["frame_index"] == 0


def test_scanning_session_accepts_live_telemetry():
    api = client()
    created = api.post("/sessions").json()
    api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )
    api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=False, can_scan=False),
    )
    api.post(f"/sessions/{created['session_id']}/scan/start")

    first = api.post(
        f"/sessions/{created['session_id']}/telemetry",
        json=telemetry_payload(frame_index=7, monotonic_timestamp_ms=7000),
    )
    second = api.post(
        f"/sessions/{created['session_id']}/telemetry",
        json=telemetry_payload(frame_index=8, monotonic_timestamp_ms=8000),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    snapshot = second.json()
    assert snapshot["state"] == "SCANNING"
    assert snapshot["last_error"] is None
    assert snapshot["telemetry"]["frame_count"] == 2
    assert snapshot["telemetry"]["latest_received_at"] is not None
    assert snapshot["telemetry"]["latest_sample"]["frame_index"] == 8
    assert snapshot["telemetry"]["latest_sample"]["tracking_state"] == "APP_HEARTBEAT"


def test_frame_metadata_is_blocked_until_session_is_scanning(tmp_path):
    api = client(capture_root=tmp_path)
    created = api.post("/sessions").json()

    response = api.post(
        f"/sessions/{created['session_id']}/frames",
        json=frame_payload(),
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "CREATED"
    assert snapshot["capture_frames"]["persisted_count"] == 0
    assert snapshot["capture_frames"]["latest_frame"] is None
    assert snapshot["last_error"]["code"] == ScannerErrorCode.SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE
    assert snapshot["last_error"]["stage"] == "frame_capture"
    assert snapshot["last_error"]["recoverable"] is True
    assert snapshot["last_error"]["details"]["frame_index"] == 0
    assert not list(tmp_path.rglob("frames.jsonl"))


def test_scanning_session_persists_frame_metadata_manifest(tmp_path):
    api = client(capture_root=tmp_path)
    created = api.post("/sessions").json()
    api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )
    api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=False, can_scan=False),
    )
    api.post(f"/sessions/{created['session_id']}/scan/start")

    first = api.post(
        f"/sessions/{created['session_id']}/frames",
        json=frame_payload(frame_index=7, monotonic_timestamp_ms=7000),
    )
    second = api.post(
        f"/sessions/{created['session_id']}/frames",
        json=frame_payload(frame_index=8, monotonic_timestamp_ms=8000, depth_filename="depth-000008.raw"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    snapshot = second.json()
    assert snapshot["state"] == "SCANNING"
    assert snapshot["last_error"] is None
    assert snapshot["capture_frames"]["persisted_count"] == 2
    assert snapshot["capture_frames"]["manifest_path"].endswith("frames.jsonl")
    assert snapshot["capture_frames"]["latest_frame"]["frame_id"] == "00000008"
    assert snapshot["capture_frames"]["latest_frame"]["raw_artifacts_uploaded"] is False
    assert snapshot["capture_frames"]["latest_frame"]["metadata"]["depth_filename"] == "depth-000008.raw"

    manifest = next(tmp_path.rglob("frames.jsonl"))
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert '"frame_id":"00000008"' in lines[1]


def test_processing_is_blocked_until_frame_metadata_exists(tmp_path):
    api = client(capture_root=tmp_path)
    created = api.post("/sessions").json()

    response = api.post(f"/sessions/{created['session_id']}/processing/start")

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "CREATED"
    assert snapshot["processing"]["status"] == "BLOCKED"
    assert snapshot["processing"]["input_frame_count"] == 0
    assert snapshot["processing"]["geometry"] is None
    assert snapshot["last_error"]["code"] == ScannerErrorCode.UPLOAD_INCOMPLETE
    assert snapshot["last_error"]["stage"] == "processing"
    assert snapshot["last_error"]["recoverable"] is True


def test_processing_is_blocked_until_raw_artifacts_are_uploaded(tmp_path):
    api = client(capture_root=tmp_path)
    created = api.post("/sessions").json()
    api.post(
        f"/sessions/{created['session_id']}/pair",
        json={"pairing_token": created["pairing_token"]},
    )
    api.post(
        f"/sessions/{created['session_id']}/capabilities",
        json=capability_payload(network_paired=False, can_scan=False),
    )
    api.post(f"/sessions/{created['session_id']}/scan/start")
    api.post(
        f"/sessions/{created['session_id']}/frames",
        json=frame_payload(
            frame_index=8,
            color_image_filename="color-000008.jpg",
            depth_filename="depth-000008.raw",
            confidence_filename="confidence-000008.raw",
        ),
    )

    response = api.post(f"/sessions/{created['session_id']}/processing/start")

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["state"] == "SCANNING"
    assert snapshot["processing"]["status"] == "BLOCKED"
    assert snapshot["processing"]["input_frame_count"] == 1
    assert snapshot["processing"]["available_artifacts"] == ["color_image", "confidence", "raw_depth"]
    assert snapshot["processing"]["geometry"] is None
    assert snapshot["last_error"]["code"] == ScannerErrorCode.UPLOAD_INCOMPLETE
    assert "raw artifact upload confirmation" in snapshot["processing"]["blocked_reason"]
