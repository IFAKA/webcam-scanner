package dev.roomscanner

import android.Manifest
import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.app.ActivityCompat

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var startButton: Button
    private lateinit var pairButton: Button
    private lateinit var apiBaseUrlInput: EditText
    private lateinit var sessionIdInput: EditText
    private lateinit var pairingTokenInput: EditText
    private lateinit var gate: CapabilityGate
    private val pairingClient = PairingClient()
    private var isNetworkPaired = false
    private var backendReadyForScan = false
    private var isScanStarted = false
    private var pairingStatus = "Pair with the local laptop server before scanning."

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        gate = CapabilityGate(this)
        render()
        ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), 10)
    }

    override fun onResume() {
        super.onResume()
        updateCapabilityState()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        updateCapabilityState()
    }

    private fun render() {
        status = TextView(this).apply {
            textSize = 16f
            setPadding(32, 32, 32, 16)
        }
        apiBaseUrlInput = EditText(this).apply {
            hint = "Phone API URL from desktop, e.g. http://192.168.1.20:8000"
            setSingleLine(true)
        }
        sessionIdInput = EditText(this).apply {
            hint = "Session ID from desktop"
            setSingleLine(true)
        }
        pairingTokenInput = EditText(this).apply {
            hint = "Pairing token from desktop"
            setSingleLine(true)
        }
        pairButton = Button(this).apply {
            text = "Pair Laptop"
            setOnClickListener { pairWithLaptop() }
        }
        startButton = Button(this).apply {
            text = "Start Scan"
            isEnabled = false
            setOnClickListener { startBackendScan() }
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(32, 32, 32, 32)
            addView(status)
            addView(apiBaseUrlInput)
            addView(sessionIdInput)
            addView(pairingTokenInput)
            addView(pairButton)
            addView(startButton)
        }
        setContentView(root)
    }

    private fun updateCapabilityState() {
        val (report, error) = gate.evaluate(isNetworkPaired = isNetworkPaired)
        startButton.isEnabled = report.canScan && backendReadyForScan && !isScanStarted
        status.text = if (isScanStarted) {
            buildStatus("SCANNING", report, pairingStatus)
        } else if (error == null && backendReadyForScan) {
            buildStatus("READY", report, pairingStatus)
        } else {
            val localBlock = if (error == null) {
                "Backend has not accepted this session as READY yet."
            } else {
                "${error.code}\n${error.message}"
            }
            buildStatus("SCAN BLOCKED", report, "$localBlock\n$pairingStatus")
        }
    }

    private fun pairWithLaptop() {
        pairButton.isEnabled = false
        pairingStatus = "Pairing with local laptop server..."
        updateCapabilityState()

        val apiBaseUrl = apiBaseUrlInput.text.toString()
        val sessionId = sessionIdInput.text.toString()
        val pairingToken = pairingTokenInput.text.toString()

        Thread {
            val result = pairingClient.pair(
                apiBaseUrl = apiBaseUrl,
                sessionId = sessionId,
                pairingToken = pairingToken,
            )
            val capabilityStatus = if (result is PairingResult.Success && result.networkPaired) {
                submitCapabilityReport(apiBaseUrl, sessionId)
            } else {
                null
            }

            runOnUiThread {
                when (result) {
                    is PairingResult.Success -> {
                        isNetworkPaired = result.networkPaired && capabilityStatus?.backendAccepted != false
                        backendReadyForScan = capabilityStatus?.backendReadyForScan == true
                        isScanStarted = false
                        pairingStatus = if (result.networkPaired) {
                            capabilityStatus?.message
                                ?: "Phone is paired, but capability reporting did not run."
                        } else {
                            "Pairing endpoint responded, but backend did not mark this session paired."
                        }
                    }
                    is PairingResult.Failure -> {
                        isNetworkPaired = false
                        backendReadyForScan = false
                        isScanStarted = false
                        pairingStatus = result.message
                    }
                }
                pairButton.isEnabled = true
                updateCapabilityState()
            }
        }.start()
    }

    private fun submitCapabilityReport(apiBaseUrl: String, sessionId: String): CapabilitySubmissionStatus {
        val (report, _) = gate.evaluate(isNetworkPaired = true)
        return when (
            val result = pairingClient.submitCapabilities(
                apiBaseUrl = apiBaseUrl,
                sessionId = sessionId,
                report = report,
            )
        ) {
            is CapabilitySubmissionResult.Success -> {
                if (result.canScan) {
                    CapabilitySubmissionStatus(
                        backendAccepted = true,
                        backendReadyForScan = result.state == "READY",
                        message = "Phone is paired. Capability report accepted; backend state is ${result.state}.",
                    )
                } else {
                    CapabilitySubmissionStatus(
                        backendAccepted = true,
                        backendReadyForScan = false,
                        message = "Phone is paired. Capability report accepted; backend blocked scanning in ${result.state}.",
                    )
                }
            }
            is CapabilitySubmissionResult.Failure -> {
                CapabilitySubmissionStatus(
                    backendAccepted = false,
                    backendReadyForScan = false,
                    message = result.message,
                )
            }
        }
    }

    private fun startBackendScan() {
        startButton.isEnabled = false
        pairingStatus = "Requesting backend scan start..."
        updateCapabilityState()

        val apiBaseUrl = apiBaseUrlInput.text.toString()
        val sessionId = sessionIdInput.text.toString()

        Thread {
            val result = pairingClient.startScan(apiBaseUrl = apiBaseUrl, sessionId = sessionId)

            runOnUiThread {
                when (result) {
                    is ScanStartResult.Success -> {
                        isScanStarted = result.started
                        backendReadyForScan = result.state == "READY" || result.started
                        pairingStatus = if (result.started) {
                            "Backend accepted scan start; session state is ${result.state}."
                        } else {
                            val reason = listOfNotNull(result.errorCode, result.errorMessage).joinToString(": ")
                            "Backend blocked scan start in ${result.state}. $reason"
                        }
                    }
                    is ScanStartResult.Failure -> {
                        isScanStarted = false
                        pairingStatus = result.message
                    }
                }
                updateCapabilityState()
            }
        }.start()
    }

    private fun buildStatus(
        headline: String,
        report: CapabilityReport,
        message: String,
    ): String {
        val identity = report.deviceIdentity
        val checks = report.checks.joinToString(separator = "\n") { check ->
            val marker = if (check.passed) "PASS" else "BLOCKED"
            "$marker ${check.name}: ${check.message}"
        }

        return """
            $headline
            $message

            Expected scanner: Redmi Note 14 5G
            Observed device: ${identity.displayName}
            Brand: ${identity.brand}
            Device: ${identity.device}
            Product: ${identity.product}
            Android SDK: ${identity.androidSdk}

            $checks
        """.trimIndent()
    }

    private data class CapabilitySubmissionStatus(
        val backendAccepted: Boolean,
        val backendReadyForScan: Boolean,
        val message: String,
    )
}
