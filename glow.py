#!/usr/bin/env python

import time
import math
import random
import click
#import thread
import threading
import logging
#1import bottle

import blinkt
import json

from bottle import get, post, request, Bottle

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

lock = threading.Lock()

class Thread(threading.Thread):

  def __init__(self, glow):
    threading.Thread.__init__(self)
    self.daemon = True
    logging.debug('Thread started')
    self.glow = glow
    self.start()

  def run(self):
    while True:
#     logging.debug('Updated')
      with lock:
        delay = self.glow.delay
        self.glow.update()
      time.sleep(delay)

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
    return json.dumps(self.__dict__)

  def fromJson(self, str):
    o = json.loads(str)
    if isinstance(o, dict):
      self.__dict__.update(o)

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

#S = [0, 0, 0, 0, 0, 0.125, 0.25, 1.0, 0.25, 0.125, 0, 0, 0, 0, 0, 0]
#S = [0, 0, 0, 0, 0.1, 0.2, 0.5, 1.0, 0.5, 0.2, 0.1, 0, 0, 0, 0, 0]
#S = [0, 0, 0.1, 0.2, 0.5, 1.0, 0.5, 0.2, 0.1, 0, 0]

#start_time = time.time()

#while True:
    # Sine wave, spends a little longer at min/max
    # delta = (time.time() - start_time) * 8
    # offset = int(round(((math.sin(delta) + 1) / 2) * (blinkt.NUM_PIXELS - 1)))

    # Triangle wave, a snappy ping-pong effect
#    delta = (time.time() - start_time) * 1.0

#    max = len(S) - blinkt.NUM_PIXELS
#    offset = int(abs(delta%(max*2)))
#    if offset>=max:
#       offset = max*2 - offset - 1

#    r = random.randint(0,255)
#    r = random.randint(0,255) | random.randint(0,255)
#    print r


#    RGB = [255, 255, 0]
#    RGB = [255, 64, 0]
#    RGB = [255, 0, 0]
#    RGB = [192, 192, 255]
#    for i in range(blinkt.NUM_PIXELS):
#       blinkt.set_pixel(i , RGB[0]*S[offset + i], RGB[1]*S[offset+i], RGB[2]*S[offset+i])
#        blinkt.set_pixel(i , RGB[0]*((1<<i)&r != 0), RGB[1]*((1<<i)&r != 0), RGB[2]*((1<<i)&r != 0))
#        blinkt.set_pixel(i , RGB[0]*s, RGB[1]*s, RGB[2]*s)

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

#  j = glow.toJson()
# print('%s'%(j))
#  glow.fromJson('{"max": 1.0, "colour": [255, 0, 255], "brightness": 1.0, "min": 0.1}')
#  glow.fromJson('{"max": 1.0, "colour": [255, 0, 255], "brightness": 0.2, "min": 0.1, "duration": 2.0}')

  app = Bottle()

  @app.get('/')
  def status():
    with lock:
      return '%s\n'%(glow.toJson())

  @app.post('/')
  def status():
    json = request.body.getvalue()
    logging.debug('Request: %s'%(json))
    try:
      with lock:
        glow.fromJson(request.body.getvalue())
    except:
     pass

#  worker = threading.Thread(target=glow.loop())
  app.glow = glow
  thread = Thread(glow)
#  thread.start()
#  thread.start_new_thread(glow.loop())

  try:
    app.run(host='localhost', port=8080)
  except:
    blinkt.clear()
    blinkt.show()

#  run(host='localhost', port=8080)


#  while True:
#    time.sleep(1)

#    logging.debug('Waiting')
#    glow.update()
#    with lock:
#    logging.debug('Waiting')
#      print('%s'%(glow.toJson()))

if __name__ == '__main__':
  blinkt.set_clear_on_exit()
  cli()

