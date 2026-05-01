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
            "READY\n${report.deviceModel}\nAll required scanner capabilities passed."
        } else {
            "SCAN BLOCKED\n${error.code}\n${error.message}"
        }
    }
}
