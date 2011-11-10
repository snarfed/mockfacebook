"""FQL request handler and support classes.

Based on https://developers.facebook.com/docs/reference/fql/ .
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import logging
import re
import json
import sqlite3
import time

import sqlparse
from sqlparse import sql
from sqlparse import tokens
import webapp2

import oauth
import schemautil


class FqlError(Exception):
  """Base error class.

  Attributes:
    code: integer error_code
    msg: string error_msg
  """
  code = None
  msg = None

  def __init__(self, *args):
    self.msg = self.msg % args

class UnexpectedError(FqlError):
  code = 601
  msg = "Parser error: unexpected '%s' at position <not implemented>."

class UnexpectedEndError(FqlError):
  code = 601
  msg = 'Parser error: unexpected end of query.'

class WildcardError(FqlError):
  code = 601
  msg = 'Parser error: SELECT * is not supported.  Please manually list the columns you are interested in.'

class NotIndexableError(FqlError):
  code = 604
  msg = 'Your statement is not indexable. The WHERE clause must contain an indexable column. Such columns are marked with * in the tables linked from http://developers.facebook.com/docs/reference/fql '

class InvalidFunctionError(FqlError):
  code = 605
  msg = '%s is not a valid function name.'

class ParamMismatchError(FqlError):
  code = 606
  msg = '%s function expects %d parameters; %d given.'

class SqliteError(FqlError):
  code = -1
  msg = 'SQLite error: %s'

class MissingParamError(FqlError):
  code = -1
  msg = 'The parameter %s is required'

class InvalidAccessTokenError(FqlError):
  code = 190
  msg = 'Invalid access token signature.'


class Fql(object):
  """A parsed FQL statement. Just a thin wrapper around sqlparse.sql.Statement.

  Attributes:
    query: original FQL query string
    me: integer, the user id that me() should return
    schema: schemautil.FqlSchema
    Statement: sqlparse.sql.Statement
    table: sql.Token or None
    where: sql.Where or None
  """

  # FQL functions. Maps function name to expected number of parameters.
  FUNCTIONS = {
    'me': 0,
    'now': 0,
    'strlen': 1,
    'substr': 3,
    'strpos': 2,
    }

  def __init__(self, schema, query, me):
    """Args:
      query: FQL statement
      me: integer, the user id that me() should return
    """
    logging.debug('parsing %s' % query)
    self.schema = schema
    self.query = query
    self.me = me
    self.statement = stmt = sqlparse.parse(query)[0]

    # extract table and WHERE clause, if any
    self.table = None
    self.where = None

    from_ = stmt.token_next_match(0, tokens.Keyword, 'FROM')
    if from_:
      index = stmt.token_index(from_)
      self.table = stmt.token_next(index)
      if self.table.is_group():
        self.table = self.table.token_first()

    self.where = stmt.token_next_by_instance(0, sql.Where)

    logging.debug('table %s, where %s' % (self.table, self.where))

  def table_name(self):
    """Returns the table name, or '' if None.
    """
    if self.table:
      return self.table.value
    else:
      return ''

  def validate(self):
    """Checks the query for Facebook API semantic errors.

    Returns the error response string if there is an error, otherwise None.
    """
    first = self.statement.tokens[0].value
    if first != 'SELECT':
      raise UnexpectedError(first)
    elif self.statement.token_next(1).match(tokens.Wildcard, '*'):
      raise WildcardError()
    elif not self.where:
      raise UnexpectedEndError()
    elif not self.table:
      raise UnexpectedError('WHERE')

    def check_indexable(token_list):
      """Recursive function that checks for non-indexable columns."""
      for tok in token_list.tokens:
        if tok.ttype == tokens.Name:
          col = self.schema.get_column(self.table.value, tok.value)
          if col and not col.indexable:
            raise NotIndexableError()
        elif isinstance(tok, (sql.Comparison, sql.Identifier)):
          check_indexable(tok)

    check_indexable(self.where)

  def to_sqlite(self):
    """Converts to a SQLite query.

    Specifically:
    - validates
    - processes functions
    - prefixes table names with underscores
    """
    self.validate()
    self.process_functions()
    self.table.value = '`%s`' % self.table.value
    return self.statement.to_unicode()

  def process_functions(self, group=None):
    """Recursively parse and process FQL functions in the given group token.

    Currently handles: me(), now()
    """
    if group is None:
      group = self.statement

    for tok in group.tokens:
      if isinstance(tok, sql.Function):
        assert isinstance(tok.tokens[0], sql.Identifier)
        name = tok.tokens[0].tokens[0]
        if name.value not in Fql.FUNCTIONS:
          raise InvalidFunctionError(name.value)

        # check number of params
        #
        # i wish i could use tok.get_parameters() here, but it doesn't work
        # with string parameters for some reason. :/
        assert isinstance(tok.tokens[1], sql.Parenthesis)
        params = [t for t in tok.tokens[1].flatten()
                  if t.ttype not in (tokens.Punctuation, tokens.Whitespace)]
        actual_num = len(params)
        expected_num = Fql.FUNCTIONS[name.value]
        if actual_num != expected_num:
          raise ParamMismatchError(name.value, expected_num, actual_num)

        # handle each function
        replacement = None
        if name.value == 'me':
          replacement = str(self.me)
        elif name.value == 'now':
          replacement = str(int(time.time()))
        elif name.value == 'strlen':
          # pass through to sqlite's length() function
          name.value = 'length'
        elif name.value == 'substr':
          # the index param is 0-based in FQL but 1-based in sqlite
          params[1].value = str(int(params[1].value) + 1)
        elif name.value == 'strpos':
          # strip quote chars
          string = params[0].value[1:-1]
          sub = params[1].value[1:-1]
          replacement = str(string.find(sub))
        else:
          # shouldn't happen
          assert False, 'unknown function: %s' % name.value

        if replacement is not None:
          tok.tokens = [sql.Token(tokens.Number, replacement)]

      elif tok.is_group():
        self.process_functions(tok)


class FqlHandler(webapp2.RequestHandler):
  """The FQL request handler.

  Not thread safe!

  Class attributes:
    conn: sqlite3.Connection
    me: integer, the user id that me() should return
    schema: schemautil.FqlSchema
  """

  XML_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<fql_query_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" list="true">
%s
</fql_query_response>"""
  XML_ERROR_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<error_response xmlns="http://api.facebook.com/1.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://api.facebook.com/1.0/ http://api.facebook.com/1.0/facebook.xsd">
%s
</error_response>"""

  ROUTES = [(r'/method/fql.query/?', 'fql.FqlHandler'),
            ('/fql', 'fql.FqlHandler'),
            ]

  @classmethod
  def init(cls, conn, me):
    """Args:
      conn: sqlite3.Connection
      me: integer, the user id that me() should return
    """
    cls.conn = conn
    cls.me = me
    cls.schema = schemautil.FqlSchema.read()

  def get(self):
    table = ''
    graph_endpoint = (self.request.path == '/fql')

    try:
      query_arg = 'q' if graph_endpoint else 'query'
      query = self.request.get(query_arg)
      if not query:
        raise MissingParamError(query_arg)

      token =  self.request.get('access_token')
      if token and not oauth.AccessTokenHandler.is_valid_token(self.conn, token):
        raise InvalidAccessTokenError()

      logging.debug('Received FQL query: %s' % query)

      fql = Fql(self.schema, query, self.me)
      # grab the table name before it gets munged
      table = fql.table_name()
      sqlite = fql.to_sqlite()
      logging.debug('Running SQLite query: %s' % sqlite)

      try:
        cursor = self.conn.execute(sqlite)
      except sqlite3.OperationalError, e:
        logging.debug('SQLite error: %s', e)
        raise SqliteError(unicode(e))

      results = self.schema.sqlite_to_json(cursor, table)

    except FqlError, e:
      results = self.error(self.request.GET, e.code, e.msg)

    if self.request.get('format') == 'json' or graph_endpoint:
      json.dump(results, self.response.out, indent=2)
    else:
      self.response.out.write(self.render_xml(results, table))

    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'

  def render_xml(self, results, table):
    """Renders a query result into an XML string response.

    Args:
      results: dict mapping strings to strings or lists of (key, value) tuples
      table: string table name
    """
    if 'error_code' in results:
      template = self.XML_ERROR_TEMPLATE
      results['request_args'] = [{'arg': elem} for elem in results['request_args']]
    else:
      template = self.XML_TEMPLATE
      results = [{table: row} for row in results]

    return template % self.render_xml_part(results)

  def render_xml_part(self, results):
    """Recursively renders part of a query result into an XML string response.

    Args:
      results: dict or list or primitive
    """

    if isinstance(results, (list, tuple)):
      return '\n'.join([self.render_xml_part(elem) for elem in results])
    elif isinstance(results, dict):
      elems = []
      for key, val in results.iteritems():
        list_attr = ' list="true"' if isinstance(val, list) else ''
        br = '\n' if isinstance(val, (list, dict)) else ''
        rendered = self.render_xml_part(val)
        elems.append('<%(key)s%(list_attr)s>%(br)s%(rendered)s%(br)s</%(key)s>' %
                     locals())
      return '\n'.join(elems)
    else:
      return unicode(results)

  def error(self, args, code, msg):
    """Renders an error response.

    Args:
      args: dict, the parsed URL query string arguments
      code: integer, the error_code
      msg: string, the error_msg

    Returns: the response string
    """
    args['method'] = 'fql.query'  # (always)
    request_args = [{'key': key, 'value': val} for key, val in args.items()]
    return {'error_code': code,
            'error_msg': msg,
            'request_args': request_args,
            }
