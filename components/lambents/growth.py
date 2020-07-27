import random

from components.lambents.lib.color import HSVHelper
from components.lambents.lib.config import IntegerConfig, ArrayConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep
from components.lambents.solids import BaseState


class GrowthMortalityBase(DefaultStep):
    pass


class GMLeave(GrowthMortalityBase):
    pass


class GMFireflyRandomHSVState(HSVHelper, BaseState):
    pass


class GMFireflyHSVState(HSVHelper, BaseState):
    active = False
    c_cnt = 5
    c_cnt_done = 0
    c_state = 0

    def __init__(self, status=0, h=52, s=255, v=255):
        self.h = h
        self.s = s
        self.v = 0
        self.v_max = v
        self.status = status

    def do_step(self):
        if self.active:
            if self.c_cnt_done >= self.c_cnt:
                self.active = False
                self.c_cnt_done = 0
                return

            if self.v == 0:
                self.v = int(random.choice([self.v_max, self.v_max / 2, self.v_max / 3]))
            else:
                self.v = 0
                self.c_cnt_done += 1

        else:
            self.active = random.choice([True] + [False] * 5000)
            self.c_cnt = random.randint(3, 7)

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class GMFireflyRandomHSV(DefaultStep):
    desc = "A bug that blinks on and off randomly in one of X colors"
    grps = ["gm"]
    name = "Lightning Bug Random"
    speed = TickEnum.FTENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = GMFireflyRandomHSVState
        state_status = True
        config = {
            "h": {
                "cls": ArrayConfig(max_count=32, min=0, max=255, default=[52, 15, 140], of_type=int),
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
        }

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class FireflyHSV(DefaultStep):
    desc = "A bug that blinks on and off a few times"
    grps = ["gm"]
    name = "FireflyHSV"
    speed = TickEnum.FTENTHS
    running = RunningEnum.RUNNING

    class meta:
        state = GMFireflyHSVState
        state_status = True
        config = {
            "h": {
                "cls": IntegerConfig(min=0, max=255, default=52),
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
        }
