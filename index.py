from twisted.internet.defer import inlineCallbacks, returnValue
from klein import Klein
import os
import vbuild

class HostedKlein(Klein):
    def __init__(self, **kwargs):
        super().__init__()

    def resource(self, **kwargs):
        print("KLEINKWARGS ==================>")
        print(kwargs)
        return super().resource()

app = Klein()

@app.route('/', methods=['GET'])
def index(request):
    with open(os.path.join(os.getcwd(),"..","web","index.html")) as file:
        buf = file.read()# should contains a tag "<!-- HERE -->" that would be substituted
    # buf = buf.replace("<!-- HERE -->", str(vbuild.render("vues/*.vue")))
    # writeYourTemplate("index.html", buf)
    # return "heyheyhey"
    return buf


def resource(args):
    return app.resource()