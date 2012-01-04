"""Graph API request handler that uses the Graph API data in SQLite.

Based on http://developers.facebook.com/docs/reference/api/ .

Note that this code uses the term 'name' to mean something that's either an id
or an alias.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import json
import os
import sqlite3
import traceback
import types
import urllib
import re

import datetime
import random
import sys

import webapp2

import oauth
import schemautil

# the one connection that returns an HTTP 302 redirect instead of a normal
# 200 with response data.
# http://developers.facebook.com/docs/reference/api/#pictures
REDIRECT_CONNECTION = 'picture'

# this is here because GraphHandler handles the "/" front page request when it
# has query parameters, e.g. /?ids=..., and webapp2 can't route based on query
# parameters alone.
FRONT_PAGE = """
<html>
<body>
<h2>Welcome to <a href="https://github.com/rogerhu/mockfacebook">mockfacebook</a>!</h2>
<p>This server is currently serving these endpoints:</p>
<table style="border-spacing: .5em">
<tr><td><a href="http://developers.facebook.com/docs/reference/api/">Graph API</a></td>
 <td><code>/...[/...]</code></td></tr>
<tr><td><a href="http://developers.facebook.com/docs/reference/fql/">FQL</a></td>
 <td><code>/method/fql.query</code> and <code>/fql</code></td></tr>
<tr><td><a href="http://developers.facebook.com/docs/authentication/">OAuth</a></td>
 <td><code>/dialog/oauth</code> and <code>/oauth/access_token</code></td></tr>
</table>
<p>See <code>README.md</code> and the
<a href="https://github.com/rogerhu/mockfacebook#readme">online docs</a> for more
information.</p>
</body>
</html>
"""

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
    self.message = json.dumps(
      {'error': {'message': self.message % args, 'type': self.type}},
      indent=2)

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

class ValidationError(JsonError):
  message = 'Error validating application.'

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

class InternalError(JsonError):
  status = 500
  message = '%s'
  type = 'InternalError'


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

class UTCTZ(datetime.tzinfo):
  def utcoffset(self, dt):
    return datetime.timedelta(0)
  def dst(self, dt):
    return datetime.timedelta(0)

utctz = UTCTZ()

class PostField(object):
  def __init__(self, name, required=False, is_argument=True, default="", arg_type=types.StringTypes, validator=None):
    """Represents a post field/argument

    Args:
      name: name of the argument
      required: set to True if the argument is required
      is_argument: if set to true, then field can be specified by the user (i.e. an argument)
      default: the default value to be used. This can be a string or a callback that returns a string
      arg_type: the Python type that this argument must be. The type must be JSON serializable
      validator: the callback to use to validate the argument.
    """
    self.name = name
    self.required = required
    self.is_argument = is_argument
    self.default = default
    self.arg_type = arg_type
    self.validator = validator

  def get_default(self, *args, **kwargs):
    if callable(self.default):
      return self.default(*args, **kwargs)
    return self.default

  def is_valid(self, arg):
    if not isinstance(arg, self.arg_type):
      return False
    if callable(self.validator):
      return self.validator(arg)
    return True

class MultiType(object):
  def __init__(self, *args):
    self.connections = args

DEFAULT_URL = "http://invalid/invalid"
YOUTUBE_LINK_RE = re.compile("http://[^/]*youtube")

def get_generic_id(*args, **kwargs):
  obj_id = kwargs.get("obj_id", "obj_id")
  return "%s_%s" % (obj_id, random.randint(0, sys.maxint))

def get_comment_id(*args, **kwargs):
  return get_generic_id(*args, **kwargs)

def get_note_id(*args, **kwargs):
  return get_generic_id(*args, **kwargs)

def get_photo_id(*args, **kwargs):
  return str(random.randint(0, sys.maxint))

def get_link_id(*args, **kwargs):
  return get_generic_id(*args, **kwargs)

def get_status_id(*args, **kwargs):
  return get_generic_id(*args, **kwargs)

def get_post_id(*args, **kwargs):
  return get_generic_id(*args, **kwargs)

def get_actions(*args, **kwargs):
  obj_id = kwargs.get("obj_id", "obj_id")
  obj_type = kwargs.get("type", "obj_type")
  gen_id = kwargs.get("id", "gen_id").split('_')[-1]
  return [{"name": "Comment", "link": "https://www.facebook.com/%s/%s/%s" % (obj_id, obj_type, gen_id)},
          {"name": "Like", "link": "https://www.facebook.com/%s/%s/%s" % (obj_id, obj_type, gen_id)}]

def get_comments(*args, **kwargs):
  return {"count": 0}

def get_name_from_link(*args, **kwargs):
  return kwargs.get("link", DEFAULT_URL)

def get_likes(*args, **kwargs):
  return {"data": []}

def get_from(*args, **kwargs):
  user_id = kwargs.get("user_id")
  return {"name": "Test", "category": "Test", "id": user_id}

def get_application(*args, **kwargs):
  return {"name": "TestApp", "canvas_name": "test", "namespace": "test", "id":"1234567890"}

def get_time(*args, **kwargs):
  return datetime.datetime.now(utctz).strftime("%Y-%m-%dT%H:%S:%M%z")

# TODO: support posting of events (attending, maybe, declined), albums (photos), and checkins
# Note: the order of the fields matter because the default values of some fields depend on the value of other fields.
#       "id" should always be first. and "type" should be before "action".
# Note: "posts" is not an actual type, and you can't publish to it. "posts" is just another way to get data from "feed"
CONNECTION_POST_ARGUMENTS = {"feed": MultiType("statuses", "links"),
                             "comments": [PostField("message", True),
                                          PostField("type", False, False, default="comment"),
                                          PostField("id", False, False, default=get_comment_id),
                                          PostField("from", False, False, arg_type=dict, default=get_from),
                                          PostField("created_time", False, False, default=get_time),
                                          PostField("likes", False, False, arg_type=int, default=0),
                                          # TODO: support user_likes
                                          ],
                             "notes": [PostField("subject", True),
                                       PostField("message", True),
                                       PostField("id", False, False, default=get_note_id),
                                       PostField("from", False, False, arg_type=dict, default=get_from),
                                       PostField("created_time", False, False, default=get_time),
                                       PostField("updated_time", False, False, default=get_time),
                                       # TODO: build out more stuff for notes
                                       ],
                             "photos":[PostField("message", True),
                                       PostField("source", True),
                                       PostField("id", False, False, default=get_photo_id),
                                       PostField("from", False, False, arg_type=dict, default=get_from),
                                       PostField("type", False, False, default="photo"),
                                       PostField("name", False, False, default=""),
                                       PostField("icon", False, False, default=DEFAULT_URL),
                                       PostField("picture", False, False, default=DEFAULT_URL),
                                       PostField("height", False, False, arg_type=int, default=100),  # TODO: detect the height and width from the image
                                       PostField("width", False, False, arg_type=int, default=100),
                                       PostField("link", False, False, default=DEFAULT_URL),
                                       PostField("created_time", False, False, default=get_time),
                                       PostField("updated_time", False, False, default=get_time)
                                       # TODO: support tags, images, and position
                                       ],
                             "links": [PostField("link", True, default=DEFAULT_URL),
                                       PostField("message", False),
                                       PostField("id", False, False, default=get_link_id),
                                       PostField("from", False, False, arg_type=dict, default=get_from),
                                       PostField("type", False, False, default="link"),
                                       PostField("name", False, False, default=get_name_from_link),
                                       PostField("caption", False, False),
                                       PostField("comments", False, False, arg_type=list, default=get_comments),
                                       PostField("description", False, False),
                                       PostField("icon", False, False, default=DEFAULT_URL),
                                       PostField("actions", False, False, arg_type=list, default=get_actions),
                                       PostField("application", False, False, arg_type=dict, default=get_application),
                                       PostField("picture", False, False, default=DEFAULT_URL),
                                       PostField("created_time", False, False, default=get_time),
                                       PostField("updated_time", False, False, default=get_time),
                                       ],
                             "statuses": [PostField("message", True, default=None),
                                          PostField("id", False, False, default=get_status_id),
                                          PostField("from", False, False, arg_type=dict, default=get_from),
                                          PostField("created_time", False, False, default=get_time),
                                          PostField("updated_time", False, False, default=get_time),
                                          PostField("type", False, False, default="status"),
                                          PostField("actions", False, False, arg_type=list, default=get_actions),
                                          PostField("comments", False, False, arg_type=dict, default=get_comments),
                                          PostField("icon", False, False, default=DEFAULT_URL),
                                          PostField("application", False, False, arg_type=dict, default=get_application),
                                          ]}


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

  ROUTES = [webapp2.Route('<id:(/[^/]*)?><connection:(/[^/]*)?/?>', 'graph.GraphHandler')]

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
    cls.posted_graph_objects = {}
    cls.posted_connections = {}  # maps id -> connection -> list of elements

  def _get(self, id, connection):
    if id in self.all_connections and not connection:
      connection = id
      id = None

    try:
      token =  self.request.get('access_token')
      if token and not oauth.AccessTokenHandler.is_valid_token(self.conn, token):
        raise ValidationError()

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
      return resp
    except GraphError as e:
      raise e


  def get(self, id, connection):
    """Handles GET requests.
    """
    if (id == '/' or not id) and not connection and not self.request.arguments():
      self.response.out.write(FRONT_PAGE)
      return

    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'

    # strip slashes
    if connection:
      connection = connection.strip("/")
    if id:
      id = id.strip("/")

    try:
      resp = self._get(id, connection)
      json.dump(resp, self.response.out, indent=2)
    except GraphError, e:
      # i don't use webapp2's handle_exception() because there's no way to get
      # the original exception's traceback, which makes testing difficult.
      self.response.write(e.message)
      self.response.set_status(e.status)


  def post(self, id, connection):
    id = id.strip("/")
    connection = connection.strip("/")

    # try to get the base object we're posting to
    try:
      graph_obj = self._get(id, None)
    except GraphError as e:
      self.response.write(e.message)
      self.response.set_status(e.status)
      return

    # validate the object type and connection
    try:
      obj_type = graph_obj.get("type")
      if obj_type is None:
        raise InternalError("object does not have a type")

      valid_connections =  self.schema.connections.get(obj_type)
      if valid_connections is None:
        raise InternalError("object type: %s is not supported" % obj_type)

      if connection not in valid_connections:
        raise InternalError("Connection: %s is not supported" % connection)
    except GraphError as e:
      self.response.write(e.message)
      self.response.set_status(e.status)
      return

    # TODO: validate that the mock is in sync with Facebook's metadata (except their metadata is really stale right now)
    #fields = self.schema.tables.get(obj_type)
    fields = []

    if self.update_graph_object(id, connection, graph_obj):
      resp = True
    else:
      # The connection determines what type of object to create
      try:
        graph_obj = self.create_graph_object(fields, self.request.POST, id, connection, graph_obj)
        obj_id = graph_obj["id"]
        GraphHandler.posted_graph_objects[obj_id] = graph_obj
        resp = {"id": obj_id}
      except GraphError as e:
        self.response.write(e.message)
        self.response.set_status(e.status)
        return

    # check the arguments

    # get the object w/ the given id and check it's type
    # lookup in the schema, the type and get the list of available options next.
    # Only some of those options are postable (does fb have a schema for this or do we just hardcode it?)
    # Then each option has a list of arguments it accepts (some require and some not) (does fb have a scheme for this or hardcode it?)
    # Note: hardcoding is possible b/c it's all documented (what's available and required) but it'd be better if they had a schema for this.

    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    json.dump(resp, self.response.out, indent=2)

  def delete(self, id, connection):
    if id == "/clear":
      GraphHandler.posted_graph_objects = {}
      GraphHandler.posted_connections = {}
      response_code = "ok"
    else:
      response_code = "fail"
    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    resp = {"response": response_code}
    json.dump(resp, self.response.out, indent=2)

  def get_objects(self, namedict):
    if not namedict:
      raise BadGetError()

    ids = namedict.keys()


    cursor = self.conn.execute(
      'SELECT id, data FROM graph_objects WHERE id IN (%s)' % self.qmarks(ids),
      ids)
    ret_dict = dict((namedict[obj_id], json.loads(data)) for obj_id, data in cursor.fetchall())

    # Anything in the published graph objects overwrite the normal results
    for obj_id in ids:
      if obj_id in GraphHandler.posted_graph_objects:
        ret_dict[obj_id] = GraphHandler.posted_graph_objects[obj_id]

    return ret_dict

  def get_connections(self, namedict, connection):
    if not namedict:
      raise NoNodeError()
    elif connection not in self.all_connections:
      raise UnknownPathError(connection)

    ids = namedict.keys()
    query = ('SELECT id, data FROM graph_connections '
               'WHERE id IN (%s) AND connection = ?' % self.qmarks(ids))
    cursor = self.conn.execute(query, ids + [connection])
    rows = cursor.fetchall()

    if connection == REDIRECT_CONNECTION and rows:
      self.redirect(json.loads(rows[0][1]), abort=True)  # this raises

    resp = {}
    # add posted data first b/c it must be newer
    for name in namedict.values():
      posted_data = GraphHandler.posted_connections.get(name, {}).get(connection, [])
      resp[name] = {"data": posted_data}

    for id, data in rows:
      resp[namedict[id]]['data'].extend(posted_data)
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
    names = set()
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
    for name in names:
      if name in GraphHandler.posted_graph_objects:
        namedict[name] = name

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

  def update_graph_object(self, id, connection, graph_object):
    if connection == "likes":
      liker = id  # TODO: get the the user performing the like
      like_data = graph_object.setdefault("likes", {"data": []})["data"]
      for data in like_data:
        if data["id"] == liker:
          return True  # probably should be False, but Facebook returns True
      like_data.append({"id": liker, "name":"Test", "category": "Test"})
      GraphHandler.posted_graph_objects[id] = graph_object  # keep a copy the graph object to modify it
      return True
    return False

  def create_blob_from_args(self, obj_id, fields, spec, args):
    """
    Args:
      fields: The known fields given by Facebook's metadata
      spec: The argument specification
      args: The arguments to use to create the blob

    Returns:
    Raises: GraphError
    """
    # TODO: validate that the mock is in sync with Facebook's metadata (except their metadata is really stale right now)
    # field_names = set([f.name for f in fields])
    # spec_names = set([a.name for a in spec])
    # removed_arguments = spec_names - field_names
    # if len(removed_arguments) > 0:
    #   raise InternalError("Update the mock. The following arguments are no longer supported by Facebook: %s" % ",".join(removed_arguments))

    default_args = {"obj_id": obj_id,
                    "user_id": self.me,   # TODO: get the user_id from the access_token
                    }

    blob = {}
    for field in spec:
      arg_value = args.get(field.name)
      # Facebook currently doesn't return errors if required arguments are not specified, they just have default values
      if arg_value is None:
        arg_value = field.get_default(**default_args)
      else:
        if not field.is_valid(arg_value):
          arg_value = field.get_default(**default_args)
        else:
          if field.name == "picture":  # Facebook automatically proxies pictures
            # TODO: figure out how facebook generates the checksum (looks like MD5), v, and size attributes
            arg_value = "https://www.facebook.com/app_full_proxy.php?app=1234567890&v=1&size=z&cksum=0&src=%s" % urllib.quote_plus(arg_value)
      if arg_value is not None:
        blob[field.name] = arg_value

      # populate the default_args
      default_args[field.name] = arg_value

    return blob


  def create_graph_object(self, fields, arguments, id, connection, parent_obj):
    argument_spec = CONNECTION_POST_ARGUMENTS.get(connection)
    if argument_spec is None:
      raise InternalError("Connection: %s is not supported. You can add it yourself. :)")

    if isinstance(argument_spec, MultiType):
      last_exception = InternalError("Could not parse POST arguments")
      if "link" in arguments and "links" in argument_spec.connections:
        blob = self.create_blob_from_args(id, fields, CONNECTION_POST_ARGUMENTS.get("links"), arguments)

        # Facebook detects YouTube links and changes the type to swf
        if YOUTUBE_LINK_RE.search(blob.get("link", "")):
          blob["type"] = "swf"

        connections = GraphHandler.posted_connections.setdefault(id, {})
        connections.setdefault(connection, []).insert(0,blob)
        if connection == "feed":
          connections.setdefault("posts", []).insert(0,blob)  # posts mirror feed
        return blob
      for c in argument_spec.connections:
        try:
          blob = self.create_blob_from_args(id, fields, CONNECTION_POST_ARGUMENTS.get(c), arguments)
          connections = GraphHandler.posted_connections.setdefault(id, {})
          connections.setdefault(connection, []).insert(0,blob)
          if connection == "feed":
            connections.setdefault("posts", []).insert(0,blob)  # posts mirror feed
          return blob
        except GraphError as e:
          last_exception = e
      raise last_exception
    else:
      blob = self.create_blob_from_args(id, fields, argument_spec, arguments)
      if parent_obj is not None:
        connection_obj = parent_obj.get(connection)
        if connection_obj is not None:
          # update the parent object if there is a list of this connection stored there
          connection_obj["count"] += 1
          data = connection_obj.setdefault("data", [])
          data.append(blob)

      return blob
