from components.lambents.lib.machine import FakeMachine, TickEnum, RunningEnum


class ImportedFFM(FakeMachine):
    desc = "A Slow Fake"
    grps = ['fake', 'bake', 'jake']
    name = "SlowestFake"
    speed = TickEnum.HUNDREDTHS
    running = RunningEnum.RUNNING