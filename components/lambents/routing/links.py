# A combination of source topics => [filters, manifolds and groups] and => recving topic for a device/zone,
# can be empty for direct rooting from source -> device
import datetime
import os
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn import wamp
from autobahn.wamp.types import SubscribeOptions
from copy import deepcopy
from twisted.internet import task
from twisted.internet.defer import inlineCallbacks

LINK_PREFIX = "com.lambentri.edge.la4.machine.link"
LINK_PREFIX_ = f"{LINK_PREFIX}."
SINK_PREFIX = "com.lambentri.edge.la4.machine.sink"
SINK_PREFIX_ = f"{SINK_PREFIX}."

class LinkManager(ApplicationSession):
    sources = {}
    sources_lseen = {}
    sinks = {}
    sinks_lseen = {}
    links = {}
    link_subs = {}
    link_src_map = {}

    HERALD_TICKS = .5

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    def onJoin(self, details):
        print("joined")
        self.register(self)
        self.subscribe(self)

        self.ticker_herald = task.LoopingCall(self.link_herald)
        self.ticker_herald.start(self.HERALD_TICKS)

    @wamp.subscribe(LINK_PREFIX, options=SubscribeOptions(match="prefix", details_arg="details"))
    def link_noticer(self, res, details, id):
        # print(res[0:100])
        # print(details)
        """
        notices a link being created and stores the last-seen etc, for UI purposes
        :return: 
        """
        split_topic = details.topic.split(LINK_PREFIX_)[1]
        src_class, src_topic = split_topic.split('.',1)
        self.sources[split_topic] = [src_class, src_topic]
        self.sources_lseen[split_topic] = datetime.datetime.now()
        # todo flush to redis
        # print(src_class)
        # print(src_topic)
        # print(split_topic)

    @wamp.subscribe(SINK_PREFIX, options=SubscribeOptions(match="prefix", details_arg="details"))
    def sink_noticer(self, res, details):
        split_topic = details.topic.split(SINK_PREFIX_)[1]
        # print("NOTICED!!")
        # print(split_topic)
        # print(res)
        for sink_sub in res:

            res_id = sink_sub.get('id')
            res_iname = sink_sub.get('iname')
            res_name = sink_sub.get('name')

            if split_topic in self.sinks:
                self.sinks[split_topic][res_id] = sink_sub
            else:
                self.sinks[split_topic] = {res_id: sink_sub}

    @property
    def computed_sinks(self):
        sdict = deepcopy(self.sinks)
        returnvals = []
        for groupkey,objects in sdict.items():
            for k,v in objects.items():
                vname = v['name']
                returnvals.append({
                    "listname" : f"{groupkey}.{vname}",
                    "grp": groupkey,
                    **v
                })

        return returnvals

    def _how_long_to_repr(self, value):
        s = abs(value.seconds)
        hours, r_h = divmod(s, 3600)
        minutes, seconds = divmod(r_h, 60)
        return f"{hours}H.{minutes}.M.{seconds}."

    @inlineCallbacks
    def link_herald(self):
        built_srcs = []
        for src, topic in self.sources.values():
            # if src not in built:
            #     built[src] = []
            last_seen = self.sources_lseen[f"{src}.{topic}"]
            how_long = datetime.datetime.now() - last_seen
            how_long_s = self._how_long_to_repr(how_long)
            built_srcs.append({"listname":topic, "ttl":how_long_s, "id": f"{LINK_PREFIX}.{src}.{topic}", "cls": src})

        built_links = self.links


        yield self.publish("com.lambentri.edge.la4.links", links=built_links, sinks=self.computed_sinks, srcs=built_srcs)

    @inlineCallbacks
    def pass_link(self, *args, **kwargs):
        # print(args)
        # print(kwargs)
        # print(kwargs.get('details'))
        print(self.link_src_map[kwargs.get('id')])
        if self.links[kwargs.get('id')]['active']:
            yield self.publish(self.link_src_map[kwargs.get('id')], args[0], id=self.links[kwargs.get('id')]['name'])

    def _do_toggle(self, target, exclude=None):
        """ Disables all links pointing to a given target

        pass an exclusion ID to keep from excluding sources during the toggle call
        """
        to_disable = [k for k,v in self.link_src_map.items() if v == target]
        for td in to_disable:
            if td == exclude:
                self.links[td]['active'] = True
            else:
                self.links[td]['active'] = False

        print(self.links)

    def _do_disable(self, link_id):
        self.links[link_id]['active'] = False

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.save")
    def save_link(self, link_name, link_spec):
        """ Create, save, and modify. All in one!

        We're going to be super lazy and assume the name engine won't collide too hard
        """
        print(link_name)
        print(link_spec)

        list_name = link_spec['source']['listname']
        target_id = link_spec['target']['id']
        source_id = link_spec['source']['id']
        self._do_toggle(link_spec['target']['id'], exclude=list_name)
        self.links[list_name] = {"name":link_name, "active": True, "list_name":list_name, "full_spec":link_spec}
        self.link_subs[link_name] = yield self.subscribe(self.pass_link, topic=source_id, options=SubscribeOptions(details_arg="details", correlation_id=link_name, correlation_is_anchor=True))
        self.link_src_map[list_name] = target_id

    @wamp.register("com.lambentri.edge.la4.links.toggle")
    def toggle_link(self, link_name):
        print("TOGGLE")
        """Toggles a link on, will disable all others that are pointing to a given device / src"""
        target = self.link_src_map[link_name]
        self._do_toggle(target, exclude=link_name)

    @wamp.register("com.lambentri.edge.la4.links.disable")
    def disable_link(self, link_name):
        print("DISABLE")
        """Disables a link (more or less the same as toggling, but to turn off the lights?"""
        self._do_disable(link_name)

    @wamp.register("com.lambentri.edge.la4.links.destroy")
    def destroy_link(self, link_name):
        list_name = self.links[link_name]['name']
        print(list_name)
        print(link_name)
        self.link_subs[list_name].unsubscribe()
        del self.link_subs[list_name]
        del self.link_src_map[link_name]
        del self.links[link_name]

if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8080/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(LinkManager)
