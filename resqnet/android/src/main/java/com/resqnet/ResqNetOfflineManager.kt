package com.innovex.resqnet

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/**
 * RESQNET Offline-First SOS Queue & Auto-Sync Engine (Android Kotlin)
 * Matches Slide 04 Architecture:
 * - Saves structured SOS packets locally in SharedPreferences when out of hotspot range
 * - Listens for local Wi-Fi hotspot connection and flushes the queue automatically
 * - Receives HTTP 201 confirmation receipt from the Rescue Team Flask Server
 */
data class SosPacket(
    val clientId: String = "SOS-" + UUID.randomUUID().toString().take(8),
    val victimName: String,
    val phone: String,
    val emergencyType: String,
    val peopleCount: Int,
    val childrenCount: Int,
    val injuredCount: Int,
    val latitude: Double,
    val longitude: Double,
    val notes: String,
    var synced: Boolean = false
)

class ResqNetOfflineManager(
    private val context: Context,
    private val serverBaseUrl: String = "http://192.168.43.1:5000" // Default laptop/phone hotspot gateway IP
) {
    private val prefs = context.getSharedPreferences("resqnet_offline_queue", Context.MODE_PRIVATE)

    fun queueOrSendSos(packet: SosPacket, onStatus: (String) -> Unit) {
        saveToLocalQueue(packet)
        onStatus("SOS saved to offline queue (${packet.clientId}). Scanning for Rescue Hotspot...")
        flushQueue(onStatus)
    }

    private fun saveToLocalQueue(packet: SosPacket) {
        val currentArray = JSONArray(prefs.getString("packets", "[]"))
        val obj = JSONObject().apply {
            put("client_id", packet.clientId)
            put("victim_name", packet.victimName)
            put("phone", packet.phone)
            put("emergency_type", packet.emergencyType)
            put("people_count", packet.peopleCount)
            put("children_count", packet.childrenCount)
            put("injured_count", packet.injuredCount)
            put("latitude", packet.latitude)
            put("longitude", packet.longitude)
            put("notes", packet.notes)
            put("synced", packet.synced)
        }
        currentArray.put(obj)
        prefs.edit().putString("packets", currentArray.toString()).apply()
    }

    fun flushQueue(onStatus: (String) -> Unit) {
        CoroutineScope(Dispatchers.IO).launch {
            val raw = prefs.getString("packets", "[]") ?: "[]"
            val arr = JSONArray(raw)
            var changed = false

            for (i in 0 until arr.length()) {
                val item = arr.getJSONObject(i)
                if (!item.optBoolean("synced", false)) {
                    val confirmedId = postToRescueServer(item)
                    if (confirmedId != null) {
                        item.put("synced", true)
                        item.put("server_id", confirmedId)
                        changed = true
                        onStatus("CONFIRMED: Rescue Laptop received SOS #$confirmedId")
                    }
                }
            }
            if (changed) {
                prefs.edit().putString("packets", arr.toString()).apply()
            }
        }
    }

    private fun postToRescueServer(payload: JSONObject): Int? {
        return try {
            val url = URL("$serverBaseUrl/api/sos")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 3000
                readTimeout = 3000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            OutputStreamWriter(conn.outputStream).use { it.write(payload.toString()) }
            if (conn.responseCode in 200..201) {
                val responseText = conn.inputStream.bufferedReader().readText()
                JSONObject(responseText).optInt("sos_id", -1)
            } else null
        } catch (e: Exception) {
            null
        }
    }

    fun registerHotspotAutoSync(onStatus: (String) -> Unit) {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val request = NetworkRequest.Builder()
            .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .build()

        cm.registerNetworkCallback(request, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                flushQueue(onStatus)
            }
        })
    }
}
