class ConfigException(Exception):
    pass

class ConfigClass:
    @classmethod
    def serialize(cls):
        raise NotImplementedError("ConfigClass children need to implement a serialize method (see TupleConfig)")


class TupleConfig(ConfigClass):
    def __init__(self, count, of_type, min=None, max=None, default=None, titles=()):
        self.count = count
        self.of_type = of_type

        self.min = min
        self.max = max
        self.default = default
        self.field_titles = titles

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

    @property
    def field_title_for_s(self):
        if self.field_titles:
            return self.field_titles
        else:
            return tuple(f"Field {i}" for i in range(self.count))

    def serialize(self): # something like this
        return {
            "name": "TupleConfig",
            "field_cnt": self.count,
            "field_type": self.of_type.__name__,
            "field_titles": self.field_title_for_s,
            "field_validation": {
                "min": self.min,
                "max": self.max
            },
            "field_default": self.default or []
        }

class ArrayConfig(ConfigClass):
    def __init__(self, of_type, min_count=2, max_count=None, min=None, max=None, default=None, titles=()):
        self.of_type = of_type

        self.min_count=min_count
        self.max_count=max_count
        self.min = min
        self.max = max
        self.default = default
        self.field_titles = titles

    def validate(self, inputdata):
        if self.min_count and len(inputdata) < self.min_count:
            raise ConfigException(f"Array Expects At Most {self.min_count} Objects")
        if self.max_count and len(inputdata) > self.max_count:
            raise ConfigException(f"Tuple Expects At Most {self.max_count} Objects")

        if not all([type(i) == self.of_type for i in inputdata]):
            raise ConfigException(f"Tuple Expects an array of {self.of_type}")

        if self.of_type in [int, float]:
            if self.min:
                if not all(i >= self.min for i in inputdata):
                    raise ConfigException(f"Array configured with a minimum value of {self.min}, one of your values is invalid")
            elif self.max:
                if not all(i <= self.max for i in inputdata):
                    raise ConfigException(f"Array configured with a maximum value of {self.max}, one of your values is invalid")
            elif self.min and self.max:
                if not all(self.min <= i <= self.max for i in inputdata):
                    raise ConfigException(
                        f"Array configured with a min value of {self.min} and a max value of {self.max}, one of your values is invalid")

        elif self.of_type in [str]:
            pass # some thing for min/max len

        return inputdata

    def serialize(self): # something like this
        return {
            "name": "ArrayConfig",
            "field_cnt": self.count,
            "field_type": self.of_type.__name__,
            "field_titles": self.field_title_for_s,
            "field_validation": {
                "min": self.min,
                "max": self.max,
                "min_count": self.min_count,
                "max_count": self.max_count
            },
            "field_default": self.default or []
        }


class IntegerConfig(ConfigClass):
    def __init__(self, min=None, max=None, default=None, titles="IntegerConfig"):
        self.min = min
        self.max = max
        self.default = default
        self.field_titles = titles

    def serialize(self): # something like this
        return {
            "name": "IntegerConfig",
            "field_titles": [self.field_titles],
            "field_validation": {
                "min": self.min,
                "max": self.max
            },
            "field_default": self.default or []
        }

    def validate(self, inputdata):
        if self.min:
            if inputdata < self.min:
                raise ConfigException(
                    f"Integer configured with a minimum value of {self.min}, one of your values is invalid")
        elif self.max:
            if inputdata > self.max:
                raise ConfigException(
                    f"Integer configured with a maximum value of {self.max}, one of your values is invalid")
        elif self.min and self.max:
            if inputdata < self.min or inputdata > self.max:
                raise ConfigException(
                    f"Integer configured with a min value of {self.min} and a max value of {self.max}, one of your values is invalid")
        return inputdata

class StringConfig(ConfigClass):
    pass

class BooleanConfig(ConfigClass):
    def __init__(self, default=True, titles="BooleanConfig"):
        self.default = default
        self.field_titles = titles

    def serialize(self): # something like this
        return {
            "name": "BooleanConfig",
            "field_titles": [self.field_titles],
            "field_validation": {},
            "field_default": self.default or True
        }

    def validate(self, inputdata):
        if inputdata not in [True, False]:
            raise ConfigException(f"Boolean Configured with something that ain't a boolean")
        return inputdata