#!/usr/bin/python
"""Unit tests for server.py.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import json
import os
import re
import threading
import unittest
import urllib
import urllib2
import urlparse
import warnings

import fql_test
import graph_test
import schemautil
import server
import testutil


TIME_RE = re.compile("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4}", re.MULTILINE)


def get_data(port, path, args, data=None, method=None):
  url = 'http://localhost:%d%s?%s' % (port, path, urllib.urlencode(args))
  request = urllib2.Request(url, data)
  if method is not None:
    request.get_method = lambda: method
  return urllib2.urlopen(request).read()


def replace_ids(obj_id, string):
  composite_id = obj_id
  obj_id = composite_id.split("_")[-1]
  return string.replace(composite_id, "COMPOSITE_ID").replace(obj_id, "OBJECT_ID")


class ServerTest(unittest.TestCase):
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

    conn = schemautil.get_db(self.db_filename)
    fql_test.insert_test_data(conn)
    graph_test.insert_test_data(conn)
    conn.close()

    started = threading.Event()
    self.thread = threading.Thread(
      target=server.main,
      args=(['--db_file', self.db_filename,
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

  def expect(self, path, args, expected, data=None, method=None):
    """Makes an HTTP request and optionally checks the result.

    Args:
      path: string
      args: dict mapping string to string
      expected: string or regexp, or None
      method: the HTTP request method to use. i.e. GET, POST, DELETE, PUT

    Returns:
      string response
    """
    resp = get_data(self.PORT, path, args, data, method)
    if expected:
      self.assertEquals(json.loads(expected), json.loads(resp))
    return resp

  def check_fb_result(self, obj_id, result, expected):
    """Checks the given Facebook result against the given expected result
       This will use regular expressions to replace Facebook ids and timestamps

    Args:
      obj_id: The Facebook object id
      result: The result from the mock to check. Will be cleaned by regexes.
      expected: The expected result. Should contain the regex cleaned result.
    """
    result_cleaned = replace_ids(obj_id, TIME_RE.sub("TIMESTAMP", result))
    # print result_cleaned.replace("\n", "\\n")  # useful for getting the expected output
    self.assertEquals(json.loads(result_cleaned), json.loads(expected))

  def test_all(self):
    self._test_post_and_delete()
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
    self.expect('/me', {}, '{\n  "foo": "bar", \n  "id": "1"\n}')

  def _test_post_and_delete(self):
    resp = get_data(self.PORT, "/3/feed", {}, method="POST")
    resp_json = json.loads(resp)
    status_id = resp_json["id"]
    resp = get_data(self.PORT, "/%s" % status_id, {})

    # verify the correct the correct data was posted.
    expected_status = '{\n  "from": {\n    "category": "Test", \n    "name": "Test", \n    "id": "1"\n  }, \n  "actions": [\n    {\n      "link": "https://www.facebook.com/3/status/OBJECT_ID", \n      "name": "Comment"\n    }, \n    {\n      "link": "https://www.facebook.com/3/status/OBJECT_ID", \n      "name": "Like"\n    }\n  ], \n  "updated_time": "TIMESTAMP", \n  "application": {\n    "id": "1234567890", \n    "namespace": "test", \n    "name": "TestApp", \n    "canvas_name": "test"\n  }, \n  "comments": {\n    "count": 0\n  }, \n  "created_time": "TIMESTAMP", \n  "type": "status", \n  "id": "COMPOSITE_ID", \n  "icon": "http://invalid/invalid"\n}'
    self.check_fb_result(status_id, resp, expected_status)

    # make sure the publish shows up in the feed
    resp = get_data(self.PORT, "/3/feed", {})
    self.check_fb_result(status_id, resp, '{\n  "data": [\n    %s\n  ]\n}' % expected_status)
    # feed should be the same as posts
    self.assertEquals(resp, get_data(self.PORT, "/3/posts", {}))

    # add a comment
    resp = get_data(self.PORT, "/%s/comments" % status_id, {}, method="POST")
    resp_json = json.loads(resp)
    comment_id = resp_json["id"]
    # check that the comment is there
    resp = get_data(self.PORT, "/%s" % comment_id, {})
    expected_comment = '{\n  "from": {\n    "category": "Test", \n    "name": "Test", \n    "id": "1"\n  }, \n  "likes": 0, \n  "created_time": "TIMESTAMP", \n  "message": "", \n  "type": "comment", \n  "id": "COMPOSITE_ID"\n}'
    self.check_fb_result(comment_id, resp, expected_comment)
    # check that the post has the comment
    expected_status_2 = json.loads(expected_status)
    expected_status_2["comments"] = {"count": 1, "data": [json.loads(expected_comment)]}
    resp = get_data(self.PORT, "/%s" % status_id, {})
    self.check_fb_result(status_id, replace_ids(comment_id, resp), json.dumps(expected_status_2))

    # Test clearing posts
    self.expect("/clear", {}, '{"response": "ok"}', method="DELETE")
    self.assertRaises(urllib2.HTTPError, get_data, self.PORT, '/%s' % status_id, {})
    self.expect('/3/feed', {}, '{\n  "data": []\n}')

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
      self.fail('Should have raised HTTPError')
    except urllib2.HTTPError, e:
      self.assertEquals(404, e.code)


if __name__ == '__main__':
  unittest.main()
