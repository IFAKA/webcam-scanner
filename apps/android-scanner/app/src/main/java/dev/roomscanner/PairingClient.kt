package dev.roomscanner

import java.io.BufferedReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
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
