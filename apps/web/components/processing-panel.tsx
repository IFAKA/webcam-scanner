import type { ProcessingSummary, ScanState } from "../lib/contracts";

const numberFormatter = new Intl.NumberFormat("en-US");

export function ProcessingPanel({
  state,
  processing,
  canStartProcessing,
  isStarting,
  onStartProcessing,
}: {
  state: ScanState;
  processing: ProcessingSummary;
  canStartProcessing: boolean;
  isStarting?: boolean;
  onStartProcessing?: () => void;
}) {
  const isReady = processing.status === "READY_FOR_REVIEW";
  const statusClass = isReady ? "ok" : processing.status === "READY_TO_PROCESS" || processing.status === "PROCESSING" ? "wait" : "fail";
  const actionDisabled = !canStartProcessing || isStarting;
  const artifactLabel =
    processing.available_artifacts.length > 0 ? processing.available_artifacts.join(", ") : "None confirmed";

  return (
    <section className="panel" aria-labelledby="processing-heading">
      <div className="panel-heading">
        <h2 id="processing-heading">Room Geometry</h2>
        <span className={`status ${statusClass}`}>{processing.status.replaceAll("_", " ")}</span>
      </div>

      <p className={processing.blocked_reason ? "network-note error" : "network-note"} role="status">
        {processing.blocked_reason
          ? `Processing is blocked: ${processing.blocked_reason}.`
          : "Processing produced review geometry from uploaded scan artifacts."}
      </p>

      <div className="metric-grid">
        <div className="metric">
          <span>Input frames</span>
          <strong>{numberFormatter.format(processing.input_frame_count)}</strong>
        </div>
        <div className="metric">
          <span>Artifacts</span>
          <strong>{artifactLabel}</strong>
        </div>
        <div className="metric">
          <span>Review geometry</span>
          <strong>{processing.geometry ? "Available" : "Not generated"}</strong>
        </div>
      </div>

      {onStartProcessing ? (
        <button className="primary-action" type="button" disabled={actionDisabled} onClick={onStartProcessing}>
          {isStarting ? "Checking upload" : "Start processing"}
        </button>
      ) : null}

      {processing.geometry ? (
        <p className="network-note telemetry-detail">
          Geometry from <code translate="no">{numberFormatter.format(processing.geometry.source_frame_count)}</code>{" "}
          frames is stored in <code translate="no">{processing.geometry.output_path}</code>.
        </p>
      ) : (
        <p className="network-note telemetry-detail">
          Raw RGB, raw depth, and confidence files must be uploaded before the backend can generate a reviewable room boundary.
          Current session state is <code translate="no">{state}</code>.
        </p>
      )}
    </section>
  );
}
