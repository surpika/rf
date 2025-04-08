#!/usr/bin/env python3

import serial.tools.list_ports
import serial
from serial.serialutil import SerialException
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import threading
import argparse

# Global variable to store the latest spectrum data
spectrum_data = [0] * 14  # Initialize with zeros for 14 WiFi channels
data_lock = threading.Lock()  # Lock for thread-safe access
serial_port = None

# Connect to the ESP32 via serial
def connect_serial(port, baud_rate):
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"Connected to {port} at {baud_rate} baud")
        return ser
    except SerialException as e:
        print(f"Error opening serial port: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error opening serial port: {e}")
        exit(1)

# Serial reading thread function
def read_serial_data(ser):
    global spectrum_data
    
    # Buffer for collecting data
    buffer = bytearray()
    reading_data = False
    
    while True:
        try:
            # Read available data
            if ser.in_waiting > 0:
                byte = ser.read(1)
                
                # Check for start marker
                if byte == b'S':
                    buffer = bytearray()
                    reading_data = True
                    continue
                
                # Check for end marker
                elif byte == b'E' and reading_data:
                    reading_data = False
                    
                    # If we got 14 values, update spectrum data
                    if len(buffer) == 14:
                        with data_lock:
                            spectrum_data = list(buffer)
                    else:
                        print(f"Received incorrect data length: {len(buffer)}")
                    
                # Add to buffer if we're in reading mode
                elif reading_data:
                    buffer.extend(byte)
            
            else:
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Error reading serial data: {e}")
            time.sleep(0.1)

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
    print("Available ports:")
    for port in serial.tools.list_ports.comports():
        print(f" - {port.device}: {port.description}")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ESP32 Serial Spectrum Analyzer Display')
    parser.add_argument('--port', default='/dev/ttyUSB0', 
                        help='Serial port (default: /dev/ttyUSB0, for Windows try COM1, COM2, etc.)')
    parser.add_argument('--baud', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    args = parser.parse_args()
    
    # Connect to the ESP32 via serial
    ser = connect_serial(args.port, args.baud)
    
    # Start the serial reading thread
    serial_thread = threading.Thread(target=read_serial_data, args=(ser,), daemon=True)
    serial_thread.start()
    
    # Setup visualization
    fig, ax, bars = setup_visualization()
    
    # Create animation
    ani = FuncAnimation(fig, update_plot, fargs=(bars,), interval=100, blit=True)
    
    # Display the plot
    plt.tight_layout()
    plt.show()
    
    # Close serial port when done
    ser.close()

if __name__ == "__main__":
    print("Starting ESP32 Serial Spectrum Analyzer...")
    print("Make sure you have installed pyserial:")
    print("pip3 install pyserial matplotlib numpy")
    main()