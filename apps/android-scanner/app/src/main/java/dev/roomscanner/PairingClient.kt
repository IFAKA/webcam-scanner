package dev.roomscanner

import java.io.BufferedReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.Base64
import org.json.JSONObject

class PairingClient {
    fun pair(apiBaseUrl: String, sessionId: String, pairingToken: String): PairingResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank() || pairingToken.isBlank()) {
            return PairingResult.Failure("Local API URL, session ID, and pairing token are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/pair")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 5_000
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true

            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write("""{"pairing_token":"${jsonEscape(pairingToken.trim())}"}""")
            }

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                PairingResult.Success(
                    networkPaired = response.optBoolean("network_paired", false),
                    rawResponse = responseBody,
                )
            } else {
                PairingResult.Failure(
                    "Pairing failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            PairingResult.Failure("Pairing request failed: ${error.message ?: error.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }

    fun submitCapabilities(
        apiBaseUrl: String,
        sessionId: String,
        report: CapabilityReport,
    ): CapabilitySubmissionResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank()) {
            return CapabilitySubmissionResult.Failure("Local API URL and session ID are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/capabilities")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 5_000
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true

            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write(report.toServerJson().toString())
            }

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                CapabilitySubmissionResult.Success(
                    state = response.optString("state", "UNKNOWN"),
                    canScan = response.optJSONObject("capability_report")?.optBoolean("can_scan", false) == true,
                    rawResponse = responseBody,
                )
            } else {
                CapabilitySubmissionResult.Failure(
                    "Capability report failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            CapabilitySubmissionResult.Failure(
                "Capability report request failed: ${error.message ?: error.javaClass.simpleName}",
            )
        } finally {
            connection?.disconnect()
        }
    }

    fun startScan(apiBaseUrl: String, sessionId: String): ScanStartResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank()) {
            return ScanStartResult.Failure("Local API URL and session ID are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/scan/start")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 5_000
            connection.setRequestProperty("Accept", "application/json")

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                val state = response.optString("state", "UNKNOWN")
                val error = response.optJSONObject("last_error")
                ScanStartResult.Success(
                    state = state,
                    started = state == "SCANNING",
                    errorCode = error?.optString("code"),
                    errorMessage = error?.optString("message"),
                    rawResponse = responseBody,
                )
            } else {
                ScanStartResult.Failure(
                    "Scan start failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            ScanStartResult.Failure("Scan start request failed: ${error.message ?: error.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }

    fun submitTelemetry(
        apiBaseUrl: String,
        sessionId: String,
        sample: ScanTelemetrySample,
    ): TelemetrySubmissionResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank()) {
            return TelemetrySubmissionResult.Failure("Local API URL and session ID are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/telemetry")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 5_000
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true

            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write(sample.toServerJson().toString())
            }

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                val telemetry = response.optJSONObject("telemetry")
                val error = response.optJSONObject("last_error")
                TelemetrySubmissionResult.Success(
                    state = response.optString("state", "UNKNOWN"),
                    frameCount = telemetry?.optInt("frame_count", 0) ?: 0,
                    accepted = error == null,
                    errorCode = error?.optString("code"),
                    errorMessage = error?.optString("message"),
                    rawResponse = responseBody,
                )
            } else {
                TelemetrySubmissionResult.Failure(
                    "Telemetry failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            TelemetrySubmissionResult.Failure("Telemetry request failed: ${error.message ?: error.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }

    fun submitCaptureFrame(
        apiBaseUrl: String,
        sessionId: String,
        metadata: CaptureFrameMetadata,
    ): FrameSubmissionResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank()) {
            return FrameSubmissionResult.Failure("Local API URL and session ID are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/frames")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 5_000
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true

            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write(metadata.toServerJson().toString())
            }

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                val captureFrames = response.optJSONObject("capture_frames")
                val error = response.optJSONObject("last_error")
                FrameSubmissionResult.Success(
                    state = response.optString("state", "UNKNOWN"),
                    persistedCount = captureFrames?.optInt("persisted_count", 0) ?: 0,
                    accepted = error == null,
                    errorCode = error?.optString("code"),
                    errorMessage = error?.optString("message"),
                    rawResponse = responseBody,
                )
            } else {
                FrameSubmissionResult.Failure(
                    "Frame metadata failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            FrameSubmissionResult.Failure("Frame metadata request failed: ${error.message ?: error.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }

    fun submitFrameArtifacts(
        apiBaseUrl: String,
        sessionId: String,
        artifacts: CaptureFrameArtifacts,
    ): FrameArtifactUploadResult {
        if (apiBaseUrl.isBlank() || sessionId.isBlank()) {
            return FrameArtifactUploadResult.Failure("Local API URL and session ID are required.")
        }

        var connection: HttpURLConnection? = null
        return try {
            val baseUrl = apiBaseUrl.trim().trimEnd('/')
            val endpoint = URL("$baseUrl/sessions/${sessionId.trim()}/frames/artifacts")
            connection = endpoint.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 5_000
            connection.readTimeout = 15_000
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true

            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write(artifacts.toServerJson().toString())
            }

            val responseBody = readResponse(connection)
            if (connection.responseCode in 200..299) {
                val response = JSONObject(responseBody)
                val captureFrames = response.optJSONObject("capture_frames")
                val latestFrame = captureFrames?.optJSONObject("latest_frame")
                val processing = response.optJSONObject("processing")
                val error = response.optJSONObject("last_error")
                FrameArtifactUploadResult.Success(
                    state = response.optString("state", "UNKNOWN"),
                    uploaded = latestFrame?.optBoolean("raw_artifacts_uploaded", false) == true && error == null,
                    processingStatus = processing?.optString("status", "BLOCKED") ?: "BLOCKED",
                    errorCode = error?.optString("code"),
                    errorMessage = error?.optString("message"),
                    rawResponse = responseBody,
                )
            } else {
                FrameArtifactUploadResult.Failure(
                    "Frame artifact upload failed with HTTP ${connection.responseCode}: $responseBody",
                )
            }
        } catch (error: Exception) {
            FrameArtifactUploadResult.Failure(
                "Frame artifact upload request failed: ${error.message ?: error.javaClass.simpleName}",
            )
        } finally {
            connection?.disconnect()
        }
    }

    private fun CapabilityReport.toServerJson(): JSONObject =
        JSONObject()
            .put("device_model", deviceModel)
            .put("arcore_supported", arcoreSupported)
            .put("depth_supported", depthSupported)
            .put("raw_depth_available", rawDepthAvailable)
            .put("confidence_available", confidenceAvailable)
            .put("tracking_available", trackingAvailable)
            .put("camera_permission", cameraPermission)
            .put("network_paired", networkPaired)
            .put("can_scan", canScan)

    private fun ScanTelemetrySample.toServerJson(): JSONObject =
        JSONObject()
            .put("frame_index", frameIndex)
            .put("tracking_state", trackingState)
            .put("monotonic_timestamp_ms", monotonicTimestampMs)
            .put("camera_position_m", cameraPositionM?.toJsonArray() ?: JSONObject.NULL)
            .put("camera_rotation_quaternion", cameraRotationQuaternion?.toJsonArray() ?: JSONObject.NULL)
            .put("depth_frame_available", depthFrameAvailable)
            .put("confidence_frame_available", confidenceFrameAvailable)

    private fun CaptureFrameMetadata.toServerJson(): JSONObject =
        JSONObject()
            .put("frame_index", frameIndex)
            .put("tracking_state", trackingState)
            .put("monotonic_timestamp_ms", monotonicTimestampMs)
            .put("camera_position_m", cameraPositionM?.toJsonArray() ?: JSONObject.NULL)
            .put("camera_rotation_quaternion", cameraRotationQuaternion?.toJsonArray() ?: JSONObject.NULL)
            .put("depth_frame_available", depthFrameAvailable)
            .put("confidence_frame_available", confidenceFrameAvailable)
            .put("color_image_filename", colorImageFilename ?: JSONObject.NULL)
            .put("depth_filename", depthFilename ?: JSONObject.NULL)
            .put("confidence_filename", confidenceFilename ?: JSONObject.NULL)

    private fun CaptureFrameArtifacts.toServerJson(): JSONObject =
        JSONObject()
            .put("frame_index", frameIndex)
            .put("color_image", colorImage.toServerJson())
            .put("raw_depth", rawDepth.toServerJson())
            .put("confidence", confidence.toServerJson())

    private fun CaptureArtifactPayload.toServerJson(): JSONObject =
        JSONObject()
            .put("filename", filename)
            .put("content_base64", Base64.getEncoder().encodeToString(bytes))
            .put("media_type", mediaType ?: JSONObject.NULL)
            .put("sha256", sha256 ?: bytes.sha256())

    private fun ByteArray.sha256(): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(this)
        return digest.joinToString(separator = "") { byte -> "%02x".format(byte) }
    }

    private fun FloatArray.toJsonArray(): org.json.JSONArray {
        val array = org.json.JSONArray()
        forEach { array.put(it.toDouble()) }
        return array
    }

    private fun readResponse(connection: HttpURLConnection): String {
        val stream = if (connection.responseCode in 200..299) {
            connection.inputStream
        } else {
            connection.errorStream ?: connection.inputStream
        }
        return BufferedReader(stream.reader(Charsets.UTF_8)).use { it.readText() }
    }

    private fun jsonEscape(value: String): String =
        value.replace("\\", "\\\\").replace("\"", "\\\"")
}

sealed class PairingResult {
    data class Success(val networkPaired: Boolean, val rawResponse: String) : PairingResult()
    data class Failure(val message: String) : PairingResult()
}

sealed class CapabilitySubmissionResult {
    data class Success(val state: String, val canScan: Boolean, val rawResponse: String) : CapabilitySubmissionResult()
    data class Failure(val message: String) : CapabilitySubmissionResult()
}

sealed class ScanStartResult {
    data class Success(
        val state: String,
        val started: Boolean,
        val errorCode: String?,
        val errorMessage: String?,
        val rawResponse: String,
    ) : ScanStartResult()

    data class Failure(val message: String) : ScanStartResult()
}

sealed class TelemetrySubmissionResult {
    data class Success(
        val state: String,
        val frameCount: Int,
        val accepted: Boolean,
        val errorCode: String?,
        val errorMessage: String?,
        val rawResponse: String,
    ) : TelemetrySubmissionResult()

    data class Failure(val message: String) : TelemetrySubmissionResult()
}

sealed class FrameSubmissionResult {
    data class Success(
        val state: String,
        val persistedCount: Int,
        val accepted: Boolean,
        val errorCode: String?,
        val errorMessage: String?,
        val rawResponse: String,
    ) : FrameSubmissionResult()

    data class Failure(val message: String) : FrameSubmissionResult()
}

sealed class FrameArtifactUploadResult {
    data class Success(
        val state: String,
        val uploaded: Boolean,
        val processingStatus: String,
        val errorCode: String?,
        val errorMessage: String?,
        val rawResponse: String,
    ) : FrameArtifactUploadResult()

    data class Failure(val message: String) : FrameArtifactUploadResult()
}
