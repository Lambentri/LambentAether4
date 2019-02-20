import importlib
import pydoc

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn import wamp
from enum import Enum
import os
import txaio
from autobahn.wamp.types import PublishOptions
from marshmallow import fields
from marshmallow.schema import Schema
from marshmallow_enum import EnumField
from twisted.internet import task


# enums
from twisted.internet.defer import inlineCallbacks


class TickEnum(Enum):
    HUNDREDTHS = .01
    FHUNDREDTHS = .05
    TENTHS = .1
    FTENTHS = .5
    ONES = 1
    TWOS = 2
    FIVES = 5
    TENS = 10
    TWENTYS = 20
    THIRTHYS = 30
    MINS = 60

    def _get_index(self, value):
        members = [i.value for i in TickEnum.__members__.values()]
        return members.index(value.value)

    def _value_from_index(self, index: int):
        members = list(TickEnum.__members__.values())
        return members[index]

    def next_up(self, value):
        if value == self.MINS:
            return TickEnum.MINS
        index = self._get_index(value) + 1
        return self._value_from_index(index)

    def next_dn(self, value):
        if value == self.HUNDREDTHS:
            return TickEnum.HUNDREDTHS
        index = self._get_index(value) - 1
        return self._value_from_index(index)


class RunningEnum(Enum):
    RUNNING = True
    NOTRUNNING = False


# serialization
class ComposableDict(fields.Dict):

    def __init__(self, inner, *args, **kwargs):
        self.inner = inner
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj):
        return {
            key: self.inner._serialize(val, key, value)
            for key, val in value.items()
        }


class MachineSerializer(Schema):
    name = fields.Str()
    iname = fields.Str()
    speed = EnumField(TickEnum)
    running = EnumField(RunningEnum)
    id = fields.Str()
    desc = fields.Str()


class MachineDictSerializer(Schema):
    machines = ComposableDict(fields.Nested(MachineSerializer))
    speed_enum = fields.Dict(keys=fields.Str(), values=fields.Number())


# machines
class FakeMachine(object):
    def step(self):
        return [0,0,0]


class SlowFakeMachine(FakeMachine):
    name = "SlowFake"
    speed = TickEnum.ONES
    running = RunningEnum.RUNNING
    desc = """
A fake machine that just runs without doing anything in particular, slowly
    """
    grps = ["fake", "make"]
    id = "FakexFakeSlow"


class FastFakeMachine(FakeMachine):
    name = "FastFake"
    speed = TickEnum.TENTHS
    running = RunningEnum.NOTRUNNING
    desc = """
    A fake machine that just runs without doing anything in particular, faster
    """

    grps = ["fake", "bake"]
    id = "FakeXFakeFast"


class LambentMachine(ApplicationSession):
    tickers = {}
    machines = {"SlowFakeMachine-a.b": SlowFakeMachine(), "FastFakeMachine-c.d": FastFakeMachine()}
    machine_library = [
        SlowFakeMachine,
        FastFakeMachine,
        "lambents.solids.SolidStep",
        "lambents.solids.SolidStepHSV",
        "lambents.solids.SolidStepHSBBBB"
    ]

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        txaio.start_logging()

        # get redis from config
        # check for passed in config file
        # if no redis/config, try and find the default config file

        # start the tick runner(s). There is one for each of the speeds
        # The tick runner will iterate through all machines and find machines set to the specific enum
        # and step them along ever X seconds
        self._init_timers()

        # In all config cases, then check for machine instances to spin up and spin them out

        # make sure to handle machine funk and log effectively:
        # One crashing machine should not kill the component.
        # Code changes that break configs should not kill the component

        # in the redis config mode, changes to machines are stored in redis for persistence automatically
        # in the file config mode, the persistence save calls are made by function call and (maybe have history?

    def _init_timers(self):
        for enum in TickEnum:
            self.tickers[enum] = task.LoopingCall(self.do_tick, enum=enum)
            self.tickers[enum].start(enum.value)

        print("alll timers initd")

    @inlineCallbacks
    def do_tick(self, enum: TickEnum):
        # print(self.machines.values())
        operating_machines = filter(lambda x: x.speed.value == enum.value and x.running.value == RunningEnum.RUNNING.value, self.machines.values())
        # print(operating_machines)
        for mach in operating_machines:

            res = mach.step()
            # print(mach.speed.value == TickEnum.TENS.value)
            if mach.speed.value == TickEnum.TENS.value:
                # print(res)
                print(vars)
                print(vars(mach))

                # yield self.publish(f"com.lambentri.edge.la4.machine.link.srx.{mach.id}", res)
                # yield self.publish(f"com.lambentri.edge.la4.device.82667777.esp_0602a5", res)
            # print(res[0:12])
            options = PublishOptions(retain=True)
            yield self.publish(f"com.lambentri.edge.la4.machine.link.src.{mach.id}", res, id=mach.id, options=options)

    def change_machine_ticks(self, machine_name: str, machine_tick: TickEnum):
        pass  # changes the value of the tick enum on the machine

    def _find_class_in_library(self, name):
        for item in self.machine_library:
            if isinstance(item, str):
                try:
                    mod = pydoc.locate("components." + item)
                    if mod.__name__ == name:
                        return mod
                except:
                    pass
            elif issubclass(item, FakeMachine):
                if item.__name__ == name:
                    return item

        else:
            raise Exception(f"Unable to locate a lighting class named '{name}'")

    @wamp.register("com.lambentri.edge.la4.machine.tick_up")
    def machine_tick_up(self, machine_name):
        mach = self.machines.get(machine_name)
        mach.speed = mach.speed.next_up(mach.speed)
        return {"speed": mach.speed.name}

    @wamp.register("com.lambentri.edge.la4.machine.tick_dn")
    def machine_tick_dn(self, machine_name):
        mach = self.machines.get(machine_name)
        mach.speed = mach.speed.next_dn(mach.speed)
        return {"speed": mach.speed.name}

    @wamp.register("com.lambentri.edge.la4.machine.library")
    def machine_library_retrieve(self):
        machine_ret = {}
        for item in self.machine_library:
            if isinstance(item, str):
                # print(item)
                # TODO cache this
                try:
                    component_name = f"components.{item}"
                    # print(component_name)
                    mod = pydoc.locate(component_name)
                    machine_ret[mod.name] = {
                        "desc": mod.desc,
                        "cls": mod.__name__,
                        "grp": mod.grps,
                        "conf": mod.get_config()
                    }
                except AttributeError as e:

                    print(f"Unable to find machine of class '{item}'")
                    # print(e)
                pass  # import inplace and inspect to get k:v
            elif issubclass(item, FakeMachine):
                machine_ret[item.name] = {
                    "desc": item.desc,
                    "cls": item.__name__,
                    "grp": item.grps,
                    "conf": {}
                }
            else:
                print("unknown")
                print(type(item))

        return machine_ret

    # @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.machine.init")
    def init_machine_instance(self, machine_cls: str, machine_name: str, machine_kwargs={}):
        # this is called on startup as well as when adding new configs
        print(machine_cls)
        cls = self._find_class_in_library(machine_cls)
        print(machine_kwargs)
        print(machine_name)
        print(cls.__name__)

        # build kwargs for cls
        built_kwargs = {}
        for k,v in cls.meta.config.items():
            print(k,v)
            print(v['cls'].serialize().items())
            if v['cls'].serialize()['name'] == "TupleConfig":
                matching_config = [vi for ki,vi in machine_kwargs.items() if ki.startswith(k + "-")]
                built_kwargs[k] = tuple(matching_config)
        id = f"{cls.__name__}-x-{machine_name}"
        mach = cls(config_params=built_kwargs)
        mach.set_id(id)
        mach.set_instance_name(machine_name)
        self.machines[id] = mach
        res = self.machines[id].step()
        print(res)
        # yield self.publish(f"com.lambentri.edge.la4.device.82667777.esp_0602a5", res)

    @wamp.register("com.lambentri.edge.la4.machine.edit")
    def modify_machine_instance(self):
        # this allows you to change execution parameters on a machine and restart it
        pass

    @wamp.register("com.lambentri.edge.la4.machine.pause")
    def pause_machine(self, machine_name):
        mach = self.machines.get(machine_name)
        if mach.running == RunningEnum.RUNNING:
            mach.running = RunningEnum.NOTRUNNING
        else:
            mach.running = RunningEnum.RUNNING
        return {"running": mach.running.name}

    @wamp.register("com.lambentri.edge.la4.machine.rm")
    def destroy_machine(self, machine_name):
        try:
            del self.machines[machine_name]
        except:
            print(f"Someone attempted to delete a machine that doesn't exist : {machine_name}")
        # deletes machine (from live/redis instance)
        schema = MachineDictSerializer()
        serialized = schema.dump(
            {"machines": self.machines, "speed_enum": {k: v.value for k, v in TickEnum.__members__.items()}})
        return serialized.data

    # pass
    @wamp.register("com.lambentri.edge.la4.machine.list")
    def list_active_machine_instances(self):
        schema = MachineDictSerializer()
        # print(self.machines)
        serialized = schema.dump(
            {"machines": self.machines, "speed_enum": {k: v.value for k, v in TickEnum.__members__.items()}})
        return serialized.data


    # links
    @wamp.register("com.lambentri.edge.la4.manifold.create")
    def manifold_create(self):
        """Creates a manifold to route and combine various sources / links / devices via virtual manifolds"""
        pass

    def onJoin(self, details):
        print("joined")
        self.register(self)

    @wamp.register("com.lambentri.edge.la4.links.list")
    def list_links(self):
        pass


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(LambentMachine)
