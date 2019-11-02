import os
import random

from autobahn import wamp
from autobahn.twisted import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import PublishOptions
from twisted.internet import task
from twisted.internet.defer import inlineCallbacks

from components.lambents.lib.decor import docupub
from components.lambents.lib.mixins import DocMixin

DOC_LISTENER_URI = "com.lambentri.edge.la4.doc"


class HelperSession(DocMixin, ApplicationSession):
    """
    An ApplicationSession that generates various things
    """
    help_documents = {}
    regs = None
    subs = None
    grp = "helpers"

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    @inlineCallbacks
    def onJoin(self, details):
        print("joined")
        self.regs = yield self.register(self)
        self.subs = yield self.subscribe(self)
        self.wamp = wamp
        self.document()

        # publish an updated documentation description every 10 seconds
        self.docpub = task.LoopingCall(self.document_publisher)
        self.docpub.start(3)

        self.compub = task.LoopingCall(self.component_publisher)
        self.compub.start(3)
        # remove this when we're done
        # self.testpub = task.LoopingCall(self._test_publish_docs)
        # self.testpub.start(30)

    # @inlineCallbacks
    # def _test_publish_docs(self):
    #     pub_options = PublishOptions(
    #         acknowledge=True,
    #         exclude_me=False
    #     )
    # yield self.publish(
    #     DOC_LISTENER_URI,
    #     component_name="tick_up",
    #     component_doc="""An endpoint that ticks up the speed of the given machine by one step
    #             """,
    #     component_topic="com.lambentri.edge.la4.machine.tick_up",
    #     component_grp="machine",
    #     component_type="call",
    #     component_schema={
    #         "kwargs": {"machine_name": "str"},
    #         "return": {"speed": "SpeedEnum"}
    #     },
    #     options=pub_options
    # )
    #
    # yield self.publish(
    #     DOC_LISTENER_URI,
    #     component_name="machine.sink",
    #     component_doc="""A prefix that is listening for various available target machine types to announce themselves
    #     """,
    #     component_topic="com.lambentri.edge.la4.machine.sink.",
    #     component_grp="sinks",
    #     component_type="sink",
    #     component_schema={
    #         "kwargs": {},
    #         "return": {}
    #     },
    #     options=pub_options
    # )
    #
    # yield self.publish(
    #     DOC_LISTENER_URI,
    #     component_name="toggle_link",
    #     component_doc="""Toggles a link on, will disable all others that are pointing to a given device / src""",
    #     component_topic="com.lambentri.edge.la4.links.toggle",
    #     component_grp="links",
    #     component_type="call",
    #     component_schema={
    #         "kwargs": {"link_name": "str"},
    #         "return": None
    #     },
    #     options=pub_options
    # )
    #
    # yield self.publish(
    #     DOC_LISTENER_URI,
    #     component_name="namegen",
    #     component_doc="""Generates Whimsical Names""",
    #     component_topic="com.lambentri.edge.la4.helpers.namegen",
    #     component_grp="helpers",
    #     component_type="call",
    #     component_schema={
    #         "kwargs": None,
    #         "return": {"name": "str"}
    #     },
    #     options=pub_options
    # )

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
        """
        Generates whimsical names
        """
        return {"name": f"{random.choice(self.NAME_ADJECTIVES)}{random.choice(self.NAME_NOUNS)}"}

    # documentation parts
    @wamp.subscribe(DOC_LISTENER_URI)
    def document_collector(self, component_name: str, component_doc: str, component_topic: str, component_grp: str,
                           component_type: str,
                           component_schema: str, **kwargs):
        """Recieves Documents"""
        print(f"Received Documentation from {component_name}")
        self.help_documents[component_topic] = {
            "name": component_name,
            "doc": component_doc,
            "topic": component_topic,
            "type": component_type,
            "grp": component_grp,
            "schema": component_schema
        }

    @docupub(topics=["com.lambentri.edge.la4.doc.pub"], shapes={"com.lambentri.edge.la4.doc.pub": {
        "$key": {"name": "str", "doc": "str", "topic": "str", "type": "str", "grp": "str", "schema": "str"}
    }})
    @inlineCallbacks
    def document_publisher(self):
        """Publishes documents at set intervals"""
        if self.help_documents:  # prevent blanking pages on refresh
            yield self.publish("com.lambentri.edge.la4.doc.pub", docs=self.help_documents)

    @docupub(topics=["com.lambentri.edge.la4.doc.com"],
             shapes={"com.lambentri.edge.la4.doc.com":
                         {"components": {"$key": {"desc": "str", "header": "str", "grp": "strL"}},
                          "terms": {"$key": {"desc": "str", "type":"str"}
                                    }
                          }
                     }
             )
    @inlineCallbacks
    def component_publisher(self):
        """Publishes Information about system components, used for the documentation"""
        data_v = {
            "Machines": {
                "desc": """Machines are the backbone of LA4. A machine is a state machine that at a configurable tick will
                publish its internal state to a predictable topic. 
                In previous iterations machines were hardcoded into the configuration and were static. LA4 Allows machines 
                to be provisioned and controlled via adhoc rpc calls""",
                "header": "Machines",
                "grp": "machine"
            },
            "Links": {
                "desc": """Links are used to dynamically route data from machines as well as other to other arbitrary links. There are special links (planned) that combine multiple topics into a single buffer, """,
                "header": "Links",
                "grp": "links"
            },
            "Sinks": {
                "desc": """Sinks are virtual representations of real lighting devices on the network. 
                            They are an abstraction that hides a lot of complexity in how the device lifecycles are managed,
                            various parameters that can be hidden from the machine layer including multi-led color space expansion
                         """,
                "header": "Sinks",
                "grp": "sinks"
            },
            "Helpers": {
                "desc": """Various utility functions for name generation and documentation collection """,
                "header": "Helpers",
                "grp": "helpers"
            }
        }
        data_h = {
            "Publishers": {
                "desc": "Topics that publish data at arbitrary-md intervals",
                "type": "pub",
            },
            "Subscribers": {
                "desc": "Topics that recieve data",
                "type": "sink",
            },
            "Calls": {
                "desc": "Topics that take args and kwargs and execute a function",
                "type": "call",
            }
        }
        yield self.publish("com.lambentri.edge.la4.doc.com", components=data_v, terms=data_h)


if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8083/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(HelperSession)
