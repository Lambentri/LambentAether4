from components.lambents.lib.color import HSVHelper
from components.lambents.lib.config import ArrayConfig, IntegerConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep
from components.lambents.solids import BaseState


class BounceScapeState(HSVHelper, BaseState):
    status = 0
    def __init__(self, h, s=255, v=255, step=1, status=0):
        self.h_1 = h[0]
        self.h_2 = h[1]
        self.s = s
        self.v = v
        self.sz = step
        self.status = status

        self.target = h[0]
        self.hue_range = self._gen_min_max_range()
        self.hue_count = len(self.hue_range)
        self.target = len(self.hue_range)

    def _gen_min_max_range(self):
        if self.h_1 <= self.h_2:
            return [i for i in range(self.h_1, self.h_2)]
        else:
            range_top = [i for i in range(self.h_1, 255)]
            range_bot = [i for i in range(0, self.h_2)]
            return range_top + range_bot

    def _at_target(self):
        return self.status == self.target

    def do_step(self):
        if self._at_target():
            if self.target == 0:
                self.target = self.hue_count
            else:
                self.target = 0

        self.status = self._naive_step(self.status, self.target)

    def read_rgb(self):
        r, g, b = self._hsv_to_rgb(self.hue_range[self.status % self.hue_count], self.s, self.v)
        return [int(r), int(g), int(b)]

    @staticmethod
    def validate(config, params):
        hue = config['h']['cls']
        hvars = hue.validate(params.get('h'))
        return {"h": hvars, **params}


class BounceScape(DefaultStep):
    desc = "bouncing hue ranges yo"
    grps = ['bounce', 'multi']
    name = "Bounce"
    speed = TickEnum.TENTHS
    running = RunningEnum.RUNNING


    class meta:
        state = BounceScapeState
        state_status = True
        config = {
            "h": {
                "cls": ArrayConfig(max_count=2, min=0, max=255, default=0, of_type=int, min_count=2),
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
