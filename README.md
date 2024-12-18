![https://github.com/nigels-com/glow](glow/glow.png)

A Raspberry Pi command-line tool and service for glowing the Pimoroni Blinkt!

## Introduction

## Command Line

```$ ./glow.py --help
Usage: glow.py [OPTIONS]

Options:
  -r, --root TEXT          Root web folder
  -d, --duration FLOAT     Duration
  --min FLOAT              Minimum
  --max FLOAT              Maximum
  -b, --brightness FLOAT   Brightness
  -p, --power FLOAT        Power
  -c, --colour INTEGER...  Colour
  --stone                  Stone Mode
  --emerald                Emerald Mode
  --redstone               Redstone Mode
  --help                   Show this message and exit.
```

## REST API

Set the colour to red, green or blue.

```
$ curl -X POST -d '{"colour":"#f00"}' http://localhost:8080/
$ curl -X POST -d '{"colour":"#0f0"}' http://localhost:8080/
$ curl -X POST -d '{"colour":"#00f"}' http://localhost:8080/
```

## Web User Interface

http://localhost:8080/

![index.html](control.png)

## Videos

[![GLOW Video](video2.jpg)](https://www.youtube.com/watch?v=jpt5c_KMTl4)

[![Minecraft Server Test #1](video1.jpg)](https://www.youtube.com/watch?v=tUi1ILAl58A)

## Installation

### Ubuntu/Raspbian

`sudo apt install python-click python-webcolors python-bottle`

## Notes

How to disable the [LED lights](https://www.jeffgeerling.com/blogs/jeff-geerling/controlling-pwr-act-leds-raspberry-pi) on a Raspberry Pi.

## Raspberry Pi 3 Model B Plus

config.txt

```
# Turn off Power LED
dtparam=pwr_led_trigger=default-on
dtparam=pwr_led_activelow=off
# Turn off Activity LED
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off
# Turn off Ethernet ACT LED
dtparam=eth_led0=14
# Turn off Ethernet LNK LED
dtparam=eth_led1=14
```