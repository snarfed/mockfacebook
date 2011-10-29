#!/usr/bin/python
"""Unit tests for graph_on_fql.py.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import re
import sys
import traceback
import unittest

import webapp2

import graph_on_fql
import schemautil
import testutil


class GraphOnFqlTest(testutil.HandlerTest):
  """Tests GraphApplication with the data in fql_data.sql and graph_data.py.
  """

  def setUp(self):
    super(GraphOnFqlTest, self).setUp(graph_on_fql.GraphOnFqlHandler, '/(.*)')

  def test_every_object_type(self):
    dataset = schemautil.GraphDataset.read()
    passed = True

    for table, data in dataset.data.items():
      try:
        self.expect('/%s' % data.query, data.data)
      except Exception:
        passed = False
        print 'Table: %s' % table
        traceback.print_exc()

    self.assertTrue(passed)

  def test_not_found(self):
    self.expect('/doesnt_exist', 'false')



if __name__ == '__main__':
  unittest.main()
