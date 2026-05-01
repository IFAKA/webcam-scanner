package dev.roomscanner

enum class ScannerErrorCode {
    SESSION_NOT_READY_FOR_SCAN,
    SESSION_NOT_SCANNING_FOR_TELEMETRY,
    SESSION_NOT_SCANNING_FOR_FRAME_CAPTURE,
    DEVICE_ARCORE_UNSUPPORTED,
    DEVICE_DEPTH_UNSUPPORTED,
    DEVICE_RAW_DEPTH_UNAVAILABLE,
    DEVICE_TRACKING_NOT_READY,
    PERMISSION_CAMERA_DENIED,
    NETWORK_PAIRING_FAILED,
    NETWORK_WEBSOCKET_DROPPED,
    UPLOAD_INCOMPLETE,
    SESSION_SCHEMA_INVALID,
    PROCESSING_POINT_CLOUD_FAILED,
    PROCESSING_PLANE_FIT_FAILED,
    GEOMETRY_POLYGON_INVALID,
    EXPORT_FAILED,
    UNKNOWN_INTERNAL_ERROR
}

data class ScannerError(
    val code: ScannerErrorCode,
    val message: String,
    val stage: String,
    val recoverable: Boolean,
)

data class DeviceIdentity(
    val manufacturer: String,
    val brand: String,
    val model: String,
    val device: String,
    val product: String,
    val androidSdk: Int,
) {
    val displayName: String
        get() = listOf(manufacturer, model)
            .filter { it.isNotBlank() }
            .joinToString(" ")
}

data class CapabilityCheck(
    val name: String,
    val passed: Boolean,
    val message: String,
)

data class CapabilityReport(
    val deviceModel: String,
    val deviceIdentity: DeviceIdentity,
    val arcoreSupported: Boolean,
    val depthSupported: Boolean,
    val rawDepthAvailable: Boolean,
    val confidenceAvailable: Boolean,
    val trackingAvailable: Boolean,
    val cameraPermission: Boolean,
    val networkPaired: Boolean,
    val checks: List<CapabilityCheck>,
) {
    val canScan: Boolean
        get() = arcoreSupported &&
            depthSupported &&
            rawDepthAvailable &&
            confidenceAvailable &&
            trackingAvailable &&
            cameraPermission &&
            networkPaired
}

data class ScanTelemetrySample(
    val frameIndex: Int,
    val trackingState: String,
    val monotonicTimestampMs: Long,
    val cameraPositionM: FloatArray? = null,
    val cameraRotationQuaternion: FloatArray? = null,
    val depthFrameAvailable: Boolean,
    val confidenceFrameAvailable: Boolean,
)

data class CaptureFrameMetadata(
    val frameIndex: Int,
    val trackingState: String,
    val monotonicTimestampMs: Long,
    val cameraPositionM: FloatArray? = null,
    val cameraRotationQuaternion: FloatArray? = null,
    val depthFrameAvailable: Boolean,
    val confidenceFrameAvailable: Boolean,
    val colorImageFilename: String? = null,
    val depthFilename: String? = null,
    val confidenceFilename: String? = null,
)
