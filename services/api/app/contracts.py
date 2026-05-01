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
    SESSION_NOT_READY_FOR_SCAN = "SESSION_NOT_READY_FOR_SCAN"
    SESSION_NOT_SCANNING_FOR_TELEMETRY = "SESSION_NOT_SCANNING_FOR_TELEMETRY"
    SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE = "SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE"
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
    ScannerErrorCode.SESSION_NOT_READY_FOR_SCAN: "The scan cannot start until the backend session is READY.",
    ScannerErrorCode.SESSION_NOT_SCANNING_FOR_TELEMETRY: "Telemetry is blocked until the backend session is SCANNING.",
    ScannerErrorCode.SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE: "Frame capture metadata is blocked until the backend session is SCANNING.",
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


class LocalNetworkConfig(BaseModel):
    api_base_url: str
    websocket_base_url: str
    host: str
    port: int
    detected_interface: str
    is_loopback: bool


class CreateSessionResponse(BaseModel):
    session_id: UUID
    pairing_token: str
    state: ScanState
    websocket_path: str
    network_config: LocalNetworkConfig


class PairSessionRequest(BaseModel):
    pairing_token: str


class ScanTelemetrySample(BaseModel):
    frame_index: int = Field(ge=0)
    tracking_state: str = Field(min_length=1)
    monotonic_timestamp_ms: int = Field(ge=0)
    camera_position_m: tuple[float, float, float] | None = None
    camera_rotation_quaternion: tuple[float, float, float, float] | None = None
    depth_frame_available: bool
    confidence_frame_available: bool


class TelemetrySummary(BaseModel):
    frame_count: int = 0
    latest_sample: ScanTelemetrySample | None = None
    latest_received_at: datetime | None = None


class CaptureFrameMetadata(BaseModel):
    frame_index: int = Field(ge=0)
    tracking_state: str = Field(min_length=1)
    monotonic_timestamp_ms: int = Field(ge=0)
    camera_position_m: tuple[float, float, float] | None = None
    camera_rotation_quaternion: tuple[float, float, float, float] | None = None
    depth_frame_available: bool
    confidence_frame_available: bool
    color_image_filename: str | None = Field(default=None, min_length=1)
    depth_filename: str | None = Field(default=None, min_length=1)
    confidence_filename: str | None = Field(default=None, min_length=1)


class CaptureArtifactPayload(BaseModel):
    filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    media_type: str | None = Field(default=None, min_length=1)
    sha256: str | None = Field(default=None, min_length=64, max_length=64)


class CaptureFrameArtifactUpload(BaseModel):
    frame_index: int = Field(ge=0)
    color_image: CaptureArtifactPayload
    raw_depth: CaptureArtifactPayload
    confidence: CaptureArtifactPayload


class CaptureArtifactRecord(BaseModel):
    filename: str
    path: str
    byte_size: int = Field(ge=0)
    sha256: str
    media_type: str | None = None


class CaptureFrameRecord(BaseModel):
    frame_id: str
    metadata: CaptureFrameMetadata
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata_path: str
    raw_artifacts_uploaded: bool = False
    artifacts: dict[str, CaptureArtifactRecord] = Field(default_factory=dict)


class CaptureFrameSummary(BaseModel):
    persisted_count: int = 0
    latest_frame: CaptureFrameRecord | None = None
    manifest_path: str | None = None


class ProcessingStatus(StrEnum):
    BLOCKED = "BLOCKED"
    READY_TO_PROCESS = "READY_TO_PROCESS"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    FAILED = "FAILED"


class RoomGeometry(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_frame_count: int
    floor_outline_m: list[tuple[float, float]]
    output_path: str


class ProcessingSummary(BaseModel):
    status: ProcessingStatus = ProcessingStatus.BLOCKED
    input_frame_count: int = 0
    required_artifacts: list[str] = Field(default_factory=lambda: ["color_image", "raw_depth", "confidence"])
    available_artifacts: list[str] = Field(default_factory=list)
    blocked_reason: str | None = "Waiting for captured scan frames."
    geometry: RoomGeometry | None = None


class SessionSnapshot(BaseModel):
    session_id: UUID
    state: ScanState
    last_error: ScannerError | None = None
    capability_report: CapabilityReport | None = None
    network_paired: bool = False
    network_config: LocalNetworkConfig | None = None
    telemetry: TelemetrySummary = Field(default_factory=TelemetrySummary)
    capture_frames: CaptureFrameSummary = Field(default_factory=CaptureFrameSummary)
    processing: ProcessingSummary = Field(default_factory=ProcessingSummary)
