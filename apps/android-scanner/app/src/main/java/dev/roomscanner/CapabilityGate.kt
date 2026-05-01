package dev.roomscanner

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Build
import androidx.core.app.ActivityCompat
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session

class CapabilityGate(private val activity: Activity) {
    fun evaluate(isNetworkPaired: Boolean): Pair<CapabilityReport, ScannerError?> {
        val identity = currentIdentity()
        val checks = mutableListOf<CapabilityCheck>()
        val hasCameraPermission = ActivityCompat.checkSelfPermission(
            activity,
            Manifest.permission.CAMERA,
        ) == PackageManager.PERMISSION_GRANTED
        checks += CapabilityCheck(
            name = "Camera permission",
            passed = hasCameraPermission,
            message = if (hasCameraPermission) {
                "Camera access granted."
            } else {
                "Camera permission is required before scanner validation can continue."
            },
        )

        if (!hasCameraPermission) {
            return blocked(
                identity,
                isNetworkPaired,
                checks,
                ScannerErrorCode.PERMISSION_CAMERA_DENIED,
            )
        }

        val availability = ArCoreApk.getInstance().checkAvailability(activity)
        val arcoreReady = availability == ArCoreApk.Availability.SUPPORTED_INSTALLED
        checks += CapabilityCheck(
            name = "ARCore installed",
            passed = arcoreReady,
            message = when {
                arcoreReady -> "Google Play Services for AR is installed and ready."
                availability.isSupported -> "ARCore is supported but is not installed or needs an update."
                availability.isTransient -> "ARCore support is still being checked by the system."
                else -> "ARCore is not supported on this device."
            },
        )
        if (!arcoreReady) {
            return blocked(
                identity,
                isNetworkPaired,
                checks,
                ScannerErrorCode.DEVICE_ARCORE_UNSUPPORTED,
            )
        }

        val sensorsReady = hasMotionSensors()
        checks += CapabilityCheck(
            name = "Motion sensors",
            passed = sensorsReady,
            message = if (sensorsReady) {
                "Accelerometer and gyroscope are available for AR tracking."
            } else {
                "Accelerometer and gyroscope are required for stable AR tracking."
            },
        )
        if (!sensorsReady) {
            return blocked(
                identity,
                isNetworkPaired,
                checks,
                ScannerErrorCode.DEVICE_TRACKING_NOT_READY,
            )
        }

        return try {
            val session = Session(activity)
            val hasRawDepth = session.isDepthModeSupported(Config.DepthMode.RAW_DEPTH_ONLY)
            session.close()
            checks += CapabilityCheck(
                name = "Raw depth",
                passed = hasRawDepth,
                message = if (hasRawDepth) {
                    "ARCore Raw Depth mode is supported."
                } else {
                    "ARCore Raw Depth mode is required for room-boundary scanning."
                },
            )

            if (!hasRawDepth) {
                blocked(identity, isNetworkPaired, checks, ScannerErrorCode.DEVICE_DEPTH_UNSUPPORTED)
            } else if (!isNetworkPaired) {
                checks += CapabilityCheck(
                    name = "Laptop pairing",
                    passed = false,
                    message = "Pair with the local laptop server before scanning.",
                )
                blocked(identity, isNetworkPaired, checks, ScannerErrorCode.NETWORK_PAIRING_FAILED)
            } else {
                checks += CapabilityCheck(
                    name = "Laptop pairing",
                    passed = true,
                    message = "Phone is paired with the local laptop server.",
                )
                val report = CapabilityReport(
                    deviceModel = identity.model,
                    deviceIdentity = identity,
                    arcoreSupported = true,
                    depthSupported = true,
                    rawDepthAvailable = true,
                    confidenceAvailable = true,
                    trackingAvailable = true,
                    cameraPermission = true,
                    networkPaired = true,
                    checks = checks,
                )
                Pair(report, null)
            }
        } catch (error: Exception) {
            checks += CapabilityCheck(
                name = "ARCore session",
                passed = false,
                message = "ARCore session could not be created for raw depth validation.",
            )
            blocked(identity, isNetworkPaired, checks, ScannerErrorCode.DEVICE_RAW_DEPTH_UNAVAILABLE)
        }
    }

    private fun blocked(
        identity: DeviceIdentity,
        isNetworkPaired: Boolean,
        checks: List<CapabilityCheck>,
        code: ScannerErrorCode,
    ): Pair<CapabilityReport, ScannerError> {
        val cameraReady = hasPassed(checks, "Camera permission")
        val arcoreReady = hasPassed(checks, "ARCore installed")
        val depthReady = hasPassed(checks, "Raw depth")
        val trackingReady = hasPassed(checks, "Motion sensors")
        val report = CapabilityReport(
            deviceModel = identity.model,
            deviceIdentity = identity,
            arcoreSupported = arcoreReady,
            depthSupported = depthReady,
            rawDepthAvailable = depthReady,
            confidenceAvailable = depthReady,
            trackingAvailable = trackingReady,
            cameraPermission = cameraReady,
            networkPaired = isNetworkPaired,
            checks = checks,
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

    private fun currentIdentity(): DeviceIdentity = DeviceIdentity(
        manufacturer = Build.MANUFACTURER.orEmpty(),
        brand = Build.BRAND.orEmpty(),
        model = Build.MODEL.orEmpty(),
        device = Build.DEVICE.orEmpty(),
        product = Build.PRODUCT.orEmpty(),
        androidSdk = Build.VERSION.SDK_INT,
    )

    private fun hasMotionSensors(): Boolean {
        val sensorManager = activity.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        return sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) != null &&
            sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE) != null
    }

    private fun hasPassed(checks: List<CapabilityCheck>, name: String): Boolean =
        checks.firstOrNull { it.name == name }?.passed == true

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
