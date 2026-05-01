from dataclasses import dataclass
from secrets import token_urlsafe
from uuid import UUID, uuid4

from .contracts import CapabilityReport, LocalNetworkConfig, ScanState, ScannerError, ScannerErrorCode, SessionSnapshot
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


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}

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
