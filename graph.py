"""Graph API request handler that uses the Graph API data in SQLite.

Based on http://developers.facebook.com/docs/reference/api/ .

Note that this code uses the term 'name' to mean something that's either an id
or an alias.

TODO:
- connections as first path element, e.g. /tagged?ids=...
- /fql?q=... for FQL:  https://developers.facebook.com/blog/post/579/
- handle requests without a leading /, e.g. '?ids=...'

- ?metadata=true introspection
- non-obvious id aliases, e.g. comment ids can have the user id as a prefix, or not:
  https://graph.facebook.com/212038_227980440569633_3361295
  https://graph.facebook.com/227980440569633_3361295
- batch requests: http://developers.facebook.com/docs/reference/api/batch/
- bug: /picture?ids=... returns picture for arbitrary id, should be *first* id
- ?date_format=...
- figure out when FB returns "Unsupported get request" vs "access token
  required" vs plain false.
- paging: ?limit=x, ?offset=y
- write support. publishing via POST, deleting via DELETE
  https://developers.facebook.com/docs/reference/api/#publishing
- field selection: https://developers.facebook.com/docs/reference/api/#reading
- return connections in order
- individual permissions
- messages: https://developers.facebook.com/docs/reference/api/message/
- reviews: https://developers.facebook.com/docs/reference/api/Review/
- real time updates: http://developers.facebook.com/docs/reference/api/realtime/
- insights: http://developers.facebook.com/docs/reference/api/insights/
- search: https://developers.facebook.com/docs/reference/api/#searching
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import logging
import json
import sqlite3
import traceback

import webapp2

import schemautil

# the one connection that returns an HTTP 302 redirect instead of a normal
# 200 with response data.
# http://developers.facebook.com/docs/reference/api/#pictures
REDIRECT_CONNECTION = 'picture'


class GraphError(Exception):
  """Base error class.

  Attributes:
    message: string
    status: integer
  """
  status = 400
  message = None

  def __init__(self, *args):
    self.message = self.message % args

class JsonError(GraphError):
  """JSON-formatted error class.

  Attributes:
    type: string
  """
  type = 'OAuthException'
    
  def __init__(self, *args):
    self.message = json.dumps({'error': {'message': self.message, 'type': self.type}})

class ObjectNotFoundError(GraphError):
  """Used for /<id> requests."""
  status = 200
  message = 'false'

class ObjectsNotFoundError(GraphError):
  """Used for /?ids=... requests."""
  status = 200
  message = '[\n\n]'

class AccessTokenError(JsonError):
  message = 'An access token is required to request this resource.'

class AliasNotFoundError(JsonError):
  status = 404
  message = '(#803) Some of the aliases you requested do not exist: %s'

class BadGetError(JsonError):
  message = 'Unsupported get request.'
  type = 'GraphMethodException'

class UnknownPathError(JsonError):
  message = 'Unknown path components: /%s'

class IdSpecifiedError(JsonError):
  message = 'Invalid token: \"%s\".  An ID has already been specified.'

class EmptyIdentifierError(JsonError):
  message = 'Cannot specify an empty identifier'

class NoNodeError(JsonError):
  message = 'No node specified'
  type = 'Exception'


class NameDict(dict):
  """Maps ids map to the names (eiter id or alias) they were requested by.

  Attributes:
    single: True if this request was of the form /<id>, False if it was of the
      form /?ids=...
  """
  pass


def is_int(str):
  """Returns True if str is an integer, False otherwise."""
  try:
    int(str)
    return True
  except ValueError:
    return False

not_int = lambda str: not is_int(str)


class GraphHandler(webapp2.RequestHandler):
  """Request handler class for Graph API handlers.

  This is a single class, instead of separate classes for objects and
  connections, because /xyz?... could be either an object or connection request
  depending on what xyz is.

  Class attributes:
    conn: sqlite3.Connection
    me: integer, the user id that /me should use
    schema: schemautil.GraphSchema
    all_connections: set of all string connection names
  """

  ROUTES = [webapp2.Route('/<id:[^/]*><connection:(/[^/]*)?>', 'graph.GraphHandler')]

  @classmethod
  def init(cls, conn, me):
    """Args:
      conn: sqlite3.Connection
      me: integer, the user id that /me should use
    """
    cls.conn = conn
    cls.me = me
    cls.schema = schemautil.GraphSchema.read()
    cls.all_connections = reduce(set.union, cls.schema.connections.values(), set())

  def get(self, id, connection):
    """Handles GET requests.
    """
    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'

    if connection:
      connection = connection[1:]  # strip the leading slash
    elif id in self.all_connections:
      connection = id
      id = None

    try:
      namedict = self.prepare_ids(id)

      if connection:
        resp = self.get_connections(namedict, connection)
      else:
        resp = self.get_objects(namedict)

      if namedict.single:
        if not resp:
          resp = []
        else:
          assert len(resp) == 1
          resp = resp.values()[0]
      self.response.out.write(json.dumps(resp))

    except GraphError, e:
      # i don't use webapp2's handle_exception() because there's no way to get
      # the original exception's traceback, which makes testing difficult.
      self.response.write(e.message)
      self.response.set_status(e.status)


  def get_objects(self, namedict):
    ids = namedict.keys()
    cursor = self.conn.execute(
      'SELECT id, data FROM graph_objects WHERE id IN (%s)' % self.qmarks(ids),
      ids)
    return dict((namedict[id], json.loads(data))
                for id, data in cursor.fetchall())

  def get_connections(self, namedict, connection):
    if connection not in self.all_connections:
      raise UnknownPathError(connection)

    ids = namedict.keys()
    query = ('SELECT id, data FROM graph_connections '
               'WHERE id IN (%s) AND connection = ?' % self.qmarks(ids))
    cursor = self.conn.execute(query, ids + [connection])
    rows = cursor.fetchall()

    if connection == REDIRECT_CONNECTION and rows:
      self.redirect(json.loads(rows[0][1]), abort=True)  # this raises

    resp = dict((name, {'data': []}) for name in namedict.values())
    for id, data in rows:
      resp[namedict[id]]['data'].append(json.loads(data))

    return resp

  def prepare_ids(self, path_id):
    """Returns the id(s) for this request.

    Looks at both path_id and the ids URL query parameter. Both can contain
    ids and/or aliases.

    Args:
      path_id: string

    Returns: NameDict

    Raises: GraphError if the query both path_id and ids are specified or an id is
      empty, 0, or not found
    """
    names = None
    if 'ids' in self.request.arguments():
      names = set(self.request.get('ids').split(','))

    if path_id:
      if names:
        raise IdSpecifiedError(path_id)
      names = set([path_id])

    if not all(name and name != '0' for name in names):
      raise EmptyIdentifierError()

    me = 'me' in names
    if me:
      names.remove('me')
      names.add(self.me)

    qmarks = self.qmarks(names)
    cursor = self.conn.execute(
      'SELECT id, alias FROM graph_objects WHERE id IN (%s) OR alias IN (%s)' %
        (qmarks, qmarks),
      tuple(names) * 2)

    namedict = NameDict()
    namedict.single = bool(path_id)
    for id, alias in cursor.fetchall():
      assert id in names or alias in names
      namedict[id] = 'me' if me else alias if alias in names else id

    not_found = names - set(namedict.values() + namedict.keys())
    if not_found:
      # the error message depends on whether any of the not found names are
      # aliases and whether this was ?ids= or /id.
      aliases = filter(not_int, not_found)
      if aliases:
        raise AliasNotFoundError(','.join(aliases))
      elif path_id:
        raise ObjectNotFoundError()
      else:
        raise ObjectsNotFoundError()

    return namedict

  def qmarks(self, values):
    """Returns a '?, ?, ...' string with a question mark per value.
    """
    return ','.join('?' * len(values))
