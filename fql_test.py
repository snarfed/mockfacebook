#!/usr/bin/python
"""Unit tests for fql.py.

TODO: test subselects, other advanced features
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import httplib
import json
import threading
import time
import traceback
import unittest
import urllib

import fql
import schemautil
import testutil

SCHEMA = schemautil.FqlSchema.read()


class FqlTest(unittest.TestCase):
  """Tests the Fql class.
  """

  def fql(self, query):
    return fql.Fql(SCHEMA, query, testutil.ME)

  def test_table(self):
    self.assertEquals(None, self.fql('SELECT *').table)
    self.assertEquals('foo', self.fql('SELECT * FROM foo').table.value)
    self.assertEquals(None, self.fql('SELECT * WHERE x').table)

    # table names that are keywords should still work
    self.assertEquals('comment', self.fql('SELECT * FROM comment').table.value)

  def test_where(self):
    self.assertEquals(None, self.fql('SELECT *').where)
    self.assertEquals(None, self.fql('SELECT * FROM foo').where)

    for query in ('SELECT * FROM foo WHERE bar', 'SELECT * WHERE bar'):
      where = self.fql(query).where
      self.assertEquals('WHERE', where.tokens[0].value)
      self.assertEquals('bar', where.tokens[2].get_name())


class FqlHandlerTest(testutil.HandlerTest):
  """Tests FqlHandler with the data in fql_data.sql and fql_data.py.
  """

  def setUp(self):
    super(FqlHandlerTest, self).setUp(fql.FqlHandler)
    self.conn.executescript(SCHEMA.to_sql())
    self.conn.commit()

  def expect_fql(self, fql, expected, format='json'):
    """Runs an FQL query and checks the response.

    Args:
      fql: string
      expected: list or dict that the JSON response should match
      format: passed as the format URL query parameter
    """
    super(FqlHandlerTest, self).expect('/method/fql.query', expected,
                                       {'format': format, 'query': fql})

  def expect_error(self, query, error):
    """Runs a query and checks that it returns the given error code and message.

    Args:
      fql: string
      error: expected error
    """
    expected = {
      'error_code': error.code,
      'error_msg': error.msg,
      'request_args': [
        # order here matters, since the list is compared by value.
        {'key': 'query', 'value': query},
        {'key': 'format', 'value': 'json'},
        {'key': 'method', 'value': 'fql.query'},
        ]}
    self.expect_fql(query, expected)

  def test_example_data(self):
    dataset = testutil.maybe_read(schemautil.FqlDataset)
    if not dataset:
      return

    self.conn.executescript(dataset.to_sql())
    self.conn.commit()
    fql.FqlHandler.me = dataset.data['user'].data[0]['uid']
    passed = True

    for table, data in dataset.data.items():
      try:
        self.expect_fql(data.query, data.data)
      except Exception:
        passed = False
        print 'Table: %s' % table
        traceback.print_exc()

    self.assertTrue(passed)

  def test_multiple_where_conditions(self):
    self.expect_fql(
      'SELECT username FROM profile WHERE id = me() AND username = "snarfed.org"',
      [{'username': 'snarfed.org'}])

  def test_me_function(self):
    queries = ['SELECT username FROM %s = me()' % clause
               for clause in ('user WHERE uid', 'profile WHERE id')]
    for query in queries:
      self.expect_fql(query, [{'username': 'snarfed.org'}])

    # try a different value for me()
    fql.FqlHandler.init(self.conn, testutil.ME + 1)
    for query in queries:
      self.expect_fql(query, [])

  def test_now_function(self):
    orig_time = time.time
    try:
      time.time = lambda: 3.14
      self.expect_fql('SELECT now() FROM profile WHERE id = me()',
                      [{'3': 3}])
    finally:
      time.time = orig_time

  def test_strlen_function(self):
    self.expect_fql('SELECT strlen("asdf") FROM profile WHERE id = me()',
                    [{'length("asdf")': 4}])
    self.expect_fql('SELECT strlen(username) FROM profile WHERE id = me()',
                    [{'length(username)': 11}])

    self.expect_error('SELECT strlen() FROM profile WHERE id = me()',
                      fql.ParamMismatchError('strlen', 1, 0))
    self.expect_error('SELECT strlen("asdf", "qwert") FROM profile WHERE id = me()',
                      fql.ParamMismatchError('strlen', 1, 2))

  def test_substr_function(self):
    self.expect_fql('SELECT substr("asdf", 1, 2) FROM profile WHERE id = me()',
                    [{'substr("asdf", 2, 2)': 'sd'}])
    self.expect_fql('SELECT substr("asdf", 1, 6) FROM profile WHERE id = me()',
                    [{'substr("asdf", 2, 6)': 'sdf'}])

    self.expect_error('SELECT substr("asdf", 0) FROM profile WHERE id = me()',
                      fql.ParamMismatchError('substr', 3, 2))

  def test_strpos_function(self):
    self.expect_fql('SELECT strpos("asdf", "sd") FROM profile WHERE id = me()',
                    [{'1': 1}])
    self.expect_fql('SELECT strpos("asdf", "x") FROM profile WHERE id = me()',
                    [{'-1': -1}])

    self.expect_error('SELECT strpos("asdf") FROM profile WHERE id = me()',
                      fql.ParamMismatchError('strpos', 2, 1))

  def test_composite_fql_types(self):
    # array
    self.expect_fql('SELECT meeting_sex FROM user WHERE uid = me()',
                    [{'meeting_sex': ['female']}])
    # comments
    self.expect_fql('SELECT comments FROM comment WHERE object_id = 130490263692746',
                    [{'comments': []}, {'comments': []}])
    # object
    self.expect_fql('SELECT venue FROM group WHERE gid = 13243224451',
                    [{'venue': {'city': 'West Portland',
                                'country': 'United States',
                                'longitude': -122.73099999999999,
                                'state': 'Oregon',
                                'street': '',
                                'latitude': 45.454999999999998,
                                }}])

  def test_non_indexable_column_error(self):
    self.expect_error('SELECT id FROM profile WHERE pic = "http://url.to/image"',
                      fql.NotIndexableError())

    # check that non-indexable columns inside strings are ignored
    self.expect_fql('SELECT id FROM profile WHERE username = "pic pic_big type"', [])

  def test_xml_format(self):
    self.expect_fql(
      'SELECT id, name, url, type, username FROM profile WHERE id = me()',
      """<?xml version="1.0" encoding="UTF-8"?>
<fql_query_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" list="true">
<profile>
<url>http://www.facebook.com/snarfed.org</url>
<username>snarfed.org</username>
<type>user</type>
<id>%d</id>
<name>Ryan Barrett</name>
</profile>
</fql_query_response>""" % testutil.ME,
      format='xml')

  def test_format_defaults_to_xml(self):
    for format in ('foo', ''):
      self.expect_fql(
        'SELECT username FROM profile WHERE id = me()',
        """<?xml version="1.0" encoding="UTF-8"?>
<fql_query_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" list="true">
<profile>
<username>snarfed.org</username>
</profile>
</fql_query_response>""",
        format=format)

  def test_xml_format_error(self):
    self.expect_fql(
      'SELECT strlen() FROM profile WHERE id = me()',
      """<?xml version="1.0" encoding="UTF-8"?>
<error_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://api.facebook.com/1.0/ http://api.facebook.com/1.0/facebook.xsd">
<error_code>606</error_code>
<error_msg>strlen function expects 1 parameters; 0 given.</error_msg>
<request_args list="true">
<arg>
<value>SELECT strlen() FROM profile WHERE id = me()</value>
<key>query</key>
</arg>
<arg>
<value>xml</value>
<key>format</key>
</arg>
<arg>
<value>fql.query</value>
<key>method</key>
</arg>
</request_args>
</error_response>""",
      format='xml')

  def test_no_select_error(self):
    self.expect_error('INSERT id FROM profile WHERE id = me()',
                      fql.UnexpectedError('INSERT'))

  def test_no_table_error(self):
    self.expect_error('SELECT id', fql.UnexpectedEndError())

  def test_no_where_error(self):
    self.expect_error('SELECT id FROM profile', fql.UnexpectedEndError())

  def test_where_and_no_table_error(self):
    self.expect_error('SELECT name WHERE id = me()', fql.UnexpectedError('WHERE'))

  def test_invalid_function_error(self):
    self.expect_error('SELECT name FROM profile WHERE foo()',
                      fql.InvalidFunctionError('foo'))

  def test_wildcard_error(self):
    self.expect_error('SELECT * FROM profile WHERE id = me()',
                      fql.WildcardError())

  def test_sqlite_error(self):
    self.expect_error('SELECT bad syntax FROM profile WHERE id = me()',
                      fql.SqliteError('no such column: bad'))

  def test_no_query_error(self):
    self.expect_error('', fql.MissingParamError('query'))


if __name__ == '__main__':
  unittest.main()
