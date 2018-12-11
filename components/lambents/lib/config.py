class ConfigException(Exception):
    pass

class ConfigClass:
    @classmethod
    def serialize(cls):
        raise NotImplementedError("ConfigClass children need to implement a serialize method (see TupleConfig)")


class TupleConfig(ConfigClass):
    def __init__(self, count, of_type, min=None, max=None):
        self.count = count
        self.of_type = of_type

        self.min = min
        self.max = max

    def validate(self, inputdata):
        if len(inputdata) > self.count:
            raise ConfigException(f"Tuple Expects At Most {self.count}")

        if not all([type(i) == self.of_type for i in inputdata]):
            raise ConfigException(f"Tuple Expects an array of {self.of_type}")

        if self.of_type in [int, float]:
            if self.min:
                if not all(i >= self.min for i in inputdata):
                    raise ConfigException(f"Tuple configured with a minimum value of {self.min}, one of your values is invalid")
            elif self.max:
                if not all(i <= self.max for i in inputdata):
                    raise ConfigException(f"Tuple configured with a maximum value of {self.max}, one of your values is invalid")
            elif self.min and self.max:
                if not all(self.min <= i <= self.max for i in inputdata):
                    raise ConfigException(
                        f"Tuple configured with a min value of {self.min} and a max value of {self.max}, one of your values is invalid")

        elif self.of_type in [str]:
            pass # some thing for min/max len

        return inputdata

    def serialize(self): # something like this
        return {
            "field_cnt": self.count,
            "field_validate": self.of_type.__name__
        }


class StringConfig(ConfigClass):
    pass
