#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <WebSocketsServer.h>

#define SCAN_INTERVAL 100  // milliseconds between scans

// Initialize WebSocket server on port 81
WebSocketsServer webSocket = WebSocketsServer(81);

// WiFi configuration - create an access point
const char* ap_ssid = "ESP32_Spectrum";
const char* ap_password = "spectrum123";

// Variables to store scan results
uint8_t channelValues[14] = {0}; // For 14 WiFi channels

void setup() {
  Serial.begin(115200);
  
  // Initialize WiFi in AP mode
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(ap_ssid, ap_password);
  
  Serial.println("ESP32 Spectrum Analyzer");
  Serial.print("Access Point IP: ");
  Serial.println(WiFi.softAPIP());
  
  // Initialize WebSocket server
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
  Serial.println("WebSocket server started");
  
  // Set WiFi to promiscuous mode for better scanning
  esp_wifi_set_promiscuous(true);
}

void loop() {
  // Handle WebSocket communications
  webSocket.loop();
  
  // Perform WiFi scan for energy levels
  scanWiFiChannels();
  
  // Send data through WebSocket
  sendSpectrumData();
  
  delay(SCAN_INTERVAL);
}

void scanWiFiChannels() {
  wifi_scan_config_t config = {
    .ssid = NULL,
    .bssid = NULL,
    .channel = 0,
    .show_hidden = true
  };
  
  // Start WiFi scan
  esp_wifi_scan_start(&config, true);
  
  // Get scan results
  uint16_t num_ap = 0;
  esp_wifi_scan_get_ap_num(&num_ap);
  
  if (num_ap > 0) {
    wifi_ap_record_t* ap_records = new wifi_ap_record_t[num_ap];
    esp_wifi_scan_get_ap_records(&num_ap, ap_records);
    
    // Reset channel values
    for (int i = 0; i < 14; i++) {
      channelValues[i] = 0;
    }
    
    // Process scan results
    for (int i = 0; i < num_ap; i++) {
      int channel = ap_records[i].primary;
      int rssi = ap_records[i].rssi;
      
      // Convert RSSI (typically -100 to -30 dBm) to a value 0-100
      // -30 dBm (very strong) = 100, -100 dBm (very weak) = 0
      int signal_strength = constrain(map(rssi, -100, -30, 0, 100), 0, 100);
      
      // Keep the strongest signal per channel
      if (channel > 0 && channel <= 14 && signal_strength > channelValues[channel-1]) {
        channelValues[channel-1] = signal_strength;
      }
    }
    
    delete[] ap_records;
  }
  
  // Optionally, we can also get raw energy data for each channel
  // This requires ESP-IDF and is more complex but provides better spectrum analysis
  // The simplified version above is adequate for most purposes
}

void sendSpectrumData() {
  // Create JSON with channel data
  String jsonData = "{\"spectrum\":[";
  
  for (int i = 0; i < 14; i++) {
    jsonData += channelValues[i];
    if (i < 13) jsonData += ",";
  }
  
  jsonData += "]}";
  
  // Send to all connected WebSocket clients
  webSocket.broadcastTXT(jsonData);
  
  // Also print to serial for debugging
  Serial.println(jsonData);
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.printf("[%u] Disconnected!\n", num);
      break;
    case WStype_CONNECTED:
      {
        IPAddress ip = webSocket.remoteIP(num);
        Serial.printf("[%u] Connected from %d.%d.%d.%d\n", num, ip[0], ip[1], ip[2], ip[3]);
      }
      break;
    case WStype_TEXT:
      // Handle any commands from the client
      break;
  }
}