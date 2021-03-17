from typing import List

import os
from autobahn.asyncio import ApplicationSession
from autobahn.asyncio.wamp import ApplicationRunner
from bleak import BleakClient, BleakScanner
from twisted.internet.defer import inlineCallbacks
from twisted.internet import task, threads, reactor

from components.lambents.lib.mixins import DocMixin
import txredisapi as redis



class BLEScanSession(DocMixin, ApplicationSession):
    WRITE_TICKS: int = 60
    SCAN_TICKS: int = 300
    client: BleakClient
    scanner: BleakScanner

    found_devices: set = set()
    tracked_devices: set = set()
    auto_prefixes: set = set()

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    async def onJoin(self, details):
        # client = BleakClient()
        scanner = BleakScanner()

        if os.environ.get('LA4_REDIS'):
            print("Yay a redis")
            self.redis = await redis.Connection(os.environ.get("LA4_REDIS"), 6379, 13)
            self.config_writer = task.LoopingCall(self.write_names)
            self.config_writer.start(self.WRITE_TICKS, now=False)

            # read config and add macs to library
            self.auto_prefixes = self.redis.get()

        # self.scan_runner = task.LoopingCall(self.do_scan())
        # self.scan_runner.start(self.SCAN_TICKS)
        # d = threads.deferToThread(self.do_scan)
        # d.addCallback(self.save_device_scan)
        # d.addErrback(self.err_device_scan)
        await self.do_scan()

    async def do_scan(self):
        print("scanning")
        result = await self.scanner.discover()
        for d in result:
            print(d)

    def save_device_scan(self, results: List):
        pass

    def err_device_scan(self, *args, **kwargs):
        print("err")
        print(args)

    def write_config(self):
        pass

if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8083/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(BLEScanSession)