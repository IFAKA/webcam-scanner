import { CapabilityPanel } from "../components/capability-panel";
import { DiagnosticsPanel } from "../components/diagnostics-panel";
import { mockSession } from "../lib/mock-session";

export default function Home() {
  const session = mockSession;

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <h1>Room Boundary Scanner</h1>
          <p>Local ARCore Depth control room</p>
        </div>
        <span className="status fail">No fallback mode</span>
      </header>

      <div className="grid">
        <div>
          <CapabilityPanel report={session.capability_report} lastError={session.last_error} />
          <DiagnosticsPanel session={session} />
        </div>

        <section className="panel">
          <h2>Live Room View</h2>
          <div className="viewport">
            <p className="muted">Pair the Android scanner to stream pose and sparse points.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
