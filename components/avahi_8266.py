import itertools
import struct

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp import SubscribeOptions
from twisted.internet import task
from twisted.internet.defer import inlineCallbacks
from zeroconf import ServiceBrowser, Zeroconf
import os
import socket
import sys

from components.lambents.lib.decor import docupub
from components.lambents.lib.mixins import DocMixin
from components.library import chunks


class ZeroConfSession(DocMixin, ApplicationSession):
    regs = {}
    subs = {}
    grp = "sinks"

    current_items = {}
    zsubs = {}
    port = 7777

    HERALD_TICKS = .5
    HERALD_SRC = "8266-7777"

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        print("component created")
        self.zeroconf = Zeroconf()
        self.listener = self
        self.browser = ServiceBrowser(self.zeroconf, "_ws2812._udp.local.", self.listener)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    def onConnect(self):
        print("transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        print("authentication challenge received")

    @inlineCallbacks
    def onJoin(self, details):
        print("session joined")
        self.regs = yield self.register(self)
        self.subs = yield self.subscribe(self)
        self.document()

        self.ticker_herald = task.LoopingCall(self.device_herald)
        self.ticker_herald.start(self.HERALD_TICKS)

    def onLeave(self, details):
        print("session left")
        self.browser.cancel()
        print("give zeroconf some seconds to quit")
        self.zeroconf.close()
        os._exit(0)

    def onDisconnect(self):
        print("transport disconnected")

    @docupub(topics=["com.lambentri.edge.la4.machine.sink.8266-7777"], shapes={
        "com.lambentri.edge.la4.machine.sink.8266-7777": [{"iname": "str", "id": "topicstr", "name": "str"}]})
    @inlineCallbacks
    def device_herald(self):
        """Announces found devices every half second"""
        built = []
        for k, v in self.current_items.items():
            built.append({"iname": v['iname'], "id": f"com.lambentri.edge.la4.device.82667777.{k}",
                          "name": v.get('nname', v['name'].split('.', 1)[0])})
        yield self.publish("com.lambentri.edge.la4.machine.sink.8266-7777", res=built)

    @wamp.register("com.lambentri.edge.la4.zeroconf.8266")
    def get_list(self):
        """List all found devices"""
        return {"devices": self.current_items}

    @wamp.register("com.lambentri.edge.la4.device.82667777.name")
    def set_name(self, shortname: str, nicename: str):
        """Set a device's display name property """
        self.current_items[shortname]['nname'] = nicename

    # zeroconf methods
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))
        del self.current_items[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s, %s" % (name, info, type))
        print(socket.inet_ntoa(info.address))
        name_p = name.split('.', 1)[0]
        self.current_items[name_p] = {"address": socket.inet_ntoa(info.address), "name": name_p, "iname": name,
                                      "port": info.port}
        self.zsubs[name_p] = self.subscribe(self.udp_send, f"com.lambentri.edge.la4.device.82667777.{name_p}",
                                            options=SubscribeOptions(details_arg="details", correlation_id=name))
        print(self.zsubs)

    # udp methods
    def udp_send(self, message, details, id=None):
        # print(details)
        name = details.topic.rsplit('.', 1)[1]

        chunked = chunks(message, 3)
        filtered = [[rgbvals[1], rgbvals[0], rgbvals[2]] for rgbvals in chunked]
        values = list(itertools.chain.from_iterable(filtered))

        structd = struct.pack('B' * len(values), *values)
        self.socket.sendto(structd, (self.current_items[name]['address'], self.port))


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(ZeroConfSession)

    # TODO ADD FAKE AVAHI DEVICE
