import serial
import time
import threading
import tkinter as tk
import logging

logging.basicConfig(filename="ender3_printer_log.txt", level=logging.INFO)

# create serial connection with 3D printer
ser = serial.Serial("/dev/tty.usbserial-210", 115200)
time.sleep(2)

# locking thread synchronization
serial_lock = threading.Lock()


# Waiting for printer to execute task and erasing buffer
def wait_for_printer_ready(ser):
    while True:
        response = ser.readline().decode().strip()
        if "ok" in response or "wait" in response:
            logging.info(f"Printer response: {response}")
            ser.flushInput()  # Empfangspuffer nach Empfang von "ok" leeren
            break


# homing printer
ser.flushInput()  # Empfangspuffer leeren
ser.flushOutput()  # Sendepuffer leeren
ser.write(str.encode("G28\r\n"))
wait_for_printer_ready(ser)

ser.write(str.encode("M104 S100\r\n"))
wait_for_printer_ready(ser)

ser.write(str.encode("M109 S100\r\n"))
wait_for_printer_ready(ser)
