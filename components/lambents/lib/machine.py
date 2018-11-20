from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn import wamp
from enum import Enum
import os
import txaio
from marshmallow import fields
from marshmallow.schema import Schema
from marshmallow_enum import EnumField
from twisted.internet import task

# enums

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
    speed = EnumField(TickEnum)
    running = EnumField(RunningEnum)
    foo = fields.Str()

class MachineDictSerializer(Schema):
    machines = ComposableDict(fields.Nested(MachineSerializer))
    speed_enum = fields.Dict(keys=fields.Str(), values=fields.Number())
# machines
class FakeMachine(object):
    pass

class SlowFakeMachine(FakeMachine):
    name = "SlowFake"
    speed = TickEnum.ONES
    running = RunningEnum.RUNNING
    foo = "k"

class FastFakeMachine(FakeMachine):
    name = "FastFake"
    speed = TickEnum.TENTHS
    running = RunningEnum.NOTRUNNING
    foo = "l"

class LambentMachine(ApplicationSession):
    tickers = {}
    machines = {"a.b": SlowFakeMachine(), "c.d":FastFakeMachine()}

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

    def do_tick(self, enum: TickEnum):
        operating_machines = filter(lambda x:x.speed==enum, self.machines.values())
        for mach in operating_machines:
            pass
            print(mach.__class__)
            print(mach.running)

    def change_machine_ticks(self, machine_name: str, machine_tick: TickEnum):
        pass  # changes the value of the tick enum on the machine

    @wamp.register("com.lambentri.edge.la4.machine.tick_up")
    def machine_tick_up(self, machine_name):
        mach = self.machines.get(machine_name)
        mach.speed = mach.speed.next_up(mach.speed)
        return {"speed":mach.speed.name}

    @wamp.register("com.lambentri.edge.la4.machine.tick_dn")
    def machine_tick_dn(self, machine_name):
        mach = self.machines.get(machine_name)
        mach.speed = mach.speed.next_dn(mach.speed)
        return {"speed":mach.speed.name}

    @wamp.register("com.lambentri.edge.la4.machine.init")
    def init_machine_instance(self, machine_cls, machine_kwargs={}):
        # this is called on startup as well as when adding new configs
        pass

    @wamp.register("com.lambentri.edge.la4.machine.edit")
    def modify_machine_instance(self):
        # this allows you to change execution parameters on a machine and restart it
        pass

    @wamp.register("com.lambentri.edge.la4.machine.paus")
    def pause_machine(self):
        # sets machine to paused
        pass

    @wamp.register("com.lambentri.edge.la4.machine.rm")
    def destroy_machine(self):
        # deletes machine (from live/redis instance)
        pass

    @wamp.register("com.lambentri.edge.la4.machine.list")
    def list_active_machine_instances(self):
        schema = MachineDictSerializer()
        # print(self.machines)
        serialized = schema.dump({"machines":self.machines, "speed_enum":{k:v.value for k,v in TickEnum.__members__.items()}})
        return serialized.data

    @wamp.register("com.lambentri.edge.la4.machine.ticks")

    def onJoin(self, details):
        print("joined")
        self.register(self)


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(LambentMachine)