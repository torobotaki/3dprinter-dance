import serial
import time
import threading
import tkinter as tk
import logging

# logging.basicConfig(filename='ender3_printer_log.txt',level=logging.INFO)

# Serielle Verbindung zum Drucker herstellen
ser = serial.Serial("/dev/tty.usbserial-110", 250000)
time.sleep(2)

ser.write(str.encode("G28\r\n"))

ser.write(str.encode("M104 S100\r\n"))

ser.write(str.encode("M109 S100\r\n"))
