import inspect
from autobahn.wamp import PublishOptions
from autobahn.wamp.request import Registration
from twisted.internet.defer import inlineCallbacks

DOC_LISTENER_URI = "com.lambentri.edge.la4.doc"

pub_options = PublishOptions(
    acknowledge=True,
    exclude_me=False
)


class DocMixin:
    zsubs = None
    regs = None

    def _get_function_handle_from_uri(self, uri):
        return next(iter([i for i in self.members if i[1]._wampuris[0]._uri == uri]))

    def _get_doc_from_name_handle(self, handle):
        return getattr(self, handle).__doc__

    def _get_args_and_kwargs_from_name_handle(self, handle):
        """TODO INSPECT RETURN on args"""
        func = getattr(self, handle)
        args = inspect.signature(func)
        # print(args)
        if args and args.parameters:
            if isinstance(list(args.parameters.values())[0], dict):
                x =  {k:v.get("annotation", "str") for k,v in args.parameters.items()}
                print(x)
                return x
            # print("notdict")
            y = {k:str(v.annotation).split("'")[1] for k,v in args.parameters.items() if v.annotation != inspect._empty }
            # print(y)
            return y


    @inlineCallbacks
    def document(self):
        print("superjoin")
        print(self.regs, self.zsubs)
        self.members = [i for i in inspect.getmembers(self, predicate=inspect.ismethod) if hasattr(i[1], "_wampuris")]
        try:
            if self.regs:
                print("REGS", self.regs)
                for reg in self.regs:
                    yield self.publish(
                        DOC_LISTENER_URI,
                        component_name=reg.procedure.rsplit('.', 1)[1],
                        component_doc=self._get_doc_from_name_handle(self._get_function_handle_from_uri(reg.procedure)[0]),
                        component_topic=reg.procedure,
                        component_grp=self.grp,
                        component_type="call",
                        component_schema={
                            "kwargs": self._get_args_and_kwargs_from_name_handle(self._get_function_handle_from_uri(reg.procedure)[0]),
                            "return": {"name": "TODO GET THIS ACTUAL DATA"}
                        },
                        options=pub_options,
                    )

            if self.zsubs:
                print("SUBS", self.zsubs)
                for sub in self.zsubs:
                    yield self.publish(
                        DOC_LISTENER_URI,
                        component_name=sub.topic.rsplit('.', 1)[1],
                        component_doc=self._get_doc_from_name_handle(self._get_function_handle_from_uri(sub.topic)[0]),
                        component_topic=sub.topic,
                        component_grp=self.grp,
                        component_type="sink",
                        component_schema={
                            "kwargs": self._get_args_and_kwargs_from_name_handle(self._get_function_handle_from_uri(sub.topic)[0]),
                            "return": {"name": "TODO GET THIS ACTUAL DATA"}
                        },
                        options=pub_options
                    )

            self.pubmembers = [i for i in inspect.getmembers(self, predicate=inspect.ismethod) if
                               hasattr(i[1], "_publisher")]
            # print("PUBMEMBERS")
            for member in self.pubmembers:
                for topic in member[1]._topics:
                    yield self.publish(
                        DOC_LISTENER_URI,
                        component_name=member[1].__name__,
                        component_doc=member[1]._doc,
                        component_topic=topic,
                        component_grp=self.grp,
                        component_type="pub",
                        component_schema={
                            "kwargs": None,
                            "return": member[1]._shapes.get(topic, "NO SHAPES PASSED IN")
                        },
                        options=pub_options,
                    )
        except Exception as e:
            print(e)

