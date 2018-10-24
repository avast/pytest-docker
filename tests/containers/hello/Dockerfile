# -*- coding: utf-8 -*-

FROM python:3.6-alpine
# Python won't pick up SIGTERM (the default) and will have to be killed with SIGKILL
# from Docker after a timeout. But it will pick up SIGINT and stop immediately
# as if touched by Ctrl+c.
STOPSIGNAL SIGINT

WORKDIR /app
ADD server.py /app

CMD [ "python", "/app/server.py" ]
