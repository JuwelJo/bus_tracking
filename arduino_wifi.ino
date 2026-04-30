#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";      // Replace with your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";  // Replace with your WiFi password

TinyGPSPlus gps;

// GPS UART
HardwareSerial gpsSerial(2);

// Server
String serverURL = "http://10.80.251.38:8000/location";  // Local IP for FastAPI backend

// Function declarations
void sendToServer(float lat, float lon, float speed);
bool connectWiFi();

void setup() {
  Serial.begin(115200);

  gpsSerial.begin(9600, SERIAL_8N1, 4, -1);   // GPS RX only

  Serial.println("Connecting to WiFi...");
  if (!connectWiFi()) {
    Serial.println("WiFi failed! Restarting...");
    ESP.restart();
  }

  Serial.println("System Starting...");
  delay(2000);
}

void loop() {
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  if (gps.location.isValid()) {
    float lat = gps.location.lat();
    float lon = gps.location.lng();
    float speed = gps.speed.isValid() ? gps.speed.kmph() : 0.0;

    Serial.println("\n--- GPS FIXED ---");
    Serial.print("Lat: ");
    Serial.println(lat, 6);
    Serial.print("Lon: ");
    Serial.println(lon, 6);
    Serial.print("Speed: ");
    Serial.println(speed, 2);

    sendToServer(lat, lon, speed);

    delay(20000);
  }
}

/////////////////////////////////////////////////////
// WiFi Connection
/////////////////////////////////////////////////////
bool connectWiFi() {
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.println(WiFi.localIP());
    return true;
  }
  return false;
}

/////////////////////////////////////////////////////
// Send Data via WiFi
/////////////////////////////////////////////////////
void sendToServer(float lat, float lon, float speed) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String json = "{\"bus_id\":6097,\"lat\":";
  json += String(lat, 6);
  json += ",\"lng\":";
  json += String(lon, 6);
  json += ",\"speed\":";
  json += String(speed, 2);
  json += "}";

  Serial.println("Sending:");
  Serial.println(json);

  int httpResponseCode = http.POST(json);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Response:");
    Serial.println(response);
  } else {
    Serial.println("HTTP Error: " + String(httpResponseCode));
  }

  http.end();
}