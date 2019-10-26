#!/usr/bin/env python

#pylint: disable=bad-indentation,bad-whitespace

import time
import math
import json
import copy
import threading
import logging

import click
import webcolors
from bottle import request, static_file, Bottle

try:
  import blinkt
except:
  pass

try:
  import unicornhat
except:
  pass

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s')

LOCK = threading.Lock()

#
# Worker thread for periodic update
# of Blinkt! LEDs
#

class Thread(threading.Thread):

  def __init__(self, app):
    threading.Thread.__init__(self)
    self.daemon = True
    logging.debug('Worker thread started')
    self.app = app
    self.start()

  def run(self):
    while True:
      with LOCK:
        if len(self.app.glow):
          j = 0;
          for i in self.app.glow:
            i.update(j, len(self.app.glow))
            j = j+1
          delay = self.app.glow[0].delay
          self.app.glow[0].show()
          time.sleep(delay)
        else:
          time.sleep(0.1)

#
# Glow state - colour, brightness, waveform
#

class Glow:

  def __init__(self, blinkt, unicornhat):
    self.blinkt = blinkt
    self.unicornhat = unicornhat
    self.start_time = time.time()
    self.duration = 1.0
    self.colour = [192, 192, 255]
    self.brightness = 1.0
    self.power = 3.0
    self.min = 0.1
    self.max = 0.9
    self.delay = 0.05

  def to_json(self):
    o = {}
    o["duration"] = self.duration
    o["colour"] = webcolors.rgb_to_hex((self.colour[0], self.colour[1], self.colour[2]))
    o["brightness"] = self.brightness
    o["power"] = self.power
    o["min"] = self.min
    o["max"] = self.max
    o["delay"] = self.delay
    return json.dumps(o)

  def from_json(self, j):
    o = json.loads(j)
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

  def update(self, n, max):

    t = (time.time() - self.start_time)
    u = (t%self.duration)/self.duration

    # Triangle wave from 0 to 1 to 0
    f = abs(u*2.0)
    if f>1.0:
      f = 2.0-f
    f = math.pow(f, self.power)
    f = f*self.brightness
    f = self.min + (self.max-self.min)*f

    colour = [self.colour[0]*f, self.colour[1]*f, self.colour[2]*f]

    if self.unicornhat:
      colour = [int(i) for i in colour]
      for i in range(n, 64, max):
        self.unicornhat.set_pixel(i%8, i/8, colour[0], colour[1], colour[2])

    if self.blinkt:
      for i in range(n, blinkt.NUM_PIXELS, max):
        blinkt.set_pixel(i , colour[0], colour[1], colour[2])

  def show(self):

    if self.unicornhat:
      self.unicornhat.show()

    if self.blinkt:
      blinkt.show()

#
# Glowing LEDs as a CLI or a service
#

@click.command()
@click.option('-r', '--root',                            default='glow', help='Root web folder')
@click.option('-d', '--duration',            type=float, default=None,   help='Duration')
@click.option(      '--min',                 type=float, default=None,   help='Minimum')
@click.option(      '--max',                 type=float, default=None,   help='Maximum')
@click.option('-b', '--brightness',          type=float, default=None,   help='Brightness')
@click.option('-p', '--power',               type=float, default=None,   help='Power')
@click.option('-c', '--colour',     nargs=3, type=int,   default=None,   help='Colour')
@click.option('-n', '--number',              type=int,   default=1,      help='Number of GLOW channels')
@click.option(      '--stone',      is_flag=True,        default=False,  help='Stone Mode')
@click.option(      '--emerald',    is_flag=True,        default=False,  help='Emerald Mode')
@click.option(      '--redstone',   is_flag=True,        default=False,  help='Redstone Mode')
@click.option(      '--candle',     is_flag=True,        default=False,  help='Candle Mode')
def cli(root, duration, min, max, brightness, power, colour, number, stone, emerald, redstone, candle):

  if blinkt:
    print('Pimoroni Blinkt support available.')
  shape = None
  if unicornhat:
    shape = unicornhat.get_shape()
    unicornhat.brightness(1.0)
    print('Pimoroni Unicorn Hat support available, shape is: %s,%s'%(shape))

  glow = Glow(blinkt, unicornhat)
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
  if candle:
    glow.colour = [255, 180, 0]
    glow.min    = 0.5
    glow.max    = 0.9
    glow.brightness = 1.0
    glow.duration = 10.0
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

  # HTTP REST API

  app = Bottle()

  @app.get('/glow.png')
  def logo():
    response = static_file('glow.png', root=root, mimetype='image/png')
    response.set_header("Cache-Control", "public, max-age=60000")
    return response

  @app.get('/jquery.min.js')
  def jquery():
    response = static_file('jquery.min.js', root=root, mimetype='text/javascript')
    response.set_header("Cache-Control", "public, max-age=60000")
    return response

  @app.get('/')
  @app.get('/index.html')
  def index():
    response = static_file('index.html', root=root, mimetype='text/html')
    response.set_header("Cache-Control", "public, max-age=60000")
    return response

  @app.get('/glow.json')
  def get():
    ''' GET GLOW state as JSON '''
    with LOCK:
      return '%s\n'%(app.glow[0].to_json())

  @app.post('/')
  def set():
    ''' POST GLOW state as JSON '''
    j = request.body.getvalue()
    logging.debug('Request: %s'%(j))
    try:
      with LOCK:
        app.glow[0].from_json(j)
    except:
     pass

  app.glow = [copy.copy(glow) for i in range(number)]
  if candle:
    d = app.glow[0].duration
    for i in app.glow:
      i.duration = d
      d = d*0.45

  thread = Thread(app)

  # Main event loop - list for HTTP traffic
  try:
    app.run(host='0.0.0.0', port=8080)
  except:
    if blinkt:
      blinkt.clear()
      blinkt.show()
    if unicornhat:
      unicornhat.off()

#
if __name__ == '__main__':
  blinkt.set_clear_on_exit()
  cli()
