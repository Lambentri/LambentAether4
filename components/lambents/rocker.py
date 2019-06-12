from components.lambents.lib.color import HSVHelper
from components.lambents.lib.config import ArrayConfig, IntegerConfig, BooleanConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep
from components.lambents.solids import BaseState


class RockerState(HSVHelper, BaseState):
    status = 0
    statushues = []

    def _generate_status_hsvs(self):
        out_buff = []
        for hue in self.hs:
            h_buff = []
            if self.d:  # dark mode
                for i in range(0, 255):
                    h = hue
                    s = 255
                    v = i
                    h_buff.append([h, s, v])

                for i in range(self.l):
                    h_buff.append([hue, 255, 255])

                for i in range(255, 0, -1):
                    h = hue
                    s = 255
                    v = i
                    h_buff.append([h, s, v])

            else:  # light mode
                for i in range(0, 255):
                    h = hue
                    s = i
                    v = 255
                    h_buff.append([h, s, v])

                for i in range(self.l):
                    h_buff.append([hue, 255, 255])

                for i in range(255, 0, -1):
                    h = hue
                    s = i
                    v = 255
                    h_buff.append([h, s, v])

            out_buff.extend(h_buff)
        return out_buff

    def __init__(self, h=[], l=1000, d=True, status=0):
        self.hs = h
        self.hc = len(h)
        self.h = 0  # set later
        self.s = 0  # set later
        self.v = 0  # set later
        self.l = l
        self.d = d
        self.status = status

        self.statushues = self._generate_status_hsvs()

    def do_step(self):
        self.status = (self.status + 1) % len(self.statushues)
        self.h, self.s, self.v = self.statushues[self.status]

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h, self.s, self.v)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class SolidRocker(DefaultStep):
    """
    Rock between various colors in unison
    """
    desc = "Rock between various colors in unison"
    grps = ['solids', 'multi', 'rocker']
    name = "SolidRocker"
    speed = TickEnum.FHUNDREDTHS
    running = RunningEnum.RUNNING

    class meta:
        state = RockerState
        state_status = False
        config = {
            "h": {
                "cls": ArrayConfig(max_count=32, min=0, max=255, default=0, of_type=int),
                "title": "Hue",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "l": {
                "cls": IntegerConfig(min=1, max=100000, default=1000),
                "title": "Linger",
                "desc": "How many ticks to linger at a color",
                "comp": "SliderComponent"
            },
            "d": {
                "cls": BooleanConfig(default=True),
                "title": "Dark Fade",
                "desc": "If checked, fade to dark, if not fade to light"
            }

        }


class ChasingRocker(DefaultStep):
    """
    Rock between different colors offset-like
    """
    desc = "Rock between various colors offset-like"
    grps = ['chase', 'multi', 'rocker']
    name = "ChasingRocker"
    speed = TickEnum.FHUNDREDTHS
    running = RunningEnum.RUNNING

    class meta:
        state = RockerState
        state_status = True
        config = {
            "h": {
                "cls": ArrayConfig(max_count=32, min=0, max=255, default=0, of_type=int),
                "title": "Hue",
                "desc": "Hue",
                "comp": "SliderComponent"
            },
            "l": {
                "cls": IntegerConfig(min=1, max=100000, default=1000),
                "title": "Linger",
                "desc": "How many ticks to linger at a target color",
                "comp": "SliderComponent"
            },
            "d": {
                "cls": BooleanConfig(default=True),
                "title": "Dark Fade",
                "desc": "If checked, fade to dark, if not fade to light"
            }

        }


class RandomRocker(DefaultStep):
    pass  # an idea, step between random hues, do solid/chasing variants
