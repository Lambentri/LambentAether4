from components.lambents.lib.config import TupleConfig
from components.lambents.lib.machine import TickEnum, RunningEnum
from components.lambents.lib.steps import DefaultStep


class BaseState(object):  # moveme
    def do_step(self):
        raise NotImplemented("state needs a do_step implemented")

    def read_rgb(self):
        raise NotImplemented("state needs to return an (r,g,b) tuple from read_rgb")


class SolidState(BaseState):

    def __init__(self, colors):
        self.colors = colors

    @staticmethod
    def validate(config, params):
        color = config['color']['cls']
        cvars = color.validate(params.get('color'))
        return {"colors": cvars}

    def do_step(self):
        pass  # boop

    def read_rgb(self):
        return self.colors


class SolidStep(DefaultStep):
    desc = "return a solid color"
    name = "Solid Step"
    speed = TickEnum.TENS
    running = RunningEnum.RUNNING
    grps = ['solids']

    class meta:
        state = SolidState
        config = {
            "color": {
                "cls": TupleConfig(count=3, of_type=int, min=0, max=255),
                "desc": "Colors that come out of the machine"
            }
        }
        # classes of base ConfigClass that implement configuration for a step
        # arrayfields, tuple of x-value-fields, enforced strings/ints/as typeOf(for any field)
        # kwargs for typeof include a required cnt | max_cnt | min_cnt
        # example
        # TupleField(of=Int(max=255), cnt=3)
        # ArrayField(of=String(max=64, max_cnt=4)f
