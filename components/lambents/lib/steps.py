class DefaultStep(object):
    class meta:
        state = None
    def __init__(self, led_count: int=150):
        state = self.meta.state
        self.leds = [state()] # tbd

    def step(self):
        new_buffer = []
        for led in self.leds:
            led.do_step()
            state = led.read_rgb()
            new_buffer.extend(state)

        return new_buffer