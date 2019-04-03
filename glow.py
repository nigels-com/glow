#!/usr/bin/env python

import time
import math
import json
import random
import threading
import logging

import click
import blinkt
import webcolors
from bottle import get, post, request, Bottle

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

lock = threading.Lock()

#
# Worker thread for periodic update
# of Blinkt! LEDs
#

class Thread(threading.Thread):

  def __init__(self, glow):
    threading.Thread.__init__(self)
    self.daemon = True
    logging.debug('Worker thread started')
    self.glow = glow
    self.start()

  def run(self):
    while True:
      with lock:
        delay = self.glow.delay
        self.glow.update()
      time.sleep(delay)

#
# Glow state - colour, brightness, waveform
#

class Glow:

  def __init__(self):
    self.startTime = time.time()
    self.duration = 1.0
    self.colour = [192, 192, 255]
    self.brightness = 1.0
    self.power = 3.0
    self.min = 0.1
    self.max = 0.9
    self.delay = 0.1

  def toJson(self):
    o = {}
    o["duration"] = self.duration
    o["colour"] = webcolors.rgb_to_hex((self.colour[0], self.colour[1], self.colour[2])) 
    o["brightness"] = self.brightness
    o["power"] = self.power
    o["min"] = self.min
    o["max"] = self.max
    o["delay"] = self.delay
    return json.dumps(o)

  def fromJson(self, str):
    o = json.loads(str)
    if isinstance(o, dict):
      self.__dict__.update(o)
      if isinstance(self.duration, unicode):
        self.duration = float(self.duration)
      if isinstance(self.colour, unicode):
        rgb = webcolors.hex_to_rgb(self.colour) 
        self.colour = [ rgb[0], rgb[1], rgb[2] ]
      if isinstance(self.brightness, unicode):
        self.brightness = float(self.brightness)
      if isinstance(self.power, unicode):
        self.power = float(self.power)
      if isinstance(self.min, unicode):
        self.min = float(self.min)
      if isinstance(self.max, unicode):
        self.max = float(self.max)
      if isinstance(self.delay, unicode):
        self.delay = float(self.delay)

  def update(self):

    t = (time.time() - self.startTime)
    u = (t%self.duration)/self.duration

    # Triangle wave from 0 to 1 to 0
    f = abs(u*2.0)
    if f>1.0:
      f = 2.0-f
    f = math.pow(f, self.power)
    f = f*self.brightness
    f = self.min + (self.max-self.min)*f

    colour = [self.colour[0]*f, self.colour[1]*f, self.colour[2]*f]

    for i in range(blinkt.NUM_PIXELS):
      blinkt.set_pixel(i , colour[0], colour[1], colour[2])
    blinkt.show()

#
# Glowing LEDs as a CLI or a service
#

@click.command()
@click.option('-d', '--duration',            type=float, default=None,  help='Duration')
@click.option(      '--min',                 type=float, default=None,  help='Minimum')
@click.option(      '--max',                 type=float, default=None,  help='Maximum')
@click.option('-b', '--brightness',          type=float, default=None,  help='Brightness')
@click.option('-p', '--power',               type=float, default=None,  help='Power')
@click.option('-c', '--colour',     nargs=3, type=int,   default=None,  help='Colour')
@click.option(      '--stone',      is_flag=True,        default=False, help='Stone Mode')
@click.option(      '--emerald',    is_flag=True,        default=False, help='Emerald Mode')
@click.option(      '--redstone',   is_flag=True,        default=False, help='Redstone Mode')
def cli(duration, min, max, brightness, power, colour, stone, emerald, redstone):
  glow = Glow()
  if stone:
    glow.colour = [192, 192, 102]
    glow.min    = 0.3
    glow.max    = 0.3
    glow.brightness = 1.0
  if emerald:
    glow.colour = [0, 255, 0]
    glow.min    = 0.7
    glow.max    = 0.7
    glow.brightness = 1.0
  if redstone:
    glow.colour = [255, 0, 0]
    glow.min    = 1.0
    glow.max    = 1.0
    glow.brightness = 1.0
  if duration:
    glow.duration = duration
  if min:
    glow.min = min
  if max:
    glow.max = max
  if brightness:
    glow.brightness = brightness
  if power:
    glow.power = power
  if colour:
    glow.colour = colour

  thread = Thread(glow)

  # HTTP REST API

  app = Bottle()

  # GET glow state as JSON
  @app.get('/glow.json')
  def status():
    with lock:
      return '%s\n'%(glow.toJson())

  # GET UI page
  @app.get('/')
  @app.get('/index.html')
  def index():
    return '''
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style></style>
  <title>GLOW</title>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
</head>
<body>
  <img src="logo.png"/>
  <table>
    <tr><td>Duration</td>  <td><input type="text"   id="duration"   value=""></td><td>(sec)</td></tr>
    <tr><td>Colour</td>    <td><input type="color"  id="colour"     value=""></td></tr>
    <tr><td>Brightness</td><td><input type="text"   id="brightness" value=""></td><td>[0.0,1.0]</td></tr>
    <tr><td>Power</td>     <td><input type="text"   id="power"      value=""></td><td>&gt;0.0</td></tr>
    <tr><td>Min</td>       <td><input type="text"   id="min"        value=""></td><td>[0.0,1.0]</td></tr>
    <tr><td>Max</td>       <td><input type="text"   id="max"        value=""></td><td>[0.0,1.0]</td></tr>
  </table>
  <br>
      <input type="button" id="black" style="background-color:black;"></input>
      <input type="button" id="red" style="background-color:red;"></input>
      <input type="button" id="green" style="background-color:green;"></input>
      <input type="button" id="blue" style="background-color:blue;"></input>
      <input type="button" id="white" style="background-color:white;"></input>

  <script type="text/javascript">

    jQuery.ajaxSetup({async:false});
    $.getJSON( "/glow.json", {}, function( data ) { 
        $("#duration").val(data.duration);
        $("#colour").val(data.colour);
        $("#brightness").val(data.brightness);
        $("#power").val(data.power);
        $("#min").val(data.min);
        $("#max").val(data.max);
    });
    jQuery.ajaxSetup({async:true});

    $(document).ready(function(){
        $("#duration")  .change(function(){ if (this.value.length) $.post("/", JSON.stringify({ duration: this.value })); });
        $("#colour")    .change(function(){ if (this.value.length) $.post("/", JSON.stringify({ colour: this.value })); });
        $("#brightness").change(function(){ if (this.value.length) $.post("/", JSON.stringify({ brightness: this.value })); });
        $("#power")     .change(function(){ if (this.value.length) $.post("/", JSON.stringify({ power: this.value })); });
        $("#min")       .change(function(){ if (this.value.length) $.post("/", JSON.stringify({ min: this.value })); });
        $("#max")       .change(function(){ if (this.value.length) $.post("/", JSON.stringify({ max: this.value })); });

        $("#black")     .click(function(){ $.post("/", JSON.stringify({ colour: "#000" })); });
        $("#red")       .click(function(){ $.post("/", JSON.stringify({ colour: "#f00" })); });
        $("#green")     .click(function(){ $.post("/", JSON.stringify({ colour: "#0f0" })); });
        $("#blue")      .click(function(){ $.post("/", JSON.stringify({ colour: "#00f" })); });
        $("#white")     .click(function(){ $.post("/", JSON.stringify({ colour: "#fff" })); });
    });
</script>
</body>
</html>
'''

  # POST glow state as JSON
  @app.post('/')
  def status():
    json = request.body.getvalue()
    logging.debug('Request: %s'%(json))
    try:
      with lock:
        glow.fromJson(request.body.getvalue())
    except:
     pass

  app.glow = glow

  # Main event loop - list for HTTP traffic
  try:
    app.run(host='0.0.0.0', port=8080)
  except:
    blinkt.clear()
    blinkt.show()

#
if __name__ == '__main__':
  blinkt.set_clear_on_exit()
  cli()

