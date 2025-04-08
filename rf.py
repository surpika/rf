#!/usr/bin/env python3

import json
import websocket
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import threading
import argparse

# Global variable to store the latest spectrum data
spectrum_data = [0] * 14  # Initialize with zeros for 14 WiFi channels
data_lock = threading.Lock()  # Lock for thread-safe access

# Connect to the ESP32 WebSocket server
def connect_websocket(esp32_ip):
    ws_url = f"ws://{esp32_ip}:81"
    
    def on_message(ws, message):
        global spectrum_data
        try:
            data = json.loads(message)
            with data_lock:
                spectrum_data = data["spectrum"]
            print(f"Received: {spectrum_data}")
        except json.JSONDecodeError:
            print(f"Failed to parse message: {message}")
        except KeyError:
            print(f"Missing expected key in data: {message}")
    
    def on_error(ws, error):
        print(f"Error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("Connection closed")
    
    def on_open(ws):
        print(f"Connected to ESP32 at {esp32_ip}")
    
    # Setup WebSocket connection
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    # Start WebSocket client in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    return ws

# Setup the matplotlib figure for visualization
def setup_visualization():
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.canvas.manager.set_window_title('ESP32 Spectrum Analyzer')
    
    # Set up the bar chart
    channels = np.arange(1, 15)  # Channels 1-14
    bars = ax.bar(channels, [0] * 14, width=0.8)
    
    # Add labels and title
    ax.set_xlabel('WiFi Channel')
    ax.set_ylabel('Signal Strength')
    ax.set_title('2.4GHz WiFi Spectrum Analysis')
    ax.set_xlim(0.5, 14.5)
    ax.set_ylim(0, 100)  # Signal strength from 0-100
    ax.set_xticks(channels)
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Add channel frequency labels (in GHz)
    freq_labels = ['2.412', '2.417', '2.422', '2.427', '2.432', '2.437', '2.442', 
                  '2.447', '2.452', '2.457', '2.462', '2.467', '2.472', '2.484']
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(channels)
    ax2.set_xticklabels(freq_labels, rotation=45)
    ax2.set_xlabel('Frequency (GHz)')
    
    # Add a color gradient to the bars
    for bar in bars:
        bar.set_color('blue')
    
    return fig, ax, bars

# Update function for the animation
def update_plot(frame, bars):
    with data_lock:
        data = spectrum_data.copy()
    
    # Update bar heights
    for i, bar in enumerate(bars):
        bar.set_height(data[i])
        
        # Update bar colors based on signal strength (green-yellow-red)
        if data[i] < 30:
            bar.set_color('green')
        elif data[i] < 70:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    return bars

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ESP32 Spectrum Analyzer Display')
    parser.add_argument('--ip', default='192.168.4.1', 
                        help='IP address of the ESP32 (default: 192.168.4.1)')
    args = parser.parse_args()
    
    # Connect to the ESP32
    ws = connect_websocket(args.ip)
    
    # Setup visualization
    fig, ax, bars = setup_visualization()
    
    # Create animation
    ani = FuncAnimation(fig, update_plot, fargs=(bars,), interval=100, blit=True)
    
    # Display the plot
    plt.tight_layout()
    plt.show()
    
    # Close WebSocket connection when done
    ws.close()

if __name__ == "__main__":
    # Enable websocket debug if needed
    # websocket.enableTrace(True)
    main()