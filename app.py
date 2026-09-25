"""Customer portal for the local two-repository whitebox fixture."""
import argparse
import json
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


DEMO_USERS = {'alice': 'demo-alice', 'bob': 'demo-bob'}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != '/api/login':
            return self.respond(404, {'error': 'Route not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError('Invalid body size')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('Expected object')
            username, password = data.get('username'), data.get('password')
            if not isinstance(username, str) or not isinstance(password, str):
                raise ValueError('Expected strings')
        except (ValueError, UnicodeError):
            return self.respond(400, {'error': 'Invalid login payload'})
        if username not in DEMO_USERS or password != DEMO_USERS[username]:
            return self.respond(401, {'error': 'Invalid credentials'})
        token = secrets.token_urlsafe(32)
        self.server.sessions[token] = username
        self.respond(200, {'token': token, 'username': username})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            return self.respond(200, Path(__file__).with_name('index.html').read_bytes(), 'text/html; charset=utf-8')
        if path != '/api/orders' and not re.fullmatch(r'/api/orders/[0-9]+', path):
            return self.respond(404, {'error': 'Route not found'})
        auth = self.headers.get('Authorization', '')
        user = self.server.sessions.get(auth[7:]) if auth.startswith('Bearer ') else None
        if not user:
            return self.respond(401, {'error': 'Login required'})
        request = Request(self.server.orders_url + path.removeprefix('/api'), headers={'X-Customer-ID': user})
        try:
            with urlopen(request, timeout=3) as result:
                self.respond(result.status, result.read())
        except HTTPError as exc:
            with exc:
                self.respond(exc.code, exc.read())
        except (URLError, TimeoutError):
            self.respond(502, {'error': 'Orders API unavailable; start orders-api first'})


def make_server(port=8765, orders_port=8766):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.orders_url = f'http://127.0.0.1:{orders_port}'
    server.sessions = {}
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--orders-port', type=int, default=8766)
    args = parser.parse_args()
    server = make_server(args.port, args.orders_port)
    print(f'Customer portal: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
