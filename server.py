#!/usr/bin/python
"""mockfacebook is a mock HTTP server for the Facebook FQL and Graph APIs.

http://code.google.com/p/mockfacebook/

Top-level HTTP server:
  server.py [--port PORT] [--me USER_ID] [--file SQLITE_DB_FILE]
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import itertools
import logging
import optparse
import sqlite3
import sys
import wsgiref.simple_server

import webapp2

import fql
import graph
import oauth
import schemautil

# how often the HTTP server should poll for shutdown, in seconds
SERVER_POLL_INTERVAL = 0.5

# optparse.Values object that holds command line options
options = None

# if there are fewer than this many FQL or Graph API rows, print a warning.
ROW_COUNT_WARNING_THRESHOLD = 10


# order matters here! the first handler with a matching route is used.
HANDLER_CLASSES = (
  oauth.AuthCodeHandler,
  oauth.AccessTokenHandler,
  fql.FqlHandler,
  # note that this also includes the front page
  graph.GraphHandler,
  )


def application():
  """Returns the WSGIApplication to run.
  """
  routes = list(itertools.chain(*[cls.ROUTES for cls in HANDLER_CLASSES]))
  return webapp2.WSGIApplication(routes, debug=True)


def parse_args(argv):
  global options

  parser = optparse.OptionParser(
    description='mockfacebook is a mock HTTP server for the Facebook Graph API.')
  parser.add_option('-p', '--port', type='int', default=8000,
                    help='port to serve on (default %default)')
  parser.add_option('-f', '--db_file', default=schemautil.DEFAULT_DB_FILE,
                    help='SQLite database file (default %default)')
  parser.add_option('--me', type='str', default=1,
                    help='user id that me() should return (default %default)')

  options, args = parser.parse_args(args=argv)
  logging.debug('Command line options: %s' % options)


def warn_if_no_data(conn):
  for kind, tables in (('FQL', fql.FqlHandler.schema.tables.keys()),
                       ('Graph API', ('graph_objects', 'graph_connections'))):
    queries = ['SELECT COUNT(*) FROM `%s`;' % t for t in tables]
    # can't use executemany because it doesn't support placeholders for table
    # names. can't use executescript because it doesn't return results. :/
    count = sum(conn.execute(q).fetchall()[0][0] for q in queries)
    if count <= ROW_COUNT_WARNING_THRESHOLD:
      quantity = 'Only %d' % count if count > 0 else 'No'
      print '%s %s rows found. Consider inserting more or running download.py.' % (
        quantity, kind)


def main(args, started=None):
  """Args:
    args: list of string command line arguments
    started: an Event to set once the server has started. for testing.
  """
  parse_args(args)
  print 'Options: %s' % options

  conn = schemautil.get_db(options.db_file)
  for cls in HANDLER_CLASSES:
    cls.init(conn, options.me)

  # must run after FqlHandler.init() since that reads the FQL schema
  warn_if_no_data(conn)

  global server  # for server_test.ServerTest
  server = wsgiref.simple_server.make_server('', options.port, application())

  print 'Serving on port %d...' % options.port
  if started:
    started.set()
  server.serve_forever(poll_interval=SERVER_POLL_INTERVAL)


if __name__ == '__main__':
  main(sys.argv)
