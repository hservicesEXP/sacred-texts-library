from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
ROOT=Path(__file__).parent/"docs"
ap=argparse.ArgumentParser();ap.add_argument("--port",type=int,default=8080);a=ap.parse_args()
server=ThreadingHTTPServer(("127.0.0.1",a.port),lambda *x: SimpleHTTPRequestHandler(*x,directory=str(ROOT)))
print(f"http://127.0.0.1:{a.port}/");server.serve_forever()
