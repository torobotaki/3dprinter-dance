import serial
import time
import threading
import tkinter as tk
import logging

logging.basicConfig(filename="ender3_printer_log.txt", level=logging.INFO)

# Serielle Verbindung zum Drucker herstellen
ser = serial.Serial("/dev/tty.usbserial-14520", 250000)
time.sleep(2)

# Sperre für Thread-Synchronisation
serial_lock = threading.Lock()


# Funktion, um auf die Bereitschaft des Druckers zu warten und den Empfangspuffer zu leeren
def wait_for_printer_ready(ser):
    while True:
        response = ser.readline().decode().strip()
        if "ok" in response or "wait" in response:
            logging.info(f"Printer response: {response}")
            ser.flushInput()  # Empfangspuffer nach Empfang von "ok" leeren
            break


# Funktion, um die Buchstabe "H" zu drucken
def draw_letter_h():
    # Move to the starting position (left vertical line bottom)
    ser.write(str.encode("G1 X10 Y10 Z0.2 F1200\r\n"))
    wait_for_printer_ready(ser)

    # Draw the left vertical line
    ser.write(str.encode("G1 Y50\r\n"))  # Move up
    wait_for_printer_ready(ser)

    ser.write(str.encode("G1 Y10\r\n"))  # Move back down
    wait_for_printer_ready(ser)

    # Move to the middle horizontal line
    ser.write(str.encode("G1 X30 Y30\r\n"))  # Move to the center of "H"
    wait_for_printer_ready(ser)

    # Draw the middle horizontal line
    ser.write(str.encode("G1 X50 Y30\r\n"))  # Draw right
    wait_for_printer_ready(ser)

    # Move to the right vertical line bottom
    ser.write(str.encode("G1 X70 Y10\r\n"))
    wait_for_printer_ready(ser)

    # Draw the right vertical line
    ser.write(str.encode("G1 Y50\r\n"))  # Move up
    wait_for_printer_ready(ser)

    ser.write(str.encode("G1 Y10\r\n"))  # Move back down
    wait_for_printer_ready(ser)


# Drucker homing
ser.flushInput()  # Empfangspuffer leeren
ser.flushOutput()  # Sendepuffer leeren
ser.write(str.encode("G28\r\n"))
wait_for_printer_ready(ser)

# Set nozzle temperature
ser.write(str.encode("M104 S100\r\n"))
wait_for_printer_ready(ser)

ser.write(str.encode("M109 S100\r\n"))
wait_for_printer_ready(ser)

# Draw the letter H
draw_letter_h()

# Serielle Verbindung schließen
ser.close()
