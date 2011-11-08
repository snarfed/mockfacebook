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

  Ideally the _test_*() methods would be real, top-level test methods, but
  starting and stopping the server for each test was too slow,
  and without class-level setUp() and tearDown(), I couldn 't hook into shutdown
  easily to stop the server. Not even an atexit handler worked. :/

  Attributes:
    db_filename: string SQLite db filename
    thread: Thread running the server
  """

  PORT = 60000
  db_filename = None
  thread = None

  def setUp(self):
    warnings.filterwarnings('ignore', 'tempnam is a potential security risk')
    self.db_filename = os.tempnam('/tmp', 'mockfacebook_test.')

    conn = testutil.make_test_db(self.db_filename)
    fql_test.insert_test_data(conn)
    graph_test.insert_test_data(conn)
    conn.close()

    started = threading.Event()
    self.thread = threading.Thread(
      target=server.main,
      args=(['--file', self.db_filename,
             '--port', str(self.PORT),
             '--me', '1',
             ],),
      kwargs={'started': started})
    self.thread.start()
    started.wait()

  def tearDown(self):
    server.server.shutdown()
    self.thread.join()

    try:
      os.remove(self.db_filename)
    except:
      pass

  def expect(self, path, args, expected):
    """Makes an HTTP request and optionally checks the result.

    Args:
      path: string
      args: dict mapping string to string
      expected: string or regexp, or None

    Returns:
      string response
    """
    url = 'http://localhost:%d%s?%s' % (self.PORT, path, urllib.urlencode(args))
    resp = urllib2.urlopen(url).read()
    if expected:
      self.assertEquals(expected, resp)
    return resp

  def test_all(self):
    self._test_fql()
    self._test_graph()
    self._test_oauth()
    self._test_404()

  def _test_fql(self):
    query = 'SELECT username FROM profile WHERE id = me()'
    expected = '[{"username": "alice"}]'
    self.expect('/method/fql.query', {'query': query, 'format': 'json'}, expected)
    self.expect('/fql', {'q': query}, expected)

  def _test_graph(self):
    self.expect('/1', {}, '{"foo": "bar", "id": "1"}')
    self.expect('/bob/albums', {}, '{"data": [{"id": "5"}]}')

  def _test_oauth(self):
    args = {'client_id': 'x',
            'client_secret': 'y',
            'redirect_uri': 'http://localhost:%d/placeholder' % self.PORT,
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

  def _test_404(self):
    try:
      resp = self.expect('/not_found', {}, '')
      fail('Should have raised HTTPError')
    except urllib2.HTTPError, e:
      self.assertEquals(404, e.code)


if __name__ == '__main__':
  unittest.main()
