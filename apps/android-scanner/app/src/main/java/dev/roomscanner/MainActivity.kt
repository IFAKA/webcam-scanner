package dev.roomscanner

import android.Manifest
import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.app.ActivityCompat

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var startButton: Button
    private lateinit var gate: CapabilityGate

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
        startButton = Button(this).apply {
            text = "Start Scan"
            isEnabled = false
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_VERTICAL
            addView(status)
            addView(startButton)
        }
        setContentView(root)
    }

    private fun updateCapabilityState() {
        val (report, error) = gate.evaluate(isNetworkPaired = false)
        startButton.isEnabled = report.canScan
        status.text = if (error == null) {
            buildStatus("READY", report, "All required scanner capabilities passed.")
        } else {
            buildStatus("SCAN BLOCKED", report, "${error.code}\n${error.message}")
        }
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
}
