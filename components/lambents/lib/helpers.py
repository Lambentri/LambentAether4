import os
import random

from autobahn import wamp
from autobahn.twisted import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner


class HelperSession(ApplicationSession):
    """
    An ApplicationSession that generates various things
    """
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    def onJoin(self, details):
        print("joined")
        self.register(self)

    NAME_ADJECTIVES = [
        "Selective", "Purpouseful", "Glad", "Trill", "Flattered", "Frank", "Shining",
        "Tubular", "Glistening", "Soft", "Cool", "Warm", "Patterned", "Bombastic",
        "Gorgeous", "Snubby", "Blinky", "Hairy", "Handy", "Tall", "Short", "Thin", "Wide",
        "Cantankerous", "Belicose", "Beligerent", "Astute", "Solipsistic", "Greedy",
        "Minimal", "Fluffy", "Velvety", "Mellow", "Satin", "Hexagonal", "Shoddy", "Slapdash",
        "Matte", "Candid", "Deutsch", "Divine", "Fabulous", "Buen", "Chootia"

    ]
    NAME_NOUNS = [
        "Bulb", "Fire", "Pheonix", "Globe", "Nub", "Tuber", "Beam", "Beacon",
        "Aurora", "Blaze", "Flash", "Glare", "Gleam", "Glimmer", "Glint",
        "Glitter", "Glow", "Lumos", "Luster", "Ray", "Shine", "Star"
    ]

    @wamp.register("com.lambentri.edge.la4.helpers.namegen")
    def name_generator(self):
        return {"name":f"{random.choice(self.NAME_ADJECTIVES)}{random.choice(self.NAME_NOUNS)}"}

if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(HelperSession)