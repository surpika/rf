#!/usr/bin/env python3

import serial
import serial.tools.list_ports
import time
import argparse

def main():
    # Print available ports
    print("Available serial ports:")
    for port in serial.tools.list_ports.comports():
        print(f" - {port.device}: {port.description}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ESP32 Serial Debug')
    parser.add_argument('--port', required=True, 
                        help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    args = parser.parse_args()
    
    try:
        # Connect to the serial port
        print(f"Attempting to connect to {args.port} at {args.baud} baud...")
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"Connected successfully to {args.port}")
        
        # Wait for the device to initialize
        time.sleep(2)
        
        # Clear any pending data
        ser.reset_input_buffer()
        
        # Buffer for collecting data
        buffer = bytearray()
        reading_data = False
        
        print("Reading serial data (press Ctrl+C to exit)...")
        print("Waiting for 'S' start marker followed by 14 bytes and 'E' end marker...")
        
        while True:
            # Read available data
            if ser.in_waiting > 0:
                byte = ser.read(1)
                
                # Print raw byte for debugging
                print(f"Received: {byte} ({byte.hex()})", end=' ')
                
                # Check for start marker
                if byte == b'S':
                    print("- START MARKER")
                    buffer = bytearray()
                    reading_data = True
                    continue
                
                # Check for end marker
                elif byte == b'E' and reading_data:
                    print("- END MARKER")
                    print(f"Complete packet received, length: {len(buffer)}")
                    
                    if len(buffer) == 14:
                        print("Packet has correct length (14 bytes)")
                        print("Values:", list(buffer))
                    else:
                        print(f"WARNING: Incorrect data length: {len(buffer)}, expected 14")
                    
                    reading_data = False
                    print("-----")
                
                # Add to buffer if we're in reading mode
                elif reading_data:
                    buffer.extend(byte)
                    print(f"- Added to buffer (current length: {len(buffer)})")
                
                else:
                    # Handle other data (debug output from ESP32)
                    if byte.isascii() and byte.isprintable():
                        print(f"- Debug output: {byte.decode('ascii')}")
                    else:
                        print("- Non-protocol byte")
            
            else:
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"Closed connection to {args.port}")

if __name__ == "__main__":
    main()