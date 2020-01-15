from os import path
from wsgiref.simple_server import make_server


def test_app(_, start_response):
    # This path is set up as a volume in the test's docker-compose.yml,
    # so we make sure that we really work with Docker Compose.
    if path.exists("/test_volume"):
        status = "204 No Content"
    else:
        status = "500 Internal Server Error"
    start_response(status, headers=[])
    # and empty HTTP body matching the 204
    return [b""]


HTTPD = make_server("", 80, test_app)
print("Test server running...")
HTTPD.serve_forever()
