import os
from uuid import UUID

from fastapi import FastAPI, HTTPException

from .contracts import CapabilityReport, CreateSessionResponse, PairSessionRequest, ScanTelemetrySample, SessionSnapshot
from .network import DEFAULT_API_PORT, local_network_config
from .sessions import SessionStore

app = FastAPI(title="Room Boundary Scanner API", version="0.1.0")
store = SessionStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session() -> CreateSessionResponse:
    network_config = local_network_config(
        public_api_url=os.getenv("ROOM_SCANNER_PUBLIC_API_URL"),
        api_port=int(os.getenv("ROOM_SCANNER_API_PORT", str(DEFAULT_API_PORT))),
    )
    session = store.create(network_config)
    return CreateSessionResponse(
        session_id=session.session_id,
        pairing_token=session.pairing_token,
        state=session.state,
        websocket_path=f"/sessions/{session.session_id}/telemetry",
        network_config=session.network_config,
    )


@app.get("/sessions/{session_id}", response_model=SessionSnapshot)
def get_session(session_id: UUID) -> SessionSnapshot:
    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot


@app.post("/sessions/{session_id}/pair", response_model=SessionSnapshot)
def pair_session(session_id: UUID, request: PairSessionRequest) -> SessionSnapshot:
    session = store.pair(session_id, request.pairing_token)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot


@app.post("/sessions/{session_id}/capabilities", response_model=SessionSnapshot)
def submit_capabilities(session_id: UUID, report: CapabilityReport) -> SessionSnapshot:
    session = store.save_capabilities(session_id, report)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot


@app.post("/sessions/{session_id}/scan/start", response_model=SessionSnapshot)
def start_scan(session_id: UUID) -> SessionSnapshot:
    session = store.start_scan(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot


@app.post("/sessions/{session_id}/telemetry", response_model=SessionSnapshot)
def submit_telemetry(session_id: UUID, sample: ScanTelemetrySample) -> SessionSnapshot:
    session = store.record_telemetry(session_id, sample)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot


@app.get("/sessions/{session_id}/diagnostics", response_model=SessionSnapshot)
def get_diagnostics(session_id: UUID) -> SessionSnapshot:
    snapshot = store.snapshot(session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return snapshot
