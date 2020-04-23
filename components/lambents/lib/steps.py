from copy import deepcopy


class DefaultStep(object):
    id = None
    iname = None
    class meta:
        state = None
    def __init__(self, config_params, led_count: int=256, set_status=False):
        state = self.meta.state
        kwargs = state.validate(self.meta.config, config_params)
        if not set_status:
            self.leds = [state(**kwargs) for i in range(led_count)] # tbd
        else:
            self.leds = [state(**kwargs, status=i) for i in range(led_count)]  # tbd



    def step(self):
        new_buffer = []
        for led in self.leds:
            led.do_step()
            state = led.read_rgb()
            new_buffer.extend(state)

        # print(new_buffer)
        return new_buffer

    def set_id(self, id): # We do this after init in machine invocation to keep the __init__ clear
        self.id = id

    def set_instance_name(self, name):
        self.iname = name

    @classmethod
    def get_config(self, do_serialize=True):
        """ returns a configuration dictionary if one exists """
        if hasattr(self, "meta"):
            if hasattr(self.meta, "config"):
                config = deepcopy(self.meta.config)

                for k,v in config.items():
                    if hasattr(v['cls'], "serialize") and do_serialize:
                        config[k]['cls'] = v['cls'].serialize()
                    else:
                        config[k]['cls'] = v['cls']
                # some serialization step should occur here, likely check the each object for
                # an instance type and grab a serializer embedded in each configClass
                # print(config)
                return config
        return {}
