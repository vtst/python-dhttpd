#!/usr/bin/python
# (c) Vincent Simonet, 2015.

import argparse
import httplib
import mimetypes
import os
import posixpath
import shutil
import threading
import urllib
import BaseHTTPServer
import SimpleHTTPServer
from SocketServer import ThreadingMixIn


class DelegatingHTTPServer(BaseHTTPServer.HTTPServer):

  def __init__(self, server_address,
               RequestHandlerClass,
               dserver_address,
               localdir):
    BaseHTTPServer.HTTPServer.__init__(self,
                                       server_address, RequestHandlerClass)
    self.dserver_host = dserver_address[0]
    self.dserver_port = dserver_address[1]
    self.localdir = os.path.abspath(localdir)


class ThreadedDelegatingHTTPServer(ThreadingMixIn, DelegatingHTTPServer):
    """Handle requests in a separate thread."""


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

  _FILTERED_HEADERS = set(['connection', 'host'])

  def send_local(self):
    path = self.translate_path(self.path)
    f = None
    if os.path.isdir(path):
      for index in "index.html", "index.htm":
        index = os.path.join(path, index)
        if os.path.exists(index):
          path = index
          break
        else:
          return False
    ctype = self.guess_type(path)
    if ctype.startswith('text/'):
      mode = 'r'
    else:
      mode = 'rb'
    try:
      f = open(path, mode)
    except IOError:
      return False
    self.send_response(200)
    self.send_header("Content-type", ctype)
    self.end_headers()
    self.copyfile(f, self.wfile)
    f.close()
    return True

  def translate_path(self, path):
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = self.server.localdir
    for word in words:
      drive, word = os.path.splitdrive(word)
      head, word = os.path.split(word)
      if word in (os.curdir, os.pardir): continue
      path = os.path.join(path, word)
    return path

  def copyfile(self, source, outputfile):
    shutil.copyfileobj(source, outputfile)

  def guess_type(self, path):
    base, ext = posixpath.splitext(path)
    if self.extensions_map.has_key(ext):
      return self.extensions_map[ext]
    ext = ext.lower()
    if self.extensions_map.has_key(ext):
      return self.extensions_map[ext]
    else:
      return self.extensions_map['']

  extensions_map = mimetypes.types_map.copy()
  extensions_map.update({
    '': 'application/octet-stream', # Default
    '.py': 'text/plain',
    '.c': 'text/plain',
    '.h': 'text/plain',
  })

  def do_LOCAL_or_PROXY(self):
    if not self.send_local():
      self.do_PROXY()

  def do_PROXY(self):
    conn = httplib.HTTPConnection(self.server.dserver_host,
                                  self.server.dserver_port)
    content_len = int(self.headers.get('content-length', 0))
    body = self.rfile.read(content_len)
    headers = dict((key, self.headers.get(key)) for key in self.headers
                   if not key in self._FILTERED_HEADERS)
    conn.request(self.command, self.path, body, headers)
    resp = conn.getresponse()
    self.send_response(resp.status, resp.reason)
    for name, value in resp.getheaders():
      self.send_header(name, value)
    self.end_headers()
    self.wfile.write(resp.read())
    conn.close()

  do_GET     = do_LOCAL_or_PROXY
  do_POST    = do_PROXY
  do_HEAD    = do_LOCAL_or_PROXY
  do_PUT     = do_PROXY
  do_DELETE  = do_PROXY
  do_OPTIONS = do_PROXY


_DESCRIPTION = """
An HTTP server that serves files from a local directory and a delegate HTTP
server.  For every request, the server first look for a local file to search.
If a file is found, it is returned directly.  If no local file is found, the
request is forwarded to the delegate HTTP server.
"""


def _parse_host_port(s):
  parts = s.split(':')
  if len(parts) == 1:
    return parts[0], 80
  else:
    return parts[0], int(parts[1])


def main():
  parser = argparse.ArgumentParser(description=_DESCRIPTION)
  parser.add_argument('--dserver',
                      action='store',
                      type=str,
                      dest='dserver',
                      help='Delegate HTTP server (default: localhost:8080)',
                      metavar='HOST:PORT',
                      default='localhost:8080')
  parser.add_argument('-p', '--port',
                      action='store',
                      type=int,
                      dest='port',
                      help='Port to listen (default: 8081)',
                      metavar='PORT',
                      default='8081')
  parser.add_argument('-l', '--localdir',
                      action='store',
                      type=str,
                      dest='localdir',
                      help='Local directory to serve',
                      metavar='DIR',
                      default='.')
  args = parser.parse_args()

  server_address = ('', args.port)
  dserver_address = _parse_host_port(args.dserver)
  httpd = ThreadedDelegatingHTTPServer(server_address,
                                       RequestHandler,
                                       dserver_address,
                                       args.localdir)
  httpd.daemon_threads = True
  print 'Listening port ' + str(args.port)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    httpd.shutdown()
    print '\nThat\'s all folks!'

if __name__ == '__main__':
  main()



