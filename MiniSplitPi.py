#!/usr/bin/env python

# MiniSplitPi - Mitsubishi Mr Slim HeatPump API
#
# requires file MiniSplitPi.uuid with a UUID and cert files key.pem and cert.pem, all in /home/pi/MiniSplitPi/ 
# 
# submit GET request with parameters:
#   uuid
#   action = [ poweroff, poweron, shutdown, reboot, ledon, ledoff, set ]
#   temp (if action=set)
#   mode (if action=set)
#   vane (if action=set)
#   dir (if action=set)
#   fan (if action=set)
#
# returns:
#   401 Unauthorized if invalid UUID
#   200 {"action": "received"} if action request
#   200 {...} status info if no action requested

import sys
import ssl
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from mitsi import HeatPump
from mitsi_lookup import (FAN, MODE, POWER, TEMP, VANE)

from time import sleep, time
from gpiozero import CPUTemperature, LED, Button
from subprocess import call
from decimal import Decimal

### BEGIN CONFIGURATION

# GPIO definitions
redled = LED(17)
onoff = Button(3)

# Base dir for uuid and cert/key files
basedir = '/home/pi/MiniSplitPi/'

# Heat Pump device
hpdev = '/dev/ttyAMA0'

# HTTPS Port
portnum = 8043

### END CONFIGURATION

# get UUID
f=open(basedir + 'MiniSplitPi.uuid')
uuid=f.read().strip()
f.close()

# Create our HeatPump object, and start the serial connection
heatpump = HeatPump(hpdev)
heatpump.connect()

# Watch the heatpump for 10 seconds, and get/return current state when a valid packet is found
def get_heatpump():
  for i in range(10):
      heatpump.loop()
      if heatpump.valid:
          return heatpump.to_dict()
      sleep(1)

# Get HP status as JSON
def GetStatus():
  data = get_heatpump()
  cpu = CPUTemperature()
  data['cpu'] = cpu.temperature
  data['time'] = int(time())
  return data

# Shutdown function
def poweroff():
  call("sudo poweroff", shell=True)

# Process action requests sent via GET params
def HandleAction(getParams):
  if getParams['action'][0] == "poweroff"  : 
	  heatpump.set({'power': 'OFF'})
  elif getParams['action'][0] == "poweron" : 
	  heatpump.set({'power': 'ON'})
  elif getParams['action'][0] == "shutdown" : 
  	poweroff()
  elif getParams['action'][0] == "reboot" : 
	  call("sudo reboot", shell=True)
  elif getParams['action'][0] == "ledon" : 
    redled.on()
  elif getParams['action'][0] == "ledoff" : 
    redled.off()
  elif getParams['action'][0] == "set" :
    setValues = {}
    if 'power' in getParams and getParams['power'][0] in POWER:
      setValues['power'] = getParams['power'][0]
    if 'temp' in getParams and Decimal(getParams['temp'][0]) in TEMP:
      setValues['temp'] = getParams['temp'][0]
    if 'mode' in getParams and getParams['mode'][0] in MODE:
      setValues['mode'] = getParams['mode'][0]
    if 'vane' in getParams and getParams['vane'][0] in VANE:
      setValues['vane'] = getParams['vane'][0]
    if 'dir' in getParams and getParams['dir'][0] in DIR:
      setValues['dir'] = getParams['dir'][0]
    if 'fan' in getParams and getParams['fan'][0] in FAN:
      setValues['fan'] = getParams['fan'][0]
    heatpump.set(setValues)
  sleep(3)

# Setup onoff button
onoff.when_pressed = poweroff

# Setup HTTPS server
class HttpHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    getParams = parse_qs(urlparse(self.path).query)
    if 'uuid' in getParams and getParams['uuid'][0] == uuid:
      self.send_response( 200 )
      self.send_header("Content-type", "application/json")
      self.send_header("Access-Control-Allow-Origin", "*")
      self.end_headers()
      if 'action' in getParams:
        response = '{"action": "received"}'
        self.wfile.write(response.encode())
        HandleAction(getParams)
      else:
        status = GetStatus()
        self.wfile.write(json.dumps(status).encode())

    else :
      self.send_response( 401 )
      self.send_header("Content-type", "application/json")
      self.end_headers()
      response = '{"error":"Unauthorized"}'
      self.wfile.write(response.encode())
  def log_message(self, format, *args):
    return

httpd = HTTPServer(("", portnum), HttpHandler)

httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=basedir+"key.pem", certfile=basedir+"cert.pem", server_side=True)

httpd.serve_forever()
