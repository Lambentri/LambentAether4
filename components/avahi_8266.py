from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from zeroconf import ServiceBrowser, Zeroconf
import os
import socket
import sys


class ZeroConfSession(ApplicationSession):
    current_items = {}

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        print("component created")
        self.zeroconf = Zeroconf()
        self.listener = self
        self.browser = ServiceBrowser(self.zeroconf, "_ws2812._udp.local.", self.listener)


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
        return {"devices":self.current_items}

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))
        del self.current_items[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s, %s" % (name, info, type))
        print(socket.inet_ntoa(info.address))
        self.current_items[name] = {"address":socket.inet_ntoa(info.address), "name":name, "port":info.port}


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(ZeroConfSession)

    #TODO ADD FAKE AVAHI DEVICE