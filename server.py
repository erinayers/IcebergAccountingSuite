"""Local HTTP API for the interface.

The window loads ``http://127.0.0.1:<port>/`` from this server, which serves
the static files in ``web/`` and dispatches ``/api/...`` requests to
``IcebergApi`` according to the route table in ``web/routes.js``.  The same
table drives the JavaScript client, so the two sides cannot drift.

Safety:

* bound to the loopback interface on a random free port;
* every API request must carry the per-session token (``X-Iceberg-Token``)
  that is handed to the page through the start URL;
* API calls are serialised with a lock (the in-memory SQLite database is
  used from the server's worker threads);
* handler exceptions become ``{"ok": false, "message": ...}`` with HTTP 500.
"""

import inspect
import json
import mimetypes
import os
import re
import secrets
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROUTES_FILE = os.path.join("web", "routes.js")


class RouteError(Exception):
    pass


def load_routes(root):
    """Parse web/routes.js into {name: {method, path, handler, params}}."""
    with open(os.path.join(root, ROUTES_FILE), encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r"var API_ROUTES = (\{.*?\n\});", text, re.S)
    if not match:
        raise RouteError("web/routes.js does not contain API_ROUTES")
    body = match.group(1)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)          # block comments
    body = re.sub(r",(\s*[}\]])", r"\1", body)                  # trailing commas
    raw = json.loads(body)
    routes = {}
    for name, (method, path, handler, params) in raw.items():
        routes[name] = {"method": method.upper(), "path": path, "handler": handler, "params": list(params),
                        "pattern": re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path) + "$")}
    return routes


def check_routes_against(api, routes):
    """Every route must name an existing method whose parameters match."""
    problems = []
    for name, route in routes.items():
        method = getattr(api, route["handler"], None)
        if not callable(method):
            problems.append(f"{name}: no API method '{route['handler']}'")
            continue
        parameters = inspect.signature(method).parameters
        required = [p.name for p in parameters.values() if p.default is inspect.Parameter.empty]
        unknown = [p for p in route["params"] if p not in parameters]
        missing = [p for p in required if p not in route["params"]]
        if unknown or missing:
            problems.append(f"{name}: route params {route['params']} do not fit {route['handler']}({', '.join(parameters)})")
        for placeholder in re.findall(r"\{(\w+)\}", route["path"]):
            if placeholder not in route["params"]:
                problems.append(f"{name}: path placeholder {{{placeholder}}} is not a parameter")
    return problems


class ApiServer:
    def __init__(self, api, root, host="127.0.0.1", port=0):
        self.api = api
        self.root = os.path.abspath(root)
        self.web_root = os.path.join(self.root, "web")
        self.routes = load_routes(self.root)
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.RLock()
        self._server = ThreadingHTTPServer((host, port), self._handler_class())
        self._server.daemon_threads = True
        self._thread = None

    # ---------------------------------------------------------- lifecycle

    @property
    def port(self):
        return self._server.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/?token={self.token}"

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, name="iceberg-api", daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()

    # ---------------------------------------------------------- dispatch

    def dispatch(self, method, path, query, body, token):
        """Return (status_code, payload) for an API request."""
        if token != self.token:
            return 401, {"ok": False, "message": "Missing or invalid session token.", "errors": []}
        for route in self.routes.values():
            match = route["pattern"].match(path)
            if not match:
                continue
            if route["method"] != method:
                continue
            args = {}
            for name in route["params"]:
                if name in match.groupdict():
                    args[name] = match.group(name)
                elif name in body:
                    args[name] = body[name]
                elif name in query:
                    args[name] = query[name]
            handler = getattr(self.api, route["handler"], None)
            if handler is None:
                return 501, {"ok": False, "message": f"{route['handler']} is not available in this host.", "errors": []}
            try:
                with self.lock:
                    result = handler(**args)
            except TypeError as error:
                return 400, {"ok": False, "message": f"Bad request: {error}", "errors": []}
            except Exception as error:  # never leak a traceback to the page
                return 500, {"ok": False, "message": f"Something went wrong: {error}", "errors": []}
            return 200, result if result is not None else {"ok": True, "message": "", "errors": []}
        if any(route["pattern"].match(path) for route in self.routes.values()):
            return 405, {"ok": False, "message": "Method not allowed.", "errors": []}
        return 404, {"ok": False, "message": f"Unknown API route {path}.", "errors": []}

    def static_file(self, path):
        """Return (status, bytes, content_type) for a file under web/."""
        if path in ("", "/"):
            path = "/index.html"
        target = os.path.normpath(os.path.join(self.web_root, path.lstrip("/")))
        if not target.startswith(self.web_root) or not os.path.isfile(target):
            return 404, b"Not found", "text/plain"
        with open(target, "rb") as handle:
            data = handle.read()
        content_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
            content_type += "; charset=utf-8"
        return 200, data, content_type

    def _handler_class(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt, *args):  # keep the terminal quiet
                pass

            def _send_json(self, status, payload):
                data = json.dumps(payload, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def _api(self, method):
                parsed = urllib.parse.urlsplit(self.path)
                query = {k: v[-1] for k, v in urllib.parse.parse_qs(parsed.query).items()}
                length = int(self.headers.get("Content-Length") or 0)
                body = {}
                if length:
                    try:
                        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                    except ValueError:
                        self._send_json(400, {"ok": False, "message": "The request body is not valid JSON.", "errors": []})
                        return
                    if not isinstance(body, dict):
                        body = {"value": body}
                token = self.headers.get("X-Iceberg-Token") or query.pop("token", None)
                status, payload = server.dispatch(method, parsed.path, query, body, token)
                self._send_json(status, payload)

            def do_GET(self):
                parsed = urllib.parse.urlsplit(self.path)
                if parsed.path.startswith("/api/"):
                    return self._api("GET")
                status, data, content_type = server.static_file(parsed.path)
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                self._api("POST")

            def do_PUT(self):
                self._api("PUT")

            def do_DELETE(self):
                self._api("DELETE")

        return Handler
