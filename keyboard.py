#!/usr/bin/python

import argparse
import bluetooth
import dbus
import itertools
import logging
import os
import subprocess
import sys
import time

HCI_KEYBOARD_CONTROL_PORT = 17
HCI_KEYBOARD_INTERRUPT_PORT = 19

def read_relative_file(name):
  full_path = os.path.join(os.path.dirname(sys.argv[0]), name)
  with open(full_path) as fh:
    return fh.read()

def init_adapter(interface, device_name):
  # TODO: switch to ctypes; bluetooth._bluetooth doesn't support the
  # APIs we need, sadly
  logging.info("Running hciconfig for " + interface)
  subprocess.call(["hciconfig", interface, "class", "0x002540"])
  subprocess.call(["hciconfig", interface, "name", device_name])
  subprocess.call(["hciconfig", interface, "piscan"])

  # Become discoverable by asking bluez to advertise our SDP for us
  logging.info("Advertising via sdb")
  bus = dbus.SystemBus()
  manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.bluez.Manager")
  adapter_path = manager.FindAdapter(interface)
  service = dbus.Interface(bus.get_object("org.bluez", adapter_path), "org.bluez.Service")
  service.AddRecord(read_relative_file("fake_keyboard_record.xml"))

def main():
  logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument("--interface", help="interface, defaults to hci0", default="hci0")
  parser.add_argument("--reconnect", help="reconnect to this device (mac addr), otherwise become browsable")
  arguments = parser.parse_args()

  # HID mapping is weird.  this is just a subset.
  hid_byte_map = dict()
  for c in range(ord('a'), ord('z')):
    hid_byte_map[chr(c)] = c - ord('a') + 4
  hid_byte_map[' '] = 0x2c
  
  init_adapter(arguments.interface, "Linux Keyboard")

  # Either become browsable and answer, or reconnect.  Pairing seems
  # to be optional?
  target_addr = arguments.reconnect
  if not target_addr:
    logging.info("Listening for connection")
    control_listen_socket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    control_listen_socket.bind(("", HCI_KEYBOARD_CONTROL_PORT))
    control_listen_socket.listen(1)
    interrupt_listen_socket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    interrupt_listen_socket.bind(("", HCI_KEYBOARD_INTERRUPT_PORT))
    interrupt_listen_socket.listen(1)

    control_socket, control_info = control_listen_socket.accept()
    interrupt_socket, interrupt_info = interrupt_listen_socket.accept()

    logging.info("Connection established to %s (%s)" % (control_info, interrupt_info))
    connected = False
    while not connected:
      header = ord(control_socket.recv(1))
      msg_type, msg_data = (header >> 4), (header & 0b1111)
      logging.info("data is %02x %02x" % (msg_type, msg_data))
      if msg_type == 0x09:  # SET_IDLE
        logging.info("looks like windows")
        connected = True
      elif msg_type == 0x07:  # SET_PROTOCOL
        logging.info("looks like iphone")
        connected = True
      else:
        logging.fatal("aiee who knows")

  else:
    # just connect to the specified destination
    logging.info("Reconnecting to %s" % target_addr)
    control_socket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    control_socket.connect((target_addr, HCI_KEYBOARD_CONTROL_PORT))
    interrupt_socket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    interrupt_socket.connect((target_addr, HCI_KEYBOARD_INTERRUPT_PORT))

  # We have a connection, spam away!
  logging.info("Socket connected, sending handshake")
  control_socket.send(chr(0))
  logging.info("spamming chip!")

  for byte in itertools.cycle("chip "):
    hid_byte = hid_byte_map[byte]
    msg = "".join(chr(c) for c in (0xa1, 0x01, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, hid_byte))
    interrupt_socket.send(msg)
    msg = "".join(chr(c) for c in (0xa1, 0x01, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0))
    interrupt_socket.send(msg)
    time.sleep(0.05)
    

if __name__ == '__main__':
  sys.exit(main())
