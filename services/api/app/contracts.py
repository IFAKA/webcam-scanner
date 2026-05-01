from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScanState(StrEnum):
    CREATED = "CREATED"
    PAIRING = "PAIRING"
    DEVICE_CHECKING = "DEVICE_CHECKING"
    READY = "READY"
    SCANNING = "SCANNING"
    CAPTURE_COMPLETE = "CAPTURE_COMPLETE"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"


class ScannerErrorCode(StrEnum):
    DEVICE_ARCORE_UNSUPPORTED = "DEVICE_ARCORE_UNSUPPORTED"
    DEVICE_DEPTH_UNSUPPORTED = "DEVICE_DEPTH_UNSUPPORTED"
    DEVICE_RAW_DEPTH_UNAVAILABLE = "DEVICE_RAW_DEPTH_UNAVAILABLE"
    DEVICE_TRACKING_NOT_READY = "DEVICE_TRACKING_NOT_READY"
    PERMISSION_CAMERA_DENIED = "PERMISSION_CAMERA_DENIED"
    NETWORK_PAIRING_FAILED = "NETWORK_PAIRING_FAILED"
    NETWORK_WEBSOCKET_DROPPED = "NETWORK_WEBSOCKET_DROPPED"
    UPLOAD_INCOMPLETE = "UPLOAD_INCOMPLETE"
    SESSION_SCHEMA_INVALID = "SESSION_SCHEMA_INVALID"
    PROCESSING_POINT_CLOUD_FAILED = "PROCESSING_POINT_CLOUD_FAILED"
    PROCESSING_PLANE_FIT_FAILED = "PROCESSING_PLANE_FIT_FAILED"
    GEOMETRY_POLYGON_INVALID = "GEOMETRY_POLYGON_INVALID"
    EXPORT_FAILED = "EXPORT_FAILED"
    UNKNOWN_INTERNAL_ERROR = "UNKNOWN_INTERNAL_ERROR"


ERROR_MESSAGES: dict[ScannerErrorCode, str] = {
    ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED: "This device cannot scan because ARCore is unavailable.",
    ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED: "This device cannot scan because ARCore Depth is unavailable.",
    ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE: "This device cannot scan because raw depth frames are unavailable.",
    ScannerErrorCode.DEVICE_TRACKING_NOT_READY: "The device could not reach stable AR tracking.",
    ScannerErrorCode.PERMISSION_CAMERA_DENIED: "Camera permission is required before scanning.",
    ScannerErrorCode.NETWORK_PAIRING_FAILED: "The phone could not pair with the local laptop server.",
    ScannerErrorCode.NETWORK_WEBSOCKET_DROPPED: "The live scan connection was lost.",
    ScannerErrorCode.UPLOAD_INCOMPLETE: "The scan upload is missing required files.",
    ScannerErrorCode.SESSION_SCHEMA_INVALID: "The scan session data is invalid.",
    ScannerErrorCode.PROCESSING_POINT_CLOUD_FAILED: "The backend could not build a point cloud from the scan.",
    ScannerErrorCode.PROCESSING_PLANE_FIT_FAILED: "The backend could not extract reliable room planes.",
    ScannerErrorCode.GEOMETRY_POLYGON_INVALID: "The generated floorplan geometry is invalid.",
    ScannerErrorCode.EXPORT_FAILED: "The backend could not export the requested file.",
    ScannerErrorCode.UNKNOWN_INTERNAL_ERROR: "An unexpected local error occurred.",
}


class ScannerError(BaseModel):
    code: ScannerErrorCode
    message: str
    stage: str
    recoverable: bool
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    session_id: UUID | None = None


class CapabilityReport(BaseModel):
    device_model: str
    arcore_supported: bool
    depth_supported: bool
    raw_depth_available: bool
    confidence_available: bool
    tracking_available: bool
    camera_permission: bool
    network_paired: bool
    can_scan: bool
    failure_reason: ScannerError | None = None


class CreateSessionResponse(BaseModel):
    session_id: UUID
    pairing_token: str
    state: ScanState
    websocket_path: str


class PairSessionRequest(BaseModel):
    pairing_token: str


class SessionSnapshot(BaseModel):
    session_id: UUID
    state: ScanState
    last_error: ScannerError | None = None
    capability_report: CapabilityReport | None = None
    network_paired: bool = False
