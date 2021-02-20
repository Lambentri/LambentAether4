from components.lambents.lib.mixins import DocMixin
from autobahn.twisted import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner


class FilterSession(DocMixin, ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)