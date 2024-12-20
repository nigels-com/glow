#!/usr/bin/env python

#pylint: disable=bad-indentation,bad-whitespace

import time
import math
import json
import threading
import logging

import click     # apt install python3-click
import webcolors # apt install python3-webcolors
from bottle import request, static_file, Bottle

import blinkt

LOCK = threading.Lock()

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
      with LOCK:
        delay = self.glow.delay
        self.glow.update()
      time.sleep(delay)

#
# Glow state - colour, brightness, waveform
#

class Glow:

  def __init__(self):
    self.start_time = time.time()
    self.duration = 1.0
    self.colour = [192, 192, 255]
    self.brightness = 1.0
    self.power = 3.0
    self.min = 0.1
    self.max = 0.9
    self.delay = 0.1
    self.left = 0.0
    self.right = 1.0

  def to_json(self):
    o = {}
    o["duration"] = self.duration
    o["colour"] = webcolors.rgb_to_hex((self.colour[0], self.colour[1], self.colour[2]))
    o["brightness"] = self.brightness
    o["power"] = self.power
    o["min"] = self.min
    o["max"] = self.max
    o["delay"] = self.delay
    o["left"] = self.left
    o["right"] = self.right
    return json.dumps(o)

  def from_json(self, j):
    o = json.loads(j)
    if isinstance(o, dict):
      self.__dict__.update(o)
      if isinstance(self.duration, str):
        self.duration = float(self.duration)
      if isinstance(self.colour, str):
        rgb = webcolors.hex_to_rgb(self.colour)
        self.colour = [ rgb[0], rgb[1], rgb[2] ]
      if isinstance(self.brightness, str):
        self.brightness = float(self.brightness)
      if isinstance(self.power, str):
        self.power = float(self.power)
      if isinstance(self.min, str):
        self.min = float(self.min)
      if isinstance(self.max, str):
        self.max = float(self.max)
      if isinstance(self.delay, str):
        self.delay = float(self.delay)
      if isinstance(self.left, str):
        self.left = float(self.left)
      if isinstance(self.right, str):
        self.right = float(self.right)

  def update(self):

    t = (time.time() - self.start_time)
    u = (t%self.duration)/self.duration

    # Triangle wave from 0 to 1 to 0
    f = abs(u*2.0)
    if f>1.0:
      f = 2.0-f
    f = math.pow(f, self.power)
    f = f*self.brightness
    f = self.min + (self.max-self.min)*f

    colour = [int(self.colour[0]*f), int(self.colour[1]*f), int(self.colour[2]*f)]

#   logging.debug(f'update {blinkt.NUM_PIXELS} pixels')
    n = blinkt.NUM_PIXELS
    l = self.left * n
    r = self.right * n
    print(f'{l} {r}')
    for i in range(n):
      if i < l or i >= r:
#        print(' ', end='')
        blinkt.set_pixel(i, 0, 0, 0)
      else:
#        print('X', end='')
        blinkt.set_pixel(i, colour[0], colour[1], colour[2])
#    print('')
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

@click.option(      '--stone',      is_flag=True,        default=False,  help='Stone Mode')
@click.option(      '--emerald',    is_flag=True,        default=False,  help='Emerald Mode')
@click.option(      '--redstone',   is_flag=True,        default=False,  help='Redstone Mode')

@click.option(      '--online',     is_flag=True,        default=False,  help='Machine online (blue)')
@click.option(      '--active',     is_flag=True,        default=False,  help='Machine active (yellow)')
@click.option(      '--aquiring',   is_flag=True,        default=False,  help='Machine aquiring (red)')

@click.option('-v', '--verbose',    is_flag=True,        default=False,  help='Verbose logging')

def cli(root, duration, min, max, brightness, power, colour, stone, emerald, redstone, online, active, aquiring, verbose):

  if verbose:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s')
  else:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s')

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

  # http://localhost:8080/glow.json
  if online:
    glow.from_json('{"power": 2.0, "min": 0.39, "max": 0.9, "colour": "#0000ff", "brightness": 1.0, "delay": 0.05, "duration": 4.0}')
  if active:
    glow.from_json('{"power": 2.0, "min": 0.39, "max": 0.9, "colour": "#ffd700", "brightness": 1.0, "delay": 0.05, "duration": 1.0}')
  if aquiring:
    glow.from_json('{"power": 2.0, "min": 0.39, "max": 0.9, "colour": "#ff0000", "brightness": 1.0, "delay": 0.05, "duration": 1.0}')

  thread = Thread(glow)

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
      return '%s\n'%(glow.to_json())

  @app.post('/')
  def set():
    ''' POST GLOW state as JSON '''
    j = request.body.getvalue()
    logging.debug('Request: %s'%(j))
    try:
      with LOCK:
        glow.from_json(j)
    except:
     pass

  app.glow = glow

  # Main event loop - list for HTTP traffic
  try:
    app.run(host='0.0.0.0', port=8080, debug=verbose)
  except:
    blinkt.clear()
    blinkt.show()

#
if __name__ == '__main__':
  blinkt.set_clear_on_exit()
  cli()
