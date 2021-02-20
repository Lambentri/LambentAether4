# A combination of source topics => [filters, manifolds and groups] and => recving topic for a device/zone,
# can be empty for direct rooting from source -> device
import datetime
import os
from dataclasses import dataclass

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn import wamp
from autobahn.wamp.types import SubscribeOptions
from copy import deepcopy
from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks

from components.lambents.lib.decor import docupub
from components.lambents.lib.mixins import DocMixin
from components.library import chunks

LINK_PREFIX = "com.lambentri.edge.la4.machine.link"
LINK_PREFIX_ = f"{LINK_PREFIX}."
SINK_PREFIX = "com.lambentri.edge.la4.machine.sink"
SINK_PREFIX_ = f"{SINK_PREFIX}."


@dataclass
class Link:
    name: str
    active: bool
    list_name: str
    full_spec: dict

    def serialize(self):
        return {"name": self.name, "active": self.active, "list_name": self.list_name, "full_spec": self.full_spec}


class LinkManager(DocMixin, ApplicationSession):
    sources = {}
    sources_lseen = {}
    sinks = {}
    sinks_lseen = {}
    links: dict = {}
    link_subs = {}
    link_tgt_map = {}
    link_name_to_source = {}

    source_history = {}
    iter_buffer_intermediate = {}
    iter_buffer_loop_storage = {}
    iter_buffer_timeout = {}

    HERALD_TICKS = .5

    do_fade_between = True

    regs = {}
    subs = {}
    grp = "links"

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    @inlineCallbacks
    def onJoin(self, details):
        print("joined")
        self.regs = yield self.register(self)
        self.subs = yield self.subscribe(self)
        self.document()

        self.ticker_herald = task.LoopingCall(self.link_herald)
        self.ticker_herald.start(self.HERALD_TICKS)

    @wamp.subscribe(LINK_PREFIX, options=SubscribeOptions(match="prefix", details_arg="details"))
    def link_noticer(self, res, details, id):
        # print(res[0:100])
        # print(details)
        """
        notices a link being created and stores the last-seen etc, for UI purposes
        """
        split_topic = details.topic.split(LINK_PREFIX_)[1]
        src_class, src_topic = split_topic.split('.', 1)
        self.sources[split_topic] = [src_class, src_topic]
        self.sources_lseen[split_topic] = datetime.datetime.now()
        # todo flush to redis
        # print(src_class)
        # print(src_topic)
        # print(split_topic)

    @wamp.subscribe(SINK_PREFIX, options=SubscribeOptions(match="prefix", details_arg="details"))
    def sink_noticer(self, res, details):
        """
        Notices a sink announcing itself
        """
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
        for groupkey, objects in sdict.items():
            for k, v in objects.items():
                vname = v['name']
                returnvals.append({
                    "list_name": f"{groupkey}.{vname}",
                    "grp": groupkey,
                    **v
                })

        return returnvals

    def _how_long_to_repr(self, value):
        s = abs(value.seconds)
        hours, r_h = divmod(s, 3600)
        minutes, seconds = divmod(r_h, 60)
        return f"{hours}H.{minutes}.M.{seconds}."

    @docupub(topics=["com.lambentri.edge.la4.links"], shapes={"com.lambentri.edge.la4.links": {"links":{}, "sinks":[]}})
    @inlineCallbacks
    def link_herald(self):
        """Announces links/sinks at a tick of .5s"""
        built_srcs = []
        for src, topic in self.sources.values():
            # if src not in built:
            #     built[src] = []
            last_seen = self.sources_lseen[f"{src}.{topic}"]
            how_long = datetime.datetime.now() - last_seen
            how_long_s = self._how_long_to_repr(how_long)
            built_srcs.append({"list_name": topic, "ttl": how_long_s, "id": f"{LINK_PREFIX}.{src}.{topic}", "cls": src})

        built_links = {k: v.serialize() for k, v in self.links.items()}

        yield self.publish("com.lambentri.edge.la4.links", links=built_links, sinks=self.computed_sinks,
                           srcs=built_srcs)

    def _find_link_by_src_id(self, target):
        to_pass_to = []
        for k, v in self.link_name_to_source.items():
            if v == target:
                to_pass_to.append(k)
        return to_pass_to

    # TODO figure out how2 docupub this
    @inlineCallbacks
    def pass_link(self, *args, **kwargs):
        src_id = kwargs.get('id')
        links_to_pass = self._find_link_by_src_id(src_id)
        self.source_history[src_id] = args[0]
        for link in links_to_pass:
            if self.links[link].active:
                # print(link)
                # print(self.link_tgt_map[link])
                # self.source_history[src_id] = args[0]
                yield self.publish(self.link_tgt_map[link], args[0], id=self.links[link].name)
        # print(self.link_src_map[kwargs.get('id')])
        # if self.links[kwargs.get('id')]['active']:
        #     yield self.publish(self.link_src_map[kwargs.get('id')], args[0], id=self.links[kwargs.get('id')]['name'])

    def _step(self, src, tgt, size=3):
        if src == tgt:
            return tgt

        elif src < tgt:
            if src + size > tgt:
                return tgt
            else:
                return src + size
        elif src > tgt:
            if src - size < tgt:
                return tgt
            else:
                return src - size

    def _do_naive_stepping_between_buffers(self, source, target):
        # print("step")
        # print(source[0:24])
        # print(target[0:24])
        src_c = chunks(source, 3)
        tar_c = chunks(target, 3)

        steppedbuffer = []
        for rgbvals_s, rgbvals_t in zip(src_c, tar_c):
            r_s, g_s, b_s = rgbvals_s
            r_t, g_t, b_t = rgbvals_t
            r_i, g_i, b_i = self._step(r_s, r_t), self._step(g_s, g_t), self._step(b_s, b_t)
            steppedbuffer.extend([r_i, g_i, b_i])

        return steppedbuffer

    @inlineCallbacks
    def _iterate_buffer(self, target, buffer, enable):
        target_buffer = self.source_history[target]
        if target not in self.iter_buffer_intermediate:
            self.iter_buffer_intermediate[target] = buffer
        else:
            buffer = self.iter_buffer_intermediate[target]

        working_buffer = self._do_naive_stepping_between_buffers(buffer, target_buffer)
        # print( " W ^ T")
        # print(working_buffer[0:24])
        # print(target)
        self.iter_buffer_intermediate[target] = working_buffer
        yield self.publish(self.link_tgt_map[enable], working_buffer, id='inter')
        now = datetime.datetime.now()
        if working_buffer == target_buffer or self.iter_buffer_timeout[target] < now:
            print("EQUALIZED OR TIMED OUT")
            del self.iter_buffer_intermediate[target]
            self.links[enable].active = True
            try:
                self.iter_buffer_loop_storage[target].stop()
            except AssertionError:
                print("Tried to stop a LoopingCall that was not running.")
        # when loop is complete
        # delete iter_buffer
        # enable excluded
        # loop.stop()

    def _do_toggle(self, target, exclude=None):
        """ Disables all links pointing to a given target

        pass an exclusion ID to keep from excluding sources during the toggle call
        """
        # print("tgt")
        # print(target)
        #
        # print("excl")
        # print(exclude)

        to_disable = [k for k, v in self.link_tgt_map.items() if v == target]
        # print("todi")
        # print(to_disable)

        if self.links[exclude].list_name not in self.source_history:
            task.deferLater(reactor, .1, self._do_toggle, target, exclude)
            return

        if not self.do_fade_between:
            for td in to_disable:
                if td == exclude:
                    self.links[td].active = True
                else:
                    self.links[td].active = False
            return

        if all([not self.links[i].active for i in to_disable]):
            self.links[exclude].active = True
            return

        # TODO: Redo the above code to generate a wedge pattern that will enable a smooth fade over the course of a few seconds between values
        # PRE: save the current state of latest current source values being passed through in pass_link
        if not self.links or not exclude:
            return
        try:
            curr = next(i for i in to_disable if self.links[i].active)
            # print("Currrr")
            # print(curr)
            curr_l = self.links[curr]
            # print(curr_l)
        except StopIteration:
            # print("raised stoppppp")
            return

        # disable the active ones
        for td in to_disable:
            self.links[td].active = False
        self.links[exclude].active = False

        # collect current source IDs
        curr_source_id = curr_l.list_name
        # curr_source_id = curr_l.full_spec['source']['id']
        target_source_id = self.links[exclude].list_name
        # print("hurr")
        # print(curr_source_id, target_source_id)

        # build a buffer
        working_buffer = self.source_history[curr_source_id]
        # target_buffer = self.source_history[target_source_id]

        # forge a loop
        self.iter_buffer_loop_storage[target_source_id] = task.LoopingCall(self._iterate_buffer,
                                                                           target_source_id,
                                                                           working_buffer,
                                                                           exclude,
                                                                           )
        # loop.kw.update({"loop": loop, "enable": exclude})  # oh yes.
        self.iter_buffer_timeout[target_source_id] = datetime.datetime.now() + datetime.timedelta(seconds=5)
        self.iter_buffer_loop_storage[target_source_id].start(0)

        # while working_buffer != target_source_id:
        #     # rewrite the target
        #     target_buffer = yield self._get_source_history(target_source_id)
        #     print(target_buffer)
        #     # step toward it
        #     working_buffer = self._do_naive_stepping_between_buffers(working_buffer, target_buffer)
        #
        #     yield self.publish(target, working_buffer, id='inter')

        # self.links[exclude].active = True

        # set all active to False
        # collect the current state of a given link
        # collect the current state of the one to be active
        # build a transfer buffer to smoothly switch patterns
        # pass pattern to link target
        # set active to True

    def _do_disable(self, link_id):
        self.links[link_id].active = False

        # TODO: Add a little hook in here that sends out a fadeout of current program to standby pattern
        # collect the current state of the given link
        # target = self.link_tgt_map[link_id]
        # last_state = self.source_history[target]
        # last_state = self.sou
        # mark link inactive
        # build a fade buffer from the existing buffer
        # pass pattern to link target
        # at end mark the current state buffer as our standby values so the toggle above can extrapolate back

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.save")
    def save_link(self, link_name: str, link_spec):
        """ Create, save, and modify. All in one!

        We're going to be super lazy and assume the name engine won't collide too hard
        """
        # print(link_name)
        # print(link_spec)

        list_name = link_spec['source']['list_name']
        target_id = link_spec['target']['id']
        source_id = link_spec['source']['id']
        self.links[link_name] = Link(name=link_name, active=True, list_name=list_name, full_spec=link_spec)
        self.link_tgt_map[link_name] = target_id
        self.link_name_to_source[link_name] = list_name
        self.link_subs[link_name] = yield self.subscribe(self.pass_link, topic=source_id,
                                                         options=SubscribeOptions(details_arg="details",
                                                                                  correlation_id=link_name,
                                                                                  correlation_is_anchor=True))

        self._do_toggle(link_spec['target']['id'], exclude=link_name)
        # self.links[link_name] = Link(name=link_name, active=True, list_name=list_name, full_spec=link_spec)
        # self.links[link_name] = {"name": link_name, "active": True, "list_name": list_name, "full_spec": link_spec}

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.save_bulk")
    def save_bulk_links(self, link_name, link_spec):
        for link in link_spec['targets']:
            name = link['name']
            newname = link_name + "·" + name

            newspec = {"source": link_spec['source'], "target": link}
            yield self.save_link(newname, newspec)

    @wamp.register("com.lambentri.edge.la4.links.toggle")
    def toggle_link(self, link_name: str):
        """Toggles a link on, will disable all others that are pointing to a given device / src"""
        target = self.link_tgt_map[link_name]
        self._do_toggle(target, exclude=link_name)

    @wamp.register("com.lambentri.edge.la4.links.disable")
    def disable_link(self, link_name: str):
        """Disables a link (more or less the same as toggling, but to turn off the lights?"""
        self._do_disable(link_name)

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.destroy")
    def destroy_link(self, link_name: str):
        """Destroys a link by removing it from the link struct"""
        list_name = self.links[link_name].name
        yield self.link_subs[link_name].unsubscribe()
        del self.link_subs[link_name]
        del self.link_tgt_map[link_name]
        del self.links[link_name]
        del self.link_name_to_source[link_name]

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.destroy_prefix")
    def destroy_prefix(self, prefix: str):
        """For destroying bulk link created w/ "$name·location" """
        deletable = filter(lambda x: x.startswith(prefix), self.link_subs.keys())
        for item in deletable:
            yield self.destroy_link(item)

    @inlineCallbacks
    @wamp.register("com.lambentri.edge.la4.links.destroy_all")
    def destroy_all(self):
        """ Destroy ALL Links """
        # raises builtins.RuntimeError: dictionary changed size during iteration
        link_name_list = list(self.link_subs.keys())
        for link_name in link_name_list:
            yield self.destroy_link(link_name)



if __name__ == '__main__':
    url = os.environ.get("XBAR_ROUTER", u"ws://127.0.0.1:8083/ws")
    realm = u"realm1"
    runner = ApplicationRunner(url, realm)
    runner.run(LinkManager, auto_reconnect=True)
