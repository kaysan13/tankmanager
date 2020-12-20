#!/usr/bin/env python3
#-- coding: utf-8 --

import logging, os, signal

try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    from SocketServer import TCPServer
except ImportError:
    from socketserver import TCPServer

logging.basicConfig(level=logging.INFO,
  filename='/var/log/tankmanager/info.log',
  format='%(asctime)s %(levelname)s %(message)s',
  datefmt='%d/%m/%Y %H:%M:%S')

hostName = "localhost"
serverPort = 8080

class ProgramKilled(Exception):
  pass

def signal_handler(signum, frame):
  raise ProgramKilled

class MyHttpRequestHandler(SimpleHTTPRequestHandler):
    KEY = ''

    def _set_response(self):
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()

    def do_authhead(self):
      ''' do authentication '''
      print("send header")
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
      self.send_header('Content-type', 'text/html')
      self.end_headers()

    def do_GET(self):
        ''' Present frontpage with user authentication. '''
        if self.headers.getheader('Authorization') is None:
            self.do_authhead()
            self.wfile.write('no auth header received')
        elif self.headers.getheader('Authorization') == 'Basic '+ self.KEY:
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.do_authhead()
            self.wfile.write(self.headers.getheader('Authorization'))
            self.wfile.write('not authenticated')

        if self.path == '/':
          self.path = "index.html"
          return SimpleHTTPRequestHandler.do_GET(self)

        if self.path == "/tank-service":
          os.system("sudo systemctl restart tankmanager.service")
          logging.info("Tank manager service is reload")
          self._set_response()
        
        if self.path == "/reboot":
          os.system("sudo reboot")
          logging.info("System reboot")
          self._set_response()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    webServer = TCPServer(("", serverPort), MyHttpRequestHandler)
    logging.info("Server started http://%s:%s" % (hostName, serverPort))

    try:
      webServer.serve_forever()
    except ProgramKilled:
      logging.error("Program killed: running cleanup code")
      pass

    webServer.server_close()
    logging.info("Server stopped.")