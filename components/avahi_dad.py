from autobahn.twisted.wamp import ApplicationSession


class ZeroConfDad(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        print("component created")