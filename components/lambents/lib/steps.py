class DefaultStep(object):
    class meta:
        state = None
    def __init__(self, config_params, led_count: int=150):
        state = self.meta.state
        kwargs = state.validate(self.meta.config, config_params)
        self.leds = [state(kwargs) for i in led_count] # tbd


    def step(self):
        new_buffer = []
        for led in self.leds:
            led.do_step()
            state = led.read_rgb()
            new_buffer.extend(state)

        print(new_buffer)
        return new_buffer

    @classmethod
    def get_config(self):
        """ returns a configuration dictionary if one exists """
        if hasattr(self, "meta"):
            if hasattr(self.meta, "config"):
                config = self.meta.config

                for k,v in config.items():
                    if hasattr(v['cls'], "serialize"):
                        config[k]['cls'] = v['cls'].serialize()
                # some serialization step should occur here, likely check the each object for
                # an instance type and grab a serializer embedded in each configClass
                return config
        return {}
