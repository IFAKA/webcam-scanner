from uuid import UUID

from .contracts import ERROR_MESSAGES, ScannerError, ScannerErrorCode


def make_error(
    code: ScannerErrorCode,
    *,
    stage: str,
    recoverable: bool = False,
    session_id: UUID | None = None,
    details: dict | None = None,
) -> ScannerError:
    return ScannerError(
        code=code,
        message=ERROR_MESSAGES[code],
        stage=stage,
        recoverable=recoverable,
        details=details or {},
        session_id=session_id,
    )
