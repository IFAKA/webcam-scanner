package dev.roomscanner

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.ActivityCompat
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session

class CapabilityGate(private val activity: Activity) {
    fun evaluate(isNetworkPaired: Boolean): Pair<CapabilityReport, ScannerError?> {
        val hasCameraPermission = ActivityCompat.checkSelfPermission(
            activity,
            Manifest.permission.CAMERA,
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasCameraPermission) {
            return blocked(isNetworkPaired, ScannerErrorCode.PERMISSION_CAMERA_DENIED)
        }

        val availability = ArCoreApk.getInstance().checkAvailability(activity)
        if (!availability.isSupported) {
            return blocked(isNetworkPaired, ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED)
        }

        return try {
            val session = Session(activity)
            val hasRawDepth = session.isDepthModeSupported(Config.DepthMode.RAW_DEPTH_ONLY)
            session.close()

            if (!hasRawDepth) {
                blocked(isNetworkPaired, ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED)
            } else if (!isNetworkPaired) {
                blocked(isNetworkPaired, ScannerErrorCode.NETWORK_PAIRING_FAILED)
            } else {
                val report = CapabilityReport(
                    deviceModel = Build.MODEL,
                    arcoreSupported = true,
                    depthSupported = true,
                    rawDepthAvailable = true,
                    confidenceAvailable = true,
                    trackingAvailable = true,
                    cameraPermission = true,
                    networkPaired = true,
                )
                Pair(report, null)
            }
        } catch (error: Exception) {
            blocked(isNetworkPaired, ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE)
        }
    }

    private fun blocked(
        isNetworkPaired: Boolean,
        code: ScannerErrorCode,
    ): Pair<CapabilityReport, ScannerError> {
        val report = CapabilityReport(
            deviceModel = Build.MODEL,
            arcoreSupported = code != ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED,
            depthSupported = code != ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED,
            rawDepthAvailable = code != ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE,
            confidenceAvailable = code != ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE,
            trackingAvailable = code != ScannerErrorCode.DEVICE_TRACKING_NOT_READY,
            cameraPermission = code != ScannerErrorCode.PERMISSION_CAMERA_DENIED,
            networkPaired = isNetworkPaired,
        )
        return Pair(
            report,
            ScannerError(
                code = code,
                message = messageFor(code),
                stage = "device_check",
                recoverable = false,
            ),
        )
    }

    private fun messageFor(code: ScannerErrorCode): String = when (code) {
        ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED -> "ARCore is unavailable on this device."
        ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED -> "ARCore Depth is unavailable on this device."
        ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE -> "Raw depth frames are unavailable."
        ScannerErrorCode.DEVICE_TRACKING_NOT_READY -> "AR tracking is not ready."
        ScannerErrorCode.PERMISSION_CAMERA_DENIED -> "Camera permission is required."
        ScannerErrorCode.NETWORK_PAIRING_FAILED -> "Pair with the laptop before scanning."
        else -> "Scanning is blocked by a local error."
    }
}
