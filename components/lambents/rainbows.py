from components.lambents.lib.color import HSVHelper
from components.lambents.lib.config import IntegerConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep
from components.lambents.solids import BaseState


class RainbowLEDState(HSVHelper, BaseState):
    def __init__(self, status=0, s=255, v=255, stepsize=1):
        self.h = 0
        self.s = s
        self.v = v
        self.stepsize = stepsize

        self.status = status

    def set_status(self, value):  # useful for init
        self.status = value

    def do_step(self):
        self.status = (self.status + self.stepsize) % 256
        self.h = self.status

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.h, self.s, self.v)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        print(params)
        sat = config['s']['cls']
        val = config['v']['cls']
        # svars = sat.validate(params.get('s'))
        # vvars = val.validate(params.get('v'))
        # return {"s": svars, "v": vvars, **params}

        return {**params}

class RainbowChaser(DefaultStep):
    desc = "a rainbow that chases itself"
    grps = ['rainbow']
    name = "Rainbow Chaser"
    speed = TickEnum.FHUNDREDTHS
    running = RunningEnum.RUNNING

    class meta:
        state = RainbowLEDState
        state_status = True
        config = {
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
        }