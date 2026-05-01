from fastapi.testclient import TestClient

from app import main
from app.contracts import ScannerErrorCode
from app.sessions import SessionStore


def client() -> TestClient:
    main.store = SessionStore()
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
