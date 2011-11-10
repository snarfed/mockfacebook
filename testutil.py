"""Unit test utilities.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import cStringIO
import json
import re
import sqlite3
import sys
import unittest
import urllib

import webapp2

import schemautil
import server


def maybe_read(dataset_cls):
  """Tries to read and return a dataset. If it fails, prints an error.
  """
  try:
    return dataset_cls.read()
  except IOError, e:
    print >> sys.stderr, 'Warning: skipping example data tests due to:\n%s' % e
    return None


class HandlerTest(unittest.TestCase):
  """Base test class for webapp2 request handlers.

  Attributes:
    conn: SQLite db connection
    app: WSGIApplication
  """

  ME = '1'
  conn = None

  def setUp(self, *handler_classes):
    """Args:
    handler_classes: RequestHandlers to initialize
    """
    super(HandlerTest, self).setUp()

    self.conn = schemautil.get_db(':memory:')
    for cls in handler_classes:
      cls.init(self.conn, self.ME)

    self.app = server.application()

  def expect(self, path, expected, args=None, expected_status=200):
    """Makes a request and checks the response.

    Args:
      path: string
      expected: if string, the expected response body. if list or dict,
        the expected JSON response contents.
      args: passed to get_response()
      expected_status: integer, expected HTTP response status
    """
    response = None
    results = None
    try:
      response = self.get_response(path, args=args)
      self.assertEquals(expected_status, response.status_int)
      response = response.body
      if isinstance(expected, basestring):
        self.assertEquals(expected, response)
      else:
        results = json.loads(response)
        if not isinstance(expected, list):
          expected = [expected]
        if not isinstance(results, list):
          results = [results]
        expected.sort()
        results.sort()
        self.assertEquals(len(expected), len(results), `expected, results`)
        for e, r in zip(expected, results):
          self.assert_dict_equals(e, r)
    except:
      print >> sys.stderr, '\nquery: %s %s' % (path, args)
      print >> sys.stderr, 'expected: %r' % expected
      print >> sys.stderr, 'received: %r' % results if results else response
      raise

  def get_response(self, path, args=None):
    if args:
      path = '%s?%s' % (path, urllib.urlencode(args))
    return self.app.get_response(path)

  # TODO: for the love of god, refactor, or even better, find a more supported
  # utility somewhere else.
  def assert_dict_equals(self, expected, actual):
    msgs = []

    if isinstance(expected, re._pattern_type):
      if not re.match(expected, actual):
        self.fail("%r doesn't match %s" % (expected, actual))
    # this is only here because we don't exactly match FB in whether we return
    # or omit some "empty" values, e.g. 0, null, ''. see the TODO in graph_on_fql.py.
    elif not expected and not actual:
      return True
    elif isinstance(expected, dict) and isinstance(actual, dict):
      for key in set(expected.keys()) | set(actual.keys()):
        self.assert_dict_equals(expected.get(key), actual.get(key))
    else:
      if isinstance(expected, list) and isinstance(actual, list):
        expected.sort()
        actual.sort()
      self.assertEquals(expected, actual)
