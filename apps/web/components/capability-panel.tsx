import type { CapabilityReport, ScannerError, ScanState } from "../lib/contracts";

const checks: Array<[keyof CapabilityReport, string]> = [
  ["camera_permission", "Camera permission"],
  ["arcore_supported", "ARCore supported"],
  ["depth_supported", "Depth API supported"],
  ["raw_depth_available", "Raw depth available"],
  ["confidence_available", "Confidence frame available"],
  ["tracking_available", "Tracking ready"],
  ["network_paired", "Laptop paired"],
];

export function CapabilityPanel({
  report,
  lastError,
  state,
}: {
  report: CapabilityReport | null;
  lastError: ScannerError | null;
  state: ScanState;
}) {
  const statusClass = state === "SCANNING" || report?.can_scan ? "ok" : report ? "fail" : "wait";
  const statusLabel = state === "SCANNING"
    ? "Scanning"
    : report?.can_scan
      ? "Ready to scan"
      : report
        ? "Scan blocked"
        : "Waiting for report";

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Device Gate</h2>
        <span className={`status ${statusClass}`}>{statusLabel}</span>
      </div>

      {!report ? (
        <p className="network-note">
          Backend state is <code translate="no">{state}</code>. Scanning remains blocked until the Android scanner pairs
          and submits a capability report.
        </p>
      ) : null}

      {report?.can_scan && state === "READY" ? (
        <p className="network-note">
          Backend state is <code translate="no">READY</code>. The Android scanner can now request scan start.
        </p>
      ) : null}

      {state === "SCANNING" ? (
        <p className="network-note">
          Backend state is <code translate="no">SCANNING</code>. Capture has started from a validated Android request.
        </p>
      ) : null}

      <div className="checklist">
        {checks.map(([key, label]) => {
          const isKnown = report !== null;
          const isPassing = Boolean(report?.[key]);
          return (
            <div className="check" key={key}>
              <span>{label}</span>
              <strong>{isKnown ? (isPassing ? "PASS" : "FAIL") : "PENDING"}</strong>
            </div>
          );
        })}
      </div>

      {lastError ? (
        <div className="error">
          <strong>{lastError.code}</strong>
          <p>{lastError.message}</p>
        </div>
      ) : null}
    </section>
  );
}
