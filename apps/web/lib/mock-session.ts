import type { SessionSnapshot } from "./contracts";

export const mockSession: SessionSnapshot = {
  session_id: "local-preview",
  state: "FAILED",
  network_paired: true,
  last_error: {
    code: "DEVICE_DEPTH_UNSUPPORTED",
    message: "This device cannot scan because ARCore Depth is unavailable.",
    stage: "device_check",
    recoverable: false,
    details: {},
    timestamp: new Date().toISOString(),
    session_id: "local-preview",
  },
  capability_report: {
    device_model: "Redmi Note 14 5G",
    arcore_supported: true,
    depth_supported: false,
    raw_depth_available: false,
    confidence_available: false,
    tracking_available: true,
    camera_permission: true,
    network_paired: true,
    can_scan: false,
    failure_reason: null,
  },
};
