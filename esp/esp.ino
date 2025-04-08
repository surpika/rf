#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>

#define SCAN_INTERVAL 1000  // Increased to 1000ms for more reliable scanning
#define SERIAL_BAUD 115200

// Variables to store scan results
uint8_t channelValues[14] = {0}; // For 14 WiFi channels

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000); // Give serial time to initialize
  
  // Initialize WiFi in station mode for scanning
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // Make sure we're disconnected before scanning
  
  Serial.println("ESP32 Serial Spectrum Analyzer");
  Serial.println("Initializing...");
  
  // Set WiFi to promiscuous mode for better scanning
  esp_wifi_set_promiscuous(true);
}

void loop() {
  // Perform WiFi scan for energy levels
  Serial.println("Starting WiFi scan...");
  scanWiFiChannels();
  
  // Send data through Serial
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
  
  Serial.print("Networks found: ");
  Serial.println(num_ap);
  
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
      
      // Print SSID as a C string (char array)
      Serial.print("AP: ");
      Serial.print((char*)ap_records[i].ssid);  // Cast to char* for proper string printing
      Serial.print(" Ch: ");
      Serial.print(channel);
      Serial.print(" RSSI: ");
      Serial.println(rssi);
      
      // Convert RSSI (typically -100 to -30 dBm) to a value 0-100
      // -30 dBm (very strong) = 100, -100 dBm (very weak) = 0
      int signal_strength = constrain(map(rssi, -100, -30, 0, 100), 0, 100);
      
      // Keep the strongest signal per channel
      if (channel > 0 && channel <= 14 && signal_strength > channelValues[channel-1]) {
        channelValues[channel-1] = signal_strength;
      }
    }
    
    delete[] ap_records;
  } else {
    // If no networks, set some dummy values for testing
    for (int i = 0; i < 14; i++) {
      // Create a dummy pattern with alternating values
      channelValues[i] = (i % 3) * 30 + 10; 
    }
    Serial.println("No networks found, using dummy data");
  }
}

void sendSpectrumData() {
  // Send data as a simple, compact serial protocol
  Serial.print("S"); // Start marker
  
  for (int i = 0; i < 14; i++) {
    // Send each value as a byte
    Serial.write(channelValues[i]);
  }
  
  Serial.print("E"); // End marker
  
  // Also send human-readable format for debugging
  Serial.print("Spectrum: ");
  for (int i = 0; 14 > i; i++) {
    Serial.print(channelValues[i]);
    Serial.print(" ");
  }
  Serial.println();
}