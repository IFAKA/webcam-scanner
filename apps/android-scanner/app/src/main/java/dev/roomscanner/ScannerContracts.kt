package dev.roomscanner

enum class ScannerErrorCode {
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

data class CapabilityReport(
    val deviceModel: String,
    val arcoreSupported: Boolean,
    val depthSupported: Boolean,
    val rawDepthAvailable: Boolean,
    val confidenceAvailable: Boolean,
    val trackingAvailable: Boolean,
    val cameraPermission: Boolean,
    val networkPaired: Boolean,
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
