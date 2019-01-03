import itertools
import struct

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp import SubscribeOptions
from zeroconf import ServiceBrowser, Zeroconf
import os
import socket
import sys

from components.library import chunks


class ZeroConfSession(ApplicationSession):
    current_items = {}
    subs = {}
    port = 7777

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

    def onJoin(self, details):
        print("session joined")
        self.register(self)

    def onLeave(self, details):
        print("session left")
        self.browser.cancel()
        self.zeroconf.close()
        sys.exit(0)

    def onDisconnect(self):
        print("transport disconnected")

    @wamp.register("com.lambentri.edge.la4.zeroconf.8266")
    def get_list(self):
        return {"devices": self.current_items}

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))
        del self.current_items[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s, %s" % (name, info, type))
        print(socket.inet_ntoa(info.address))
        name_p = name.split('.', 1)[0]
        self.current_items[name_p] = {"address": socket.inet_ntoa(info.address), "name": name, "port": info.port}
        self.subs[name_p] = self.subscribe(self.udp_send, f"com.lambentri.edge.la4.device.82667777.{name_p}",
                                           options=SubscribeOptions(details_arg="details", correlation_id=name))
        print(self.subs)

    def udp_send(self, message, details):
        print(details)
        name = details.topic.rsplit('.', 1)[1]

        chunked = chunks(message, 3)
        filtered = [[rgbvals[1], rgbvals[0], rgbvals[2]] for rgbvals in chunked]
        values = list(itertools.chain.from_iterable(filtered))

        structd = struct.pack('B' * len(values), *values)
        self.socket.sendto(structd, (self.current_items[name]['address'], self.port))
        # self.socket.sendto()


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(ZeroConfSession)

    # TODO ADD FAKE AVAHI DEVICE
