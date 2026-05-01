import type { CapabilityReport, ScannerError } from "../lib/contracts";

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
}: {
  report: CapabilityReport | null;
  lastError: ScannerError | null;
}) {
  return (
    <section className="panel">
      <h2>Device Gate</h2>
      <span className={`status ${report?.can_scan ? "ok" : "fail"}`}>
        {report?.can_scan ? "Ready to scan" : "Scan blocked"}
      </span>

      <div className="checklist">
        {checks.map(([key, label]) => {
          const isPassing = Boolean(report?.[key]);
          return (
            <div className="check" key={key}>
              <span>{label}</span>
              <strong>{isPassing ? "PASS" : "FAIL"}</strong>
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
