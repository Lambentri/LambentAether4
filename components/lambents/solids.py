from components.lambents.lib.steps import DefaultStep

class BaseState(object): # moveme
    def do_step(self):
        raise NotImplemented("state needs a do_step implemented")

    def read_rbp(self):
        raise NotImplemented("state needs to return an (r,g,b) tuple from read_rgb")

class SolidState(object):
    def do_step(self):
        pass # boop

    def read_rgb(self):
        return

class SolidStep(DefaultStep):
    class meta:
        state = SolidState
        config = []# classes of base ConfigClass that implement configuration for a step
        # arrayfields, tuple of x-value-fields, enforced strings/ints/as typeOf(for any field)
        # kwargs for typeof include a required cnt | max_cnt | min_cnt
        # example
        # TupleField(of=Int(max=255), cnt=3)
        # ArrayField(of=String(max=64, max_cnt=4)