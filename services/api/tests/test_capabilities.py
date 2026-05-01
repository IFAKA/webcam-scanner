from uuid import uuid4

from app.contracts import CapabilityReport, ScannerErrorCode
from app.sessions import evaluate_capabilities


def base_report(**overrides):
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
    return CapabilityReport(**values)


def test_all_required_capabilities_enable_scan():
    report = evaluate_capabilities(uuid4(), base_report())

    assert report.can_scan is True
    assert report.failure_reason is None


def test_missing_depth_blocks_scan():
    report = evaluate_capabilities(uuid4(), base_report(depth_supported=False))

    assert report.can_scan is False
    assert report.failure_reason is not None
    assert report.failure_reason.code == ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED


def test_missing_tracking_blocks_scan():
    report = evaluate_capabilities(uuid4(), base_report(tracking_available=False))

    assert report.can_scan is False
    assert report.failure_reason is not None
    assert report.failure_reason.code == ScannerErrorCode.DEVICE_TRACKING_NOT_READY
