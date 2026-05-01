from dataclasses import dataclass
from secrets import token_urlsafe
from uuid import UUID, uuid4

from .contracts import CapabilityReport, ScanState, ScannerErrorCode, SessionSnapshot
from .errors import make_error


@dataclass
class SessionRecord:
    session_id: UUID
    pairing_token: str
    state: ScanState = ScanState.CREATED
    capability_report: CapabilityReport | None = None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}

    def create(self) -> SessionRecord:
        session = SessionRecord(session_id=uuid4(), pairing_token=token_urlsafe(24))
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: UUID) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def snapshot(self, session_id: UUID) -> SessionSnapshot | None:
        session = self.get(session_id)
        if session is None:
            return None

        last_error = None
        if session.capability_report and session.capability_report.failure_reason:
            last_error = session.capability_report.failure_reason

        return SessionSnapshot(
            session_id=session.session_id,
            state=session.state,
            last_error=last_error,
            capability_report=session.capability_report,
        )

    def save_capabilities(self, session_id: UUID, report: CapabilityReport) -> SessionRecord | None:
        session = self.get(session_id)
        if session is None:
            return None
        session.capability_report = report
        session.state = ScanState.READY if report.can_scan else ScanState.FAILED
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
