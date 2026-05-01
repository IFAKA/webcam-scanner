import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_urlsafe
from uuid import UUID, uuid4

from .contracts import (
    CapabilityReport,
    CaptureFrameMetadata,
    CaptureFrameRecord,
    CaptureFrameSummary,
    LocalNetworkConfig,
    ProcessingStatus,
    ProcessingSummary,
    RoomGeometry,
    ScanState,
    ScanTelemetrySample,
    ScannerError,
    ScannerErrorCode,
    SessionSnapshot,
    TelemetrySummary,
)
from .errors import make_error


@dataclass
class SessionRecord:
    session_id: UUID
    pairing_token: str
    network_config: LocalNetworkConfig
    state: ScanState = ScanState.CREATED
    network_paired: bool = False
    capability_report: CapabilityReport | None = None
    last_error: ScannerError | None = None
    telemetry: TelemetrySummary = field(default_factory=TelemetrySummary)
    capture_frames: CaptureFrameSummary = field(default_factory=CaptureFrameSummary)
    capture_frame_records: list[CaptureFrameRecord] = field(default_factory=list)
    processing: ProcessingSummary = field(default_factory=ProcessingSummary)


class SessionStore:
    def __init__(self, capture_root: Path | str = "captures") -> None:
        self._sessions: dict[UUID, SessionRecord] = {}
        self._capture_root = Path(capture_root)

    def create(self, network_config: LocalNetworkConfig) -> SessionRecord:
        session = SessionRecord(
            session_id=uuid4(),
            pairing_token=token_urlsafe(24),
            network_config=network_config,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: UUID) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def snapshot(self, session_id: UUID) -> SessionSnapshot | None:
        session = self.get(session_id)
        if session is None:
            return None

        return SessionSnapshot(
            session_id=session.session_id,
            state=session.state,
            last_error=session.last_error,
            capability_report=session.capability_report,
            network_paired=session.network_paired,
            network_config=session.network_config,
            telemetry=session.telemetry,
            capture_frames=session.capture_frames,
            processing=session.processing,
        )

    def pair(self, session_id: UUID, pairing_token: str) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None

        if pairing_token != session.pairing_token:
            session.network_paired = False
            session.state = ScanState.FAILED
            session.last_error = make_error(
                ScannerErrorCode.NETWORK_PAIRING_FAILED,
                stage="pairing",
                session_id=session_id,
            )
            return session

        session.network_paired = True
        session.state = ScanState.DEVICE_CHECKING
        session.last_error = None
        return session

    def record_capture_frame(self, session_id: UUID, metadata: CaptureFrameMetadata) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None

        if session.state != ScanState.SCANNING:
            session.last_error = make_error(
                ScannerErrorCode.SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE,
                stage="frame_capture",
                recoverable=True,
                session_id=session_id,
                details={
                    "state": session.state,
                    "frame_index": metadata.frame_index,
                },
            )
            return session

        frame_id = f"{metadata.frame_index:08d}"
        session_dir = self._capture_root / str(session.session_id)
        manifest_path = session_dir / "frames.jsonl"
        session_dir.mkdir(parents=True, exist_ok=True)

        record = CaptureFrameRecord(
            frame_id=frame_id,
            metadata=metadata,
            metadata_path=str(manifest_path),
            raw_artifacts_uploaded=False,
        )
        with manifest_path.open("a", encoding="utf-8") as manifest:
            manifest.write(json.dumps(record.model_dump(mode="json"), separators=(",", ":")))
            manifest.write("\n")

        session.capture_frames = CaptureFrameSummary(
            persisted_count=session.capture_frames.persisted_count + 1,
            latest_frame=record,
            manifest_path=str(manifest_path),
        )
        session.capture_frame_records.append(record)
        session.processing = evaluate_processing_inputs(session)
        session.last_error = None
        return session

    def start_processing(self, session_id: UUID) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None

        processing = evaluate_processing_inputs(session)
        session.processing = processing
        if processing.status != ProcessingStatus.READY_TO_PROCESS:
            session.last_error = make_error(
                ScannerErrorCode.UPLOAD_INCOMPLETE,
                stage="processing",
                recoverable=True,
                session_id=session_id,
                details={
                    "input_frame_count": processing.input_frame_count,
                    "required_artifacts": processing.required_artifacts,
                    "available_artifacts": processing.available_artifacts,
                    "blocked_reason": processing.blocked_reason,
                },
            )
            return session

        previous_state = session.state
        session.state = ScanState.PROCESSING
        output_path = self._capture_root / str(session.session_id) / "review-geometry.json"
        try:
            geometry = RoomGeometry(
                source_frame_count=len(session.capture_frame_records),
                floor_outline_m=build_camera_path_outline(session.capture_frame_records),
                output_path=str(output_path),
            )
        except ValueError as error:
            session.state = previous_state
            session.processing = ProcessingSummary(
                status=ProcessingStatus.FAILED,
                input_frame_count=len(session.capture_frame_records),
                available_artifacts=processing.available_artifacts,
                blocked_reason=str(error),
            )
            session.last_error = make_error(
                ScannerErrorCode.GEOMETRY_POLYGON_INVALID,
                stage="processing",
                recoverable=True,
                session_id=session_id,
                details={"blocked_reason": str(error)},
            )
            return session
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(geometry.model_dump(mode="json"), separators=(",", ":")), encoding="utf-8")
        session.processing = ProcessingSummary(
            status=ProcessingStatus.READY_FOR_REVIEW,
            input_frame_count=len(session.capture_frame_records),
            available_artifacts=processing.available_artifacts,
            blocked_reason=None,
            geometry=geometry,
        )
        session.state = ScanState.READY_FOR_REVIEW
        session.last_error = None
        return session

    def save_capabilities(self, session_id: UUID, report: CapabilityReport) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None
        server_report = report.model_copy(update={"network_paired": session.network_paired})
        evaluated = evaluate_capabilities(session_id, server_report)
        session.capability_report = evaluated
        session.last_error = evaluated.failure_reason
        session.state = ScanState.READY if evaluated.can_scan else ScanState.FAILED
        return session

    def start_scan(self, session_id: UUID) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None

        if session.state == ScanState.SCANNING:
            return session

        if (
            session.state == ScanState.READY
            and session.network_paired
            and session.capability_report is not None
            and session.capability_report.can_scan
        ):
            session.state = ScanState.SCANNING
            session.last_error = None
            return session

        session.last_error = make_error(
            ScannerErrorCode.SESSION_NOT_READY_FOR_SCAN,
            stage="scan_start",
            recoverable=True,
            session_id=session_id,
            details={
                "state": session.state,
                "network_paired": session.network_paired,
                "capability_report_received": session.capability_report is not None,
                "can_scan": session.capability_report.can_scan if session.capability_report else False,
            },
        )
        return session

    def record_telemetry(self, session_id: UUID, sample: ScanTelemetrySample) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None

        if session.state != ScanState.SCANNING:
            session.last_error = make_error(
                ScannerErrorCode.SESSION_NOT_SCANNING_FOR_TELEMETRY,
                stage="telemetry",
                recoverable=True,
                session_id=session_id,
                details={
                    "state": session.state,
                    "frame_index": sample.frame_index,
                },
            )
            return session

        session.telemetry = TelemetrySummary(
            frame_count=session.telemetry.frame_count + 1,
            latest_sample=sample,
            latest_received_at=datetime.now(UTC),
        )
        session.last_error = None
        return session


def evaluate_capabilities(session_id: UUID, report: CapabilityReport) -> CapabilityReport:
    checks = [
        (report.camera_permission, ScannerErrorCode.PERMISSION_CAMERA_DENIED),
        (report.arcore_supported, ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED),
        (report.depth_supported, ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED),
        (report.raw_depth_available, ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE),
        (report.confidence_available, ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE),
        (report.tracking_available, ScannerErrorCode.DEVICE_TRACKING_NOT_READY),
        (report.network_paired, ScannerErrorCode.NETWORK_PAIRING_FAILED),
    ]

    for is_passing, code in checks:
        if not is_passing:
            return report.model_copy(
                update={
                    "can_scan": False,
                    "failure_reason": make_error(code, stage="device_check", session_id=session_id),
                }
            )

    return report.model_copy(update={"can_scan": True, "failure_reason": None})


def evaluate_processing_inputs(session: SessionRecord) -> ProcessingSummary:
    records = session.capture_frame_records
    if not records:
        return ProcessingSummary(
            input_frame_count=0,
            blocked_reason="Capture at least one frame metadata record before processing.",
        )

    available_artifacts = sorted(
        {
            artifact
            for record in records
            for artifact, filename in {
                "color_image": record.metadata.color_image_filename,
                "raw_depth": record.metadata.depth_filename,
                "confidence": record.metadata.confidence_filename,
            }.items()
            if filename
        }
    )
    missing_artifacts = [
        artifact
        for artifact in ["color_image", "raw_depth", "confidence"]
        if artifact not in available_artifacts
    ]
    pending_uploads = [record.frame_id for record in records if not record.raw_artifacts_uploaded]
    if missing_artifacts or pending_uploads:
        reason_parts = []
        if missing_artifacts:
            reason_parts.append(f"missing {', '.join(missing_artifacts)} filenames")
        if pending_uploads:
            reason_parts.append(f"{len(pending_uploads)} frames still need raw artifact upload confirmation")
        return ProcessingSummary(
            status=ProcessingStatus.BLOCKED,
            input_frame_count=len(records),
            available_artifacts=available_artifacts,
            blocked_reason="; ".join(reason_parts),
        )

    return ProcessingSummary(
        status=ProcessingStatus.READY_TO_PROCESS,
        input_frame_count=len(records),
        available_artifacts=available_artifacts,
        blocked_reason=None,
    )


def build_camera_path_outline(records: list[CaptureFrameRecord]) -> list[tuple[float, float]]:
    points = [
        (record.metadata.camera_position_m[0], record.metadata.camera_position_m[2])
        for record in records
        if record.metadata.camera_position_m is not None
    ]
    if len(points) < 3:
        raise ValueError("At least three tracked camera positions are required for review geometry.")

    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_z = min(point[1] for point in points)
    max_z = max(point[1] for point in points)
    return [(min_x, min_z), (max_x, min_z), (max_x, max_z), (min_x, max_z)]
