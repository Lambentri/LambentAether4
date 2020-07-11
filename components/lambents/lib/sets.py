import os

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

from enum import Enum

#
# Machine -> Link -> Group -> Zone
from typing import List, Dict, Set
from dataclasses import dataclass
from twisted.internet.defer import inlineCallbacks

from components.lambents.lib.machine import BrightnessEnum
from components.lambents.lib.mixins import DocMixin


@dataclass
class ZoneSpec:
    name: str
    details: str
    filters: List[str]
    devices: Set[str]
    brightness: BrightnessEnum = BrightnessEnum.FULL

    def as_dict(self):
        return {
            "name": self.name,
            "details": self.details,
            "filters": self.filters,
            "devices": self.devices,
            "brightness": self.brightness.name,
        }


class ZoneHelper(DocMixin, ApplicationSession):
    """
    Zones are meant to represent physical areas where devices reside

    - zones can have filters (RGB->GRB, etc)
    - zones can have a global brightness value

    Zones are the final step applied before being shuffled off to the device writers
    """
    grp = "sets"
    zones: Dict[str, ZoneSpec]

    @wamp.register("com.lambentri.edge.la4.sets.zone.list")
    def zone_list(self):
        return [zone.as_dict() for zone in self.zones]

    @wamp.register("com.lambentri.edge.la4.sets.zone.add")
    def zone_add(self, name: str, details: str):
        self.zones[name] = ZoneSpec(name=name, details=details)

    @wamp.register("com.lambentri.edge.la4.sets.zone.rm")
    def zone_rm(self, name: str):
        try:
            del self.zones[name]
        except:
            pass

    @wamp.register("com.lambentri.edge.la4.sets.zone.assign")
    def zone_assign(self, name: str, device: str):
        if name in self.zones:
            self.zones[name].devices.add(device)

    @wamp.register("com.lambentri.edge.la4.sets.zone.unassign")
    def zone_unassign(self, name: str, device: str):
        if name in self.zones:
            self.zones[name].devices.remove(device)

    @wamp.register("com.lambentri.edge.la4.sets.zone.brightness.status")
    def zone_brightness_status(self):
        """All the brightness statuses for all the zones"""
        return [{"name": zone.name, "brightness": zone.brightness.name} for zone in self.zones.values()]

    @wamp.register("com.lambentri.edge.la4.sets.zone.brightness.up")
    def zone_brightness_up(self, name: str):
        if name in self.zones:
            self.zones[name].brightness.next_up(self.zones[name].brightness)
            return {"brightness": self.brightness.value}

    @wamp.register("com.lambentri.edge.la4.sets.zone.brightness.dn")
    def zone_brightness_dn(self, name: str):
        if name in self.zones:
            self.zones[name].brightness.next_dn(self.zones[name].brightness)
            return {"brightness": self.brightness.value}

    @wamp.register("com.lambentri.edge.la4.sets.zone.brightness.set")
    def zone_brightness_set(self, name: str, value: int):
        self.zones[name].brightness = BrightnessEnum(value)

        return {"brightness": self.brightness.value}

    @wamp.register("com.lambentri.edge.la4.sets.zone.filter.status")
    def zone_filter_status(self):
        """All filters all zones all the time"""
        return [{"name": zone.name, "filters": zone.filters} for zone in self.zones.values()]

    @wamp.register("com.lambentri.edge.la4.sets.zone.filter.list")
    def zone_filter_list(self):
        """List the available filters"""
        pass

    @wamp.register("com.lambentri.edge.la4.sets.zone.filter.add")
    def zone_filter_add(self, name: str, filt: str, position: int = 0):
        if name in self.zones:
            self.zones[name].filters.insert(position, filt)

    @wamp.register("com.lambentri.edge.la4.sets.zone.filter.rm")
    def zone_filter_rm(self, name: str, position: int):
        if name in self.zones:
            self.zones[name].filters.pop(position)

    @wamp.register("com.lambentri.edge.la4.sets.zone.filter.move")
    def zone_filter_move(self, name: str, position: int, direction_up: bool):
        if name in self.zones:
            if direction_up:
                self.zones[name].filters[position], self.zones[name].filters[position+1] = self.zones[name].filters[position+1], self.zones[name].filters[position]
            else:
                self.zones[name].filters[position], self.zones[name].filters[position - 1] = self.zones[name].filters[position - 1], self.zones[name].filters[position]

            return self.zones[name].filters

    @inlineCallbacks
    def onJoin(self, details):
        print("joined")
        self.regs = yield self.register(self)
        self.document()

@dataclass
class GroupSpec:
    name: str
    devices: List[str]


class GroupHelper(ApplicationSession):
    """
    Groups are routing elements for grouping devices to receive the same datastream

    Adding a device to a group disables all links to it and vice versa
    """
    groups: Dict[str, GroupSpec]

    @wamp.register("com.lambentri.edge.la4.sets.group.list")
    def group_list(self):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.group.add")
    def group_add(self, name: str, devices: list):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.group.rm")
    def group_rm(self, name: str):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.group.assign")
    def group_assign(self, name: str, device: str):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.group.unassign")
    def group_unassign(self, name: str, device: str):
        pass


class FusorMode(Enum):
    TICK = "tick"
    LIVE = "live"


@dataclass
class FusorSource:
    id: str
    # indices
    start: int
    end: int


@dataclass
class FusorSpec:
    name: str
    details: str
    sources: List[FusorSource]
    mode: FusorMode


class FusorHelper(ApplicationSession):
    """
    Fusors take on multiple sources and combine them into a single datastream.
    Fusors maintain an internal state and have two modes:
    - Tick - Every configurable tick emit the internal state
    - Live - On every update from registered sources

    Upon assigning a range any conflicting ranges are trimmed or removed entirely
    On unassign, the values for the given range are set to return the fusor's default empty value, black

    """
    fusors: Dict[str, FusorSpec]

    @wamp.register("com.lambentri.edge.la4.sets.fusor.list")
    def fusor_list(self):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.fusor.add")
    def fusor_add(self, name):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.fusor.rm")
    def fusor_rm(self, name: str):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.fusor.assign")
    def fusor_assign(self, name: str, source: str, start_index: int, end_index: int):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.fusor.unassign")
    def fusor_unassign(self, name: str, source: str):
        pass

    @wamp.register("com.lambentri.edge.la4.sets.fusor.mode")
    def fusor_toggle(self, name: str, mode: str):
        pass

if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8083/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(ZoneHelper, auto_reconnect=True)