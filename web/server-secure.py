#!/usr/bin/env python3
#-- coding: utf-8 --

import base64
import os
import ssl
import sys
import logging
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer

HOSTNAME = "localhost"
PORT = 8081
CERT_FILE = os.path.expanduser("~/services/web/certificates/cert.pem")
KEY_FILE = os.path.expanduser("~/services/web/certificates/key.pem")
SSL_CMD = "openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout {0} -out {1}".format(KEY_FILE, CERT_FILE)

logging.basicConfig(level=logging.INFO,
  format='%(asctime)s %(levelname)s %(message)s',
  datefmt='%d/%m/%Y %H:%M:%S')

class SimpleHTTPAuthHandler(SimpleHTTPRequestHandler):
    KEY = ''

    def do_HEAD(self):
      ''' head method '''
      self.send_response(200)
      # self.send_header('Content-type', 'text/html')
      self.send_header('Content-type', 'application/json')
      self.end_headers()

    def do_authhead(self):
      ''' do authentication '''
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
      # self.send_header('Content-type', 'text/html')
      self.send_header('Content-type', 'application/json')
      self.end_headers()

    def _set_response(self):
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()

    def do_GET(self):
      ''' Present frontpage with user authentication. '''
      if self.headers.get('Authorization') is None:
          self.do_authhead()
          response = {
              'success': False,
              'error': 'No auth header received'
          }
          self.wfile.write(bytes(json.dumps(response), 'utf-8'))
      elif self.headers.get('Authorization') == 'Basic '+ self.KEY:
          if self.path == '/':
            self.path = "index.html"
            return SimpleHTTPRequestHandler.do_GET(self)

          elif self.path == "/tank-service":
            os.system("sudo systemctl restart tankmanager.service")
            logging.info("Tank manager service is reload")
            self._set_response()
          
          elif self.path == "/reboot":
            os.system("sudo reboot")
            logging.info("System reboot")
            self._set_response()

      else:
          self.do_authhead()
          
          response = {
            'success': False,
            'error': 'Invalid credentials'
          }

          self.wfile.write(bytes(json.dumps(response), 'utf-8'))

def server_https(handler):
  httpd = TCPServer(("", PORT), handler)
  httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=KEY_FILE, certfile=CERT_FILE, server_side=True)
  httpd.serve_forever()

def main():
  if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
    logging.error("Missing {} or {}".format(CERT_FILE, KEY_FILE))
    logging.error("Run `{}`".format(SSL_CMD))
    sys.exit(1)

  # TODO: get login from database 
  SimpleHTTPAuthHandler.KEY = base64.b64encode(bytes('%s:%s' % ('', ''), 'utf-8')).decode('ascii') # Add user password for test
  server_https(SimpleHTTPAuthHandler)

if __name__ == "__main__":
  main()