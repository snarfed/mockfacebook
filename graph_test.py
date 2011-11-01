#!/usr/bin/python
"""Unit tests for graph.py.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import re
import sys
import traceback
import unittest

import graph
import schemautil
import testutil


class TestBase(testutil.HandlerTest):

  dataset = schemautil.GraphDataset.read()

  def _test_every(self, data):
    """Args:
      data: list of Data or Connection with url paths and expected results
    """
    for datum in data:
      self.expect('/%s' % datum.query, datum.data)

  def expect_redirect(self, path, redirect_to):
    resp = self.get_response(path)
    self.assertEquals(302, resp.status_int)
    self.assertEquals(redirect_to, resp.headers['Location'])

  def expect_error(self, path, exception):
    """Args:
      path: string
      exception: expected instance of a GraphError subclass
    """
    self.expect(path, exception.message, expected_status=exception.status)


class ObjectTest(TestBase):

  def setUp(self):
    super(ObjectTest, self).setUp(graph.ObjectHandler)
    self.snarfed = self.dataset.data['snarfed.org'].data
    self.hearsay = self.dataset.data['hearsaysocial'].data

  def test_every_data(self):
    self._test_every(self.dataset.data.values())

  def test_alias(self):
    self.expect('/snarfed.org', self.snarfed)

  def test_not_found(self):
    self.expect_error('/123', graph.ObjectNotFoundError())

  def test_single_ids_not_found(self):
    self.expect_error('/?ids=123', graph.ObjectsNotFoundError())

  def test_multiple_ids_not_found(self):
    self.expect_error('/?ids=123,456', graph.ObjectsNotFoundError())

  def test_alias_not_found(self):
    for bad_query in '/foo', '/?ids=foo', '/?ids=snarfed.org,foo':
      self.expect_error(bad_query, graph.AliasNotFoundError('foo'))

    self.expect_error('/?ids=foo,bar', graph.AliasNotFoundError('foo,bar'))

  def test_id_already_specified(self):
    self.expect_error('/foo?ids=bar', graph.IdSpecifiedError('foo'))

  def test_empty_identifier(self):
    for bad_query in '/?ids=', '/?ids=snarfed.org,', '/?ids=snarfed.org,,212038':
      self.expect_error(bad_query, graph.EmptyIdentifierError())

  def test_ids_query_param(self):
    self.expect('/?ids=snarfed.org,hearsaysocial',
                {'snarfed.org': self.snarfed, 'hearsaysocial': self.hearsay})
    self.expect('/?ids=hearsaysocial,212038',
                {'212038': self.snarfed, 'hearsaysocial': self.hearsay})

  def test_ids_always_prefers_alias(self):
    self.expect('/?ids=snarfed.org,212038', {'snarfed.org': self.snarfed})
    self.expect('/?ids=212038,snarfed.org', {'snarfed.org': self.snarfed})


class ConnectionTest(TestBase):

  def setUp(self):
    super(ConnectionTest, self).setUp(graph.ConnectionHandler)
    self.snarfed_albums = self.dataset.connections['snarfed.org/albums'].data
    self.hearsay_albums = self.dataset.connections['hearsaysocial/albums'].data

  def test_every_connection(self):
    self._test_every(conn for conn in self.dataset.connections.values()
                     if conn.name != graph.REDIRECT_CONNECTION)

  def test_id(self):
    self.expect('/212038/albums', self.snarfed_albums)

  def test_alias(self):
    self.expect('/snarfed.org/albums', self.snarfed_albums)

  def test_id_not_found(self):
    self.expect('/123/albums', 'false')

  def test_alias_not_found(self):
    self.expect_error('/foo/albums', graph.AliasNotFoundError('foo'))

  def test_connection_not_found(self):
    self.expect_error('/snarfed.org/foo', graph.UnknownPathError('foo'))

  def test_no_connection_data(self):
    self.expect('/snarfed.org/family', {'data': []})
    self.expect('//family?ids=snarfed.org', {'snarfed.org': {'data': []}})

  def test_ids_query_param(self):
    self.expect('//albums?ids=snarfed.org,hearsaysocial',
                {'snarfed.org': self.snarfed_albums,
                 'hearsaysocial': self.hearsay_albums,
                 })

  def test_picture_redirect(self):
    for path in ('/snarfed.org/picture',
                 '//picture?ids=snarfed.org',
                 '//picture?ids=snarfed.org,hearsaysocial'):
      expected = self.dataset.connections['snarfed.org/picture'].data['data'][0]
      self.expect_redirect(path, expected)


if __name__ == '__main__':
  unittest.main()
