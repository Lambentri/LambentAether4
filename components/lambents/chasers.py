from itertools import chain

from components.lambents.lib.color import HSVHelper, HexHelper
from components.lambents.lib.config import IntegerConfig, TupleConfig, ArrayConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep
from components.lambents.solids import BaseState


class ChaserState(HSVHelper, BaseState):
    status = 0

    def __init__(self, h, s=255, v=0, spacing=30, fadeby=15, status=0):
        self.h = h
        self.s = s
        self.v = v
        self.spacing = spacing
        self.fadeby = fadeby

        self.window = 255 / (self.spacing - self.fadeby)
        self.status = status

    def _color_from_status(self):
        if self.fadeby < self.status < self.spacing:
            self.v = self.window * (self.status % self.fadeby)
        else:
            self.v = 0

    def do_step(self):
        self.status = (self.status + 1) % self.spacing
        self._color_from_status()

    @staticmethod
    def validate(config, params):
        print(config)
        print(params)
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class MultiChaserState(HSVHelper, BaseState):
    status = 0

    def __init__(self, h=[], s=255, v=0, spacing=30, fadeby=15, status=0):
        self.hs = h
        self.hc = len(h)
        self.h = 0  # set later
        self.s = s
        self.v = v
        self.spacing = spacing
        self.fadeby = fadeby

        self.window = 255 / (self.spacing - self.fadeby)
        self.status = status

        self.statushues = list(chain.from_iterable([[x for i in range(self.spacing)] for x in self.hs]))

    def _color_from_status(self):
        self.h = self.statushues[self.status]

        # brightness is diff here
        if self.fadeby < self.status % self.spacing < self.spacing:
            self.v = self.window * (self.status % self.fadeby)

        else:
            self.v = 0

    def do_step(self):
        self.status = (self.status + 1) % (self.spacing * self.hc)
        self._color_from_status()

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h, self.s, self.v)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class MultiNoSpaceChaseState(HSVHelper, BaseState):
    def __init__(self, h, spacing=30, status=0):
        self.hs = h
        self.hc = len(h)
        self.h = 0  # gets set later
        self.s = 255
        self.v = 255

        self.spacing = spacing
        self.status = status

        self.statushues = list(chain.from_iterable([[x for i in range(self.spacing)] for x in self.hs]))

    def color_from_status(self):
        self.h = self.statushues[self.status]

    def do_step(self):
        self.status = (self.status + 1) % (self.spacing * self.hc)
        self.color_from_status()

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h, self.s, self.v)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class MultiNoSpaceChaseStateRGB(HexHelper, BaseState):
    def __init__(self, colors, spacing=30, status=0):
        self.colors = colors
        self.lcolors = len(colors)

        self.spacing = spacing
        self.status = status

        self.statusvals = list(chain.from_iterable([[x for i in range(self.spacing)] for x in self.colors]))

    def color_from_status(self):
        self.c = self.statusvals[self.status]

    def do_step(self):
        self.status = (self.status + 1) % (self.spacing * self.lcolors)
        self.color_from_status()

    def read_rgb(self):
        r, g, b = self._hex_to_rgb(self.c)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        return {**params}


class SimpleColorChaser(DefaultStep):
    desc = "color that chases itself"
    grps = ['chase', 'solids']
    name = "Simple CC"
    speed = TickEnum.TENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = ChaserState
        state_status = True
        config = {
            "h": {
                "cls": IntegerConfig(min=0, max=255, default=0),
                "title": "Hue",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "s": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Saturation",
                "desc": "Saturation",
                "comp": "SliderComponent"
            },
            "v": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Value",
                "desc": "Value",
                "comp": "SliderComponent"
            },
            "spacing": {
                "cls": IntegerConfig(min=0, max=360, default=30),
                "title": "Spacing",
                "desc": "How far between chasers",
                "comp": "SliderComponent"
            },
            "fadeby": {
                "cls": IntegerConfig(min=0, max=360, default=15),
                "title": "Fade By",
                "desc": "How far between chairs",
                "comp": "SliderComponent"
            }
        }


class MultiColorChaser(DefaultStep):
    desc = "multi color that chases itself"
    grps = ['chase', 'solids', 'multi', 'space']
    name = "Multi CC"
    speed = TickEnum.TENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = MultiChaserState
        state_status = True
        config = {
            "h": {
                "cls": ArrayConfig(max_count=8, min=0, max=255, default=0, of_type=int),
                "title": "Hue",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "s": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Saturation",
                "desc": "Saturation",
                "comp": "SliderComponent"
            },
            "v": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Value",
                "desc": "Value",
                "comp": "SliderComponent"
            },
            "spacing": {
                "cls": IntegerConfig(min=0, max=360, default=30),
                "title": "Spacing",
                "desc": "How far between chasers",
                "comp": "SliderComponent"
            },
            "fadeby": {
                "cls": IntegerConfig(min=0, max=360, default=15),
                "title": "Fade By",
                "desc": "How far between chairs",
                "comp": "SliderComponent"
            }
        }


#
#
class MultiNoSpaceChaser(DefaultStep):
    desc = "multi color that chases itself with no spaces"
    grps = ['chase', 'solids', 'multi', 'nospace']
    name = "Multi CC"
    speed = TickEnum.TENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = MultiNoSpaceChaseState
        state_status = True
        config = {
            "h": {
                "cls": ArrayConfig(max_count=8, min=0, max=255, default=0, of_type=int),
                "title": "Hue",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "s": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Saturation",
                "desc": "Saturation",
                "comp": "SliderComponent"
            },
            "v": {
                "cls": IntegerConfig(min=0, max=255, default=255),
                "title": "Value",
                "desc": "Value",
                "comp": "SliderComponent"
            },
            "spacing": {
                "cls": IntegerConfig(min=0, max=360, default=30),
                "title": "Spacing",
                "desc": "How far between chasers",
                "comp": "SliderComponent"
            },
        }
#

class MultiNoSpaceChaserRGB(DefaultStep):
    desc = "multi color that chases itself with no spaces w/ RGB invocation"
    grps = ['chase', 'solids', 'multi', 'nospace']
    name = "Multi CC RGB"
    speed = TickEnum.TENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = MultiNoSpaceChaseStateRGB
        state_status = True
        config = {
            "colors": {
                "cls": ArrayConfig(max_count=8, default=0, of_type=str),
                "title": "Colors",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "spacing": {
                "cls": IntegerConfig(min=0, max=360, default=30),
                "title": "Spacing",
                "desc": "How far between chasers",
                "comp": "SliderComponent"
            },
        }