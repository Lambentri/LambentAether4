from enum import Enum

from autobahn.twisted.wamp import ApplicationSession
from twisted.internet.defer import inlineCallbacks
import txredisapi as redis

class RedisConfig(ApplicationSession):

    @inlineCallbacks
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        print("component created")
        self.rc = yield redis.Connection()

    # devices
    def device_list(self):
        pass

    def device_list_for_display(self, online_device_ids):
        pass

    def device_set_display(self, device_id, name):
        pass

    def device_set_last_seen(self, device_id, ts):
        pass

    # lambents
    def lambent_avail_list(self):
        pass # list all available and registered lambents

    def lambent_config_list(self, filtcls=None):
        pass

    def lambent_config_add(self, name, function, **kwargs):
        pass

    def lambent_config_rm(self, name):
        pass

    def lambent_config_reload_edit(self, name, **kwargs):
        pass  # possible to kick over a whirlygig?

    def lambent_config_copy(self, name):
        pass # copy an existing one to create a permuatation


class ConfigWidgetEnum(Enum):
    SWITCH = "sw"
    DROPDOWN = "dd"


class DeviceConfig(object):
    """
    A value that is configurable at runtime!
     AND programatically generates simple vue interfaces defined via "vue components"
     and referenced in the code in stackable meta class?
    """

class SwitchConfig(DeviceConfig):
    title = "BPP On Device"
    show_by_default = False
    default_value = 3
    widget = ConfigWidgetEnum.SWITCH

    def __init__(self, values=[], **kwargs):
        pass