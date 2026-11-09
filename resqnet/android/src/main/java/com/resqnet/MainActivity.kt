package com.innovex.resqnet

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat

class MainActivity : AppCompatActivity() {

    private lateinit var offlineManager: ResqNetOfflineManager
    private var currentLat: Double = 13.1845
    private var currentLon: Double = 74.9360

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        offlineManager = ResqNetOfflineManager(this, "http://192.168.43.1:5000")

        val statusBanner = findViewById<TextView>(R.id.tvStatusBanner)
        val spinnerType = findViewById<Spinner>(R.id.spinnerEmergencyType)
        val etName = findViewById<EditText>(R.id.etVictimName)
        val etPhone = findViewById<EditText>(R.id.etPhone)
        val etPeople = findViewById<EditText>(R.id.etPeopleCount)
        val etChildren = findViewById<EditText>(R.id.etChildrenCount)
        val etInjured = findViewById<EditText>(R.id.etInjuredCount)
        val etNotes = findViewById<EditText>(R.id.etNotes)
        val tvGps = findViewById<TextView>(R.id.tvGpsCoords)
        val btnGetGps = findViewById<Button>(R.id.btnFetchGps)
        val btnSendSos = findViewById<Button>(R.id.btnSendSos)

        // Register automatic Wi-Fi Hotspot listener for offline queue flushing
        offlineManager.registerHotspotAutoSync { msg ->
            runOnUiThread {
                statusBanner.text = msg
                Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
            }
        }

        btnGetGps.setOnClickListener {
            fetchOfflineGpsLocation(tvGps)
        }

        btnSendSos.setOnClickListener {
            val packet = SosPacket(
                victimName = etName.text.toString().ifBlank { "Anonymous" },
                phone = etPhone.text.toString().ifBlank { "N/A" },
                emergencyType = spinnerType.selectedItem.toString(),
                peopleCount = etPeople.text.toString().toIntOrNull() ?: 1,
                childrenCount = etChildren.text.toString().toIntOrNull() ?: 0,
                injuredCount = etInjured.text.toString().toIntOrNull() ?: 0,
                latitude = currentLat,
                longitude = currentLon,
                notes = etNotes.text.toString()
            )

            offlineManager.queueOrSendSos(packet) { feedback ->
                runOnUiThread {
                    statusBanner.text = feedback
                }
            }
        }
    }

    private fun fetchOfflineGpsLocation(tvGps: TextView) {
        val locationManager = getSystemService(LOCATION_SERVICE) as LocationManager
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.ACCESS_FINE_LOCATION), 101)
            return
        }
        val loc: Location? = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
        if (loc != null) {
            currentLat = loc.latitude
            currentLon = loc.longitude
            tvGps.text = "GPS Locked: %.5f, %.5f".format(currentLat, currentLon)
        } else {
            tvGps.text = "GPS Default: %.5f, %.5f (Acquiring satellites...)".format(currentLat, currentLon)
        }
    }
}
