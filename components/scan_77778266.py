from datetime import datetime

import ipaddress
import itertools
import netifaces
import os
import pytz
import socket
import struct

from autobahn import wamp
from autobahn.twisted import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import SubscribeOptions
from dataclasses import dataclass
from twisted.internet import task, threads, reactor
from twisted.internet.defer import inlineCallbacks

from components.lambents.lib.decor import docupub
from components.lambents.lib.mixins import DocMixin
from components.library import chunks

reactor.suggestThreadPoolSize(255)

@dataclass
class Item:
    address: str
    name: str
    port: int
    last_seen: datetime
    fullname: str = None
    nname: str = None

    def as_dict(self):
        return {"address": self.address, "name": self.name,"port":self.port,"last_seen":self.last_seen.isoformat(), "fullname": self.fullname, "nname":self.nname}


class ScanSession(DocMixin, ApplicationSession):
    SCAN_TICKS = 60
    HERALD_TICKS = 1
    HERALD_SRC = "8266-7777"
    PORT = 7777

    grp = "sinks"


    current_items = {}
    zsubs = {}

    PREFIXES_POP = ["lo", "br", "veth"]

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    @inlineCallbacks
    def onJoin(self, details):
        print("session joined")
        self.regs = yield self.register(self)
        self.subs = yield self.subscribe(self)
        self.document()

        self.ticker_herald = task.LoopingCall(self.device_herald)
        self.ticker_herald.start(self.HERALD_TICKS)

        self.ticker_finder = task.LoopingCall(self.setup_device_scan)
        self.ticker_finder.start(self.SCAN_TICKS)

    @docupub(topics=["com.lambentri.edge.la4.machine.sink.8266-7777"], shapes={
        "com.lambentri.edge.la4.machine.sink.8266-7777": [{"iname": "str", "id": "topicstr", "name": "str"}]})
    @inlineCallbacks
    def device_herald(self):
        """Announces found devices every half second"""
        built = []
        for k, v in self.current_items.items():
            built.append({"iname": v.name, "id": f"com.lambentri.edge.la4.device.82667777.{k}",
                          "name": v.nname or v.name})
        yield self.publish("com.lambentri.edge.la4.machine.sink.8266-7777", res=built)

    @wamp.register("com.lambentri.edge.la4.zeroconf.8266")
    def get_list(self):
        """List all found devices"""
        return {"devices": {k:v.as_dict()  for k,v in self.current_items.items()}}

    @wamp.register("com.lambentri.edge.la4.device.82667777.name")
    def set_name(self, shortname: str, nicename: str):
        """Set a device's display name property """
        self.current_items[shortname]['nname'] = nicename

    # udp methods
    def udp_send(self, message, details, id=None):
        # print(details)
        name = details.topic.rsplit('.', 1)[1]
        if name.isdigit():
            name = ".".join(details.topic.rsplit('.', 4)[1:])

        chunked = chunks(message, 3)
        filtered = [[rgbvals[1], rgbvals[0], rgbvals[2]] for rgbvals in chunked]
        values = list(itertools.chain.from_iterable(filtered))

        structd = struct.pack('B' * len(values), *values)
        self.socket.sendto(structd, (self.current_items[name].address, self.PORT))

    def err_device_scan(self, *args, **kwargs):
        pass
        print("err")
        print(args)

    @inlineCallbacks
    def save_device_scan(self, result):
        if result:
            print("result")
            try:
                hostname_data = socket.gethostbyaddr(result)[0]
                if "_" not in hostname_data:
                    return # we only care about stuff with esp_ in the hostname
                # hostname_data_short = hostname_data.split('.', 1)[0]
                hostname_data_short = result
            except Exception as e:
                print(e)
                hostname_data = result
                hostname_data_short = result


            if hostname_data_short in self.current_items:
                # only update the last-seen
                self.current_items[hostname_data_short].last_seen = datetime.now(pytz.utc)
            else:
                new_item = Item(address=result, name=hostname_data_short, fullname=hostname_data, port=7777, last_seen=datetime.now(pytz.utc))
                print(new_item)
                self.current_items[hostname_data_short] = new_item

                self.zsubs[hostname_data_short] = yield self.subscribe(self.udp_send, f"com.lambentri.edge.la4.device.82667777.{hostname_data_short}",
                                                  options=SubscribeOptions(details_arg="details", correlation_id=hostname_data_short))
                print(self.zsubs)

    def do_device_scan(self, ip:str):
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # scan if device is open on port 80/tcp
        # print("doscan 80", ip)
        result = sock_tcp.connect_ex((ip, 80))
        if result == 0:
            sock_tcp.close()

            if os.system(f'nc -vnzu {ip} 7777') == 0:
                return ip

        sock_tcp.close()

    def setup_device_scan(self):
        print("scanning")
        ifaces_list: list[str] = netifaces.interfaces()
        ifaces_trimmed = [i for i in ifaces_list if not any([i.startswith(j) for j in self.PREFIXES_POP])]
        for iface in ifaces_trimmed:
            iface_info = netifaces.ifaddresses(iface)
            try:
                addrs_inet = iface_info[netifaces.AF_INET]
            except KeyError:
                continue
            for addr in addrs_inet:
                addr_obj = ipaddress.ip_network((addr['addr'],addr['netmask']), strict=False)
                addr_hosts = addr_obj.hosts()
                for host in addr_hosts:
                    if host in self.current_items:
                        print(f"{host} is in our list, avoiding booming it again")
                        continue # avoid tickling stuff we already know about, #TODO add a timer for long term scanning
                    d = threads.deferToThread(self.do_device_scan, ip=str(host))
                    d.addCallback(self.save_device_scan)
                    d.addErrback(self.err_device_scan)


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8083/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(ScanSession, auto_reconnect=True)
