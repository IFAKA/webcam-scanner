import type { CaptureFrameSummary, ScanState } from "../lib/contracts";

const frameCountFormatter = new Intl.NumberFormat("en-US");
const receivedAtFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});
const byteFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

export function FrameManifestPanel({
  state,
  captureFrames,
}: {
  state: ScanState;
  captureFrames: CaptureFrameSummary;
}) {
  const hasFrames = captureFrames.persisted_count > 0;
  const statusClass = hasFrames ? "ok" : state === "SCANNING" ? "wait" : "fail";
  const statusLabel = hasFrames ? "Persisting" : state === "SCANNING" ? "Waiting" : "Blocked";
  const latestFrame = captureFrames.latest_frame;
  const latestReceipt = latestFrame ? receivedAtFormatter.format(new Date(latestFrame.received_at)) : "None";
  const artifactEntries = latestFrame ? Object.entries(latestFrame.artifacts) : [];
  const uploadedBytes = artifactEntries.reduce((total, [, artifact]) => total + artifact.byte_size, 0);

  return (
    <section className="panel" aria-labelledby="frame-manifest-heading">
      <div className="panel-heading">
        <h2 id="frame-manifest-heading">Frame Manifest</h2>
        <span className={`status ${statusClass}`}>{statusLabel}</span>
      </div>

      <p className="network-note">
        {state === "SCANNING"
          ? "Android frame metadata is persisted locally for the upload package. Raw RGB, raw depth, and confidence files are tracked separately."
          : "Frame metadata is blocked until the backend session is SCANNING."}
      </p>

      <div className="metric-grid">
        <div className="metric">
          <span>Persisted frames</span>
          <strong>{frameCountFormatter.format(captureFrames.persisted_count)}</strong>
        </div>
        <div className="metric">
          <span>Latest receipt</span>
          <strong>{latestReceipt}</strong>
        </div>
        <div className="metric">
          <span>Raw files</span>
          <strong>{latestFrame?.raw_artifacts_uploaded ? "Uploaded" : "Pending"}</strong>
        </div>
        <div className="metric">
          <span>Uploaded bytes</span>
          <strong>{byteFormatter.format(uploadedBytes)}</strong>
        </div>
      </div>

      {latestFrame ? (
        <p className="network-note telemetry-detail">
          Latest frame <code translate="no">#{latestFrame.metadata.frame_index}</code> is stored in{" "}
          <code translate="no">{latestFrame.metadata_path}</code> with tracking{" "}
          <code translate="no">{latestFrame.metadata.tracking_state}</code>.
        </p>
      ) : null}

      {artifactEntries.length > 0 ? (
        <ul className="artifact-list" aria-label="Latest frame raw artifacts">
          {artifactEntries.map(([name, artifact]) => (
            <li key={name}>
              <span>{name.replaceAll("_", " ")}</span>
              <code translate="no">{artifact.filename}</code>
              <span>{byteFormatter.format(artifact.byte_size)} bytes</span>
            </li>
          ))}
        </ul>
      ) : latestFrame ? (
        <p className="network-note telemetry-detail error">
          Latest frame metadata is stored, but raw artifact upload has not completed for this frame.
        </p>
      ) : null}
    </section>
  );
}
