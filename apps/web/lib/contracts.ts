export type ScanState =
  | "CREATED"
  | "PAIRING"
  | "DEVICE_CHECKING"
  | "READY"
  | "SCANNING"
  | "CAPTURE_COMPLETE"
  | "UPLOADING"
  | "PROCESSING"
  | "READY_FOR_REVIEW"
  | "EXPORTED"
  | "FAILED";

export type ScannerErrorCode =
  | "SESSION_NOT_READY_FOR_SCAN"
  | "SESSION_NOT_SCANNING_FOR_TELEMETRY"
  | "SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE"
  | "DEVICE_ARCORE_UNSUPPORTED"
  | "DEVICE_DEPTH_UNSUPPORTED"
  | "DEVICE_RAW_DEPTH_UNAVAILABLE"
  | "DEVICE_TRACKING_NOT_READY"
  | "PERMISSION_CAMERA_DENIED"
  | "NETWORK_PAIRING_FAILED"
  | "NETWORK_WEBSOCKET_DROPPED"
  | "UPLOAD_INCOMPLETE"
  | "SESSION_SCHEMA_INVALID"
  | "PROCESSING_POINT_CLOUD_FAILED"
  | "PROCESSING_PLANE_FIT_FAILED"
  | "GEOMETRY_POLYGON_INVALID"
  | "EXPORT_FAILED"
  | "UNKNOWN_INTERNAL_ERROR";

export type ScannerError = {
  code: ScannerErrorCode;
  message: string;
  stage: string;
  recoverable: boolean;
  details: Record<string, unknown>;
  timestamp: string;
  session_id: string | null;
};

export type CapabilityReport = {
  device_model: string;
  arcore_supported: boolean;
  depth_supported: boolean;
  raw_depth_available: boolean;
  confidence_available: boolean;
  tracking_available: boolean;
  camera_permission: boolean;
  network_paired: boolean;
  can_scan: boolean;
  failure_reason: ScannerError | null;
};

export type LocalNetworkConfig = {
  api_base_url: string;
  websocket_base_url: string;
  host: string;
  port: number;
  detected_interface: string;
  is_loopback: boolean;
};

export type CreateSessionResponse = {
  session_id: string;
  pairing_token: string;
  state: ScanState;
  websocket_path: string;
  network_config: LocalNetworkConfig;
};

export type ScanTelemetrySample = {
  frame_index: number;
  tracking_state: string;
  monotonic_timestamp_ms: number;
  camera_position_m: [number, number, number] | null;
  camera_rotation_quaternion: [number, number, number, number] | null;
  depth_frame_available: boolean;
  confidence_frame_available: boolean;
};

export type TelemetrySummary = {
  frame_count: number;
  latest_sample: ScanTelemetrySample | null;
  latest_received_at: string | null;
};

export type CaptureFrameMetadata = {
  frame_index: number;
  tracking_state: string;
  monotonic_timestamp_ms: number;
  camera_position_m: [number, number, number] | null;
  camera_rotation_quaternion: [number, number, number, number] | null;
  depth_frame_available: boolean;
  confidence_frame_available: boolean;
  color_image_filename: string | null;
  depth_filename: string | null;
  confidence_filename: string | null;
};

export type CaptureFrameRecord = {
  frame_id: string;
  metadata: CaptureFrameMetadata;
  received_at: string;
  metadata_path: string;
  raw_artifacts_uploaded: boolean;
};

export type CaptureFrameSummary = {
  persisted_count: number;
  latest_frame: CaptureFrameRecord | null;
  manifest_path: string | null;
};

export type ProcessingStatus =
  | "BLOCKED"
  | "READY_TO_PROCESS"
  | "PROCESSING"
  | "READY_FOR_REVIEW"
  | "FAILED";

export type RoomGeometry = {
  generated_at: string;
  source_frame_count: number;
  floor_outline_m: [number, number][];
  output_path: string;
};

export type ProcessingSummary = {
  status: ProcessingStatus;
  input_frame_count: number;
  required_artifacts: string[];
  available_artifacts: string[];
  blocked_reason: string | null;
  geometry: RoomGeometry | null;
};

export type SessionSnapshot = {
  session_id: string;
  state: ScanState;
  last_error: ScannerError | null;
  capability_report: CapabilityReport | null;
  network_paired: boolean;
  network_config: LocalNetworkConfig | null;
  telemetry: TelemetrySummary;
  capture_frames: CaptureFrameSummary;
  processing: ProcessingSummary;
};
