# Development

`pip install -r requirements.txt`

`crossbar start` will start the router bit
then you'll need all the other components you'll be using
so avahi_8266.py, links.py, machine.py, helpers.py

visit localhost:8080 to drive the UI

# Prod

TODO::: setup a crossbar config.json to run all the above components in-router

# Env Vars

## All Pieces

XBAR_ROUTER a crossbar URI for being invoked in dev mode defaulting to `u"ws://127.0.0.1:8080/ws"` which is the default shit

## machine.py

*LA4_CONFIG_PATH* Path to a config file. We default to the included `default.yml` for the full cpu melting experience

# Other Notes

## avahi_8266.py

This sink module is exposing devices flashed with https://github.com/cnlohr/esp8266ws2812i2s and announcing themselves over avahi/bonjour/zeroconf
This system assumes avahi/bonjour/zeroconf works on your network