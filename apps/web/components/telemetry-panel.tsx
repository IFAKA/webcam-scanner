import type { ScanState, TelemetrySummary } from "../lib/contracts";

const sampleCountFormatter = new Intl.NumberFormat("en-US");
const receivedAtFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

export function TelemetryPanel({ state, telemetry }: { state: ScanState; telemetry: TelemetrySummary }) {
  const isStreaming = state === "SCANNING" && telemetry.frame_count > 0;
  const statusClass = isStreaming ? "ok" : state === "SCANNING" ? "wait" : "fail";
  const statusLabel = isStreaming ? "Streaming" : state === "SCANNING" ? "Waiting" : "Blocked";
  const latestReceivedAt = telemetry.latest_received_at
    ? receivedAtFormatter.format(new Date(telemetry.latest_received_at))
    : "None";

  return (
    <section className="panel" aria-labelledby="telemetry-heading">
      <div className="panel-heading">
        <h2 id="telemetry-heading">Live Telemetry</h2>
        <span className={`status ${statusClass}`}>{statusLabel}</span>
      </div>

      <p className="network-note">
        {state === "SCANNING"
          ? "Android telemetry is accepted only while the backend remains SCANNING."
          : "Telemetry is blocked until the Android scanner starts a validated backend scan."}
      </p>

      <div className="metric-grid">
        <div className="metric">
          <span>Samples</span>
          <strong>{sampleCountFormatter.format(telemetry.frame_count)}</strong>
        </div>
        <div className="metric">
          <span>Latest receipt</span>
          <strong>{latestReceivedAt}</strong>
        </div>
        <div className="metric">
          <span>Tracking</span>
          <strong translate="no">{telemetry.latest_sample?.tracking_state ?? "PENDING"}</strong>
        </div>
      </div>

      {telemetry.latest_sample ? (
        <p className="network-note telemetry-detail">
          Latest Android sample{" "}
          <code translate="no">#{telemetry.latest_sample.frame_index}</code> arrived with depth{" "}
          <code translate="no">{telemetry.latest_sample.depth_frame_available ? "available" : "unavailable"}</code> and
          confidence{" "}
          <code translate="no">
            {telemetry.latest_sample.confidence_frame_available ? "available" : "unavailable"}
          </code>
          .
        </p>
      ) : null}
    </section>
  );
}
