import { CapabilityPanel } from "../components/capability-panel";
import { DiagnosticsPanel } from "../components/diagnostics-panel";
import { FrameManifestPanel } from "../components/frame-manifest-panel";
import { PairingPanel } from "../components/pairing-panel";
import { ProcessingPanel } from "../components/processing-panel";
import { SessionMonitor } from "../components/session-monitor";
import { TelemetryPanel } from "../components/telemetry-panel";
import { apiBaseUrl, createSession } from "../lib/api";
import type { SessionSnapshot } from "../lib/contracts";

export const dynamic = "force-dynamic";

export default async function Home() {
  const apiUrl = apiBaseUrl();
  const createdSession = await createSession().catch(() => null);
  const session: SessionSnapshot = {
    session_id: createdSession?.session_id ?? "unavailable",
    state: createdSession?.state ?? "FAILED",
    last_error: null,
    capability_report: null,
    network_paired: false,
    network_config: createdSession?.network_config ?? null,
    telemetry: {
      frame_count: 0,
      latest_sample: null,
      latest_received_at: null,
    },
    capture_frames: {
      persisted_count: 0,
      latest_frame: null,
      manifest_path: null,
    },
    processing: {
      status: "BLOCKED",
      input_frame_count: 0,
      required_artifacts: ["color_image", "raw_depth", "confidence"],
      available_artifacts: [],
      blocked_reason: "Waiting for captured scan frames.",
      geometry: null,
    },
  };

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <main className="shell" id="main-content">
        <header className="topbar">
          <div className="brand">
            <h1>Room Boundary Scanner</h1>
            <p>Local ARCore Depth control room</p>
          </div>
          <span className="status fail">No fallback mode</span>
        </header>

        <div className="grid">
          <div>
            {createdSession ? (
              <PairingPanel serverApiUrl={apiUrl} session={createdSession} />
            ) : (
              <ApiUnavailablePanel apiUrl={apiUrl} />
            )}
            {createdSession ? (
              <SessionMonitor initialSession={session} />
            ) : (
              <>
                <CapabilityPanel report={session.capability_report} lastError={session.last_error} state={session.state} />
                <TelemetryPanel state={session.state} telemetry={session.telemetry} />
                <FrameManifestPanel state={session.state} captureFrames={session.capture_frames} />
                <ProcessingPanel state={session.state} processing={session.processing} canStartProcessing={false} />
                <DiagnosticsPanel session={session} />
              </>
            )}
          </div>

          <section className="panel">
            <h2>Live Room View</h2>
            <div className="viewport">
              <p className="muted">Pair the Android scanner to stream pose and sparse points.</p>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}

function ApiUnavailablePanel({ apiUrl }: { apiUrl: string }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Phone Pairing</h2>
        <span className="status fail">API offline</span>
      </div>
      <p className="network-note error" role="status">
        Scanning is blocked because the local API did not create a session. Start the FastAPI backend and confirm
        the desktop API URL is reachable before pairing the phone.
      </p>
      <div className="pairing-fields">
        <div className="pairing-value">
          <span>Desktop API URL</span>
          <code translate="no">{apiUrl}</code>
        </div>
      </div>
    </section>
  );
}
