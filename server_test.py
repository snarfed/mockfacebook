#!/usr/bin/python
"""Unit tests for server.py.

Requires mox.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import atexit
import os
import re
import threading
import unittest
import urllib
import urllib2
import warnings
import wsgiref

import mox

import server
import testutil


class ServerTest(mox.MoxTestBase):
  """Integration test. Starts the server and makes HTTP requests to localhost.

  Class attributes:
    port: integer port to run the server on
    db_filename: string SQLite db filename
    thread: Thread running the server
  """

  port = 60001

  @classmethod
  def start_server(cls):
    """Sets up and starts the server if it's not already running.
    """
    warnings.filterwarnings('ignore', 'tempnam is a potential security risk')
    cls.db_filename = os.tempnam('/tmp', 'mockfacebook_test.')
    testutil.make_test_db(cls.db_filename).close()
    ServerTest.port += 1

    started = threading.Event()
    cls.thread = threading.Thread(
      target=server.main,
      args=(['--file', cls.db_filename,
             '--port', str(ServerTest.port),
             '--me', '%d' % testutil.ME,
             ],),
      kwargs={'started': started})
    cls.thread.start()
    started.wait()

  @classmethod
  def stop_server(cls):
    """Stops the server if it's running.
    """
    print 'trying'
    server.server.shutdown()
    cls.thread.join()

    try:
      os.remove(cls.db_filename)
    except:
      pass

  def request(self, path, args, expected):
    """Makes an HTTP request.

    Args:
      path: string
      args: dict mapping string to string
      expected: string response
    """
    url = 'http://localhost:%d%s?%s' % (self.port, path, urllib.urlencode(args))
    self.assertEquals(expected, urllib2.urlopen(url).read())

  def test_fql(self):
    args = {'query': 'SELECT username, name FROM profile WHERE id = me()',
            'format': 'json'}
    self.request('/method/fql.query', args,
                 '[{"username": "snarfed.org", "name": "Ryan Barrett"}]')

  def test_graph(self):
    self.request(
      '/10150150038100285', {},
      '{"type": "domain", "id": "10150150038100285", "name": "snarfed.org"}')

  def test_oauth(self):
    args = {'client_id': 'x',
            'client_secret': 'y',
            'redirect_uri': 'http://localhost:%d/placeholder' % self.port,
            'response_type': 'token',
            }

    resp = self.request('/dialog/oauth', args, '')
    # fail('Should have raised HTTPError')
    # except urllib2.HTTPError, e:
    #   redirect = e.geturl()
    self.assertEquals(302, resp.status_int)
    redirect = resp.headers['Location']
    assert re.search('#access_token=.+&expires_in=999999$', redirect), redirect

  def test_404(self):
    try:
      resp = self.request('/not_found', {}, '')
      fail('Should have raised HTTPError')
    except urllib2.HTTPError, e:
      self.assertEquals(404, e.code)


if __name__ == '__main__':
  ServerTest.start_server()
  atexit.register(lambda: ServerTest.stop_server())
  unittest.main()
