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
import urlparse
import warnings
import wsgiref

import mox

import fql_test
import graph_test
import server
import testutil


class ServerTest(mox.MoxTestBase):
  """Integration test. Starts the server and makes HTTP requests to localhost.

  Class attributes:
    port: integer port to run the server on
    db_filename: string SQLite db filename
    thread: Thread running the server
  """

  port = 60000

  @classmethod
  def start_server(cls):
    """Sets up and starts the server if it's not already running.
    """
    warnings.filterwarnings('ignore', 'tempnam is a potential security risk')
    cls.db_filename = os.tempnam('/tmp', 'mockfacebook_test.')
    ServerTest.port += 1

    conn = testutil.make_test_db(cls.db_filename)
    fql_test.insert_test_data(conn)
    graph_test.insert_test_data(conn)
    conn.close()

    started = threading.Event()
    cls.thread = threading.Thread(
      target=server.main,
      args=(['--file', cls.db_filename,
             '--port', str(ServerTest.port),
             '--me', '1',
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

  def expect(self, path, args, expected):
    """Makes an HTTP request and checks the result.

    Args:
      path: string
      args: dict mapping string to string
      expected: string or regexp, or None

    Returns:
      string response
    """
    url = 'http://localhost:%d%s?%s' % (self.port, path, urllib.urlencode(args))
    resp = urllib2.urlopen(url).read()
    if expected:
      self.assertEquals(expected, resp)
    return resp

  def test_fql(self):
    query = 'SELECT username FROM profile WHERE id = me()'
    expected = '[{"username": "alice"}]'
    self.expect('/method/fql.query', {'query': query, 'format': 'json'}, expected)
    self.expect('/fql', {'q': query}, expected)

  def test_graph(self):
    self.expect('/1', {}, '{"foo": "bar", "id": "1"}')
    self.expect('/bob/albums', {}, '{"data": [{"id": "5"}]}')

  def test_oauth(self):
    args = {'client_id': 'x',
            'client_secret': 'y',
            'redirect_uri': 'http://localhost:%d/placeholder' % self.port,
            }
    try:
      self.expect('/dialog/oauth', args, None)
      self.fail('Expected 404 not found on placeholder redirect')
    except urllib2.HTTPError, e:
      self.assertEquals(404, e.code)
      url = e.url

    args['code'] = urlparse.parse_qs(urlparse.urlparse(url).query)['code'][0]
    resp = self.expect('/oauth/access_token', args, None)
    assert re.match('access_token=.+&expires=999999', resp), resp

  def test_404(self):
    try:
      resp = self.expect('/not_found', {}, '')
      fail('Should have raised HTTPError')
    except urllib2.HTTPError, e:
      self.assertEquals(404, e.code)


if __name__ == '__main__':
  ServerTest.start_server()
  atexit.register(lambda: ServerTest.stop_server())
  unittest.main()
