import os
from enum import Enum

import txaio
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from twisted.internet import task


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

class FakeMachine(object):
    pass

class SlowFakeMachine(FakeMachine):
    speed = TickEnum.ONES

class FastFakeMachine(FakeMachine):
    speed = TickEnum.TENTHS

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
            print(mach.__class__)

    def change_machine_ticks(self, machine_name: str, machine_tick: TickEnum):
        pass  # changes the value of the tick enum on the machine

    def init_machine_instance(self):
        # this is called on startup as well as when adding new configs
        pass

    def modify_machine_instance(self):
        # this allows you to change execution parameters on a machine and restart it
        pass

    def pause_machine(self):
        # sets machine to paused
        pass

    def destroy_machine(self):
        # deletes machine (from live/redis instance)
        pass

    def list_active_machine_instances(self):
        # lists machines and the current config params
        pass


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(LambentMachine)