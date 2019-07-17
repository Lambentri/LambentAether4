FROM crossbario/crossbar:pypy3

COPY . /node

USER root
RUN chown -R crossbar:crossbar /node/*
RUN ls -la /node/
# USER crossbar

ENTRYPOINT ["crossbar", "start", "--cbdir", "/node/.crossbar"]
