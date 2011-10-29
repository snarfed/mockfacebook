#!/usr/bin/python
"""Generates FQL and Graph API schemas and example data.

Usage: make_schema.py [options] ACCESS_TOKEN

Gets the schema by scraping the Facebook API docs, and the example data by
querying the user's own data with the given access token. Writes the schemas and
example data as Python dictionaries (see schemautil.py), and also writes the FQL
schemas and example data as SQLite CREATE TABLE and INSERT statements.

You can get an access token here:
http://developers.facebook.com/tools/explorer?method=GET&path=me

You'll need to grant it pretty much all available permissions.

# TODO: update
Here's the process:
1. Fetch the Facebook FQL docs.
2. Scrape the HTML and generate a CREATE TABLE statement for each FQL table.
3. Write those statements, plus a couple more mockfacebook-specific tables, to
the schema files.
4. Fetch one or more rows of real Facebook data for each table, via FQL queries.
5. Writes those rows to the FQL example data files.
4. Fetch real Graph API objects for each Graph API object type.
5. Writes those objects to the Graph API example data file.


Here's a script to download of the FQL and Graph API reference docs:

#!/bin/tcsh
cd ~/docs/facebook/
foreach dir (api fql)
  wget --mirror --html-extension --page-requisites --no-host-directories \
    --cut-dirs=2 --include-directories=/docs/reference/$dir/ \
    http://developers.facebook.com/docs/reference/$dir/

  # remove the auto-redirect to developers.facebook.com and convert links to
  # absolute file:/// url. (wget --convert-links makes them relative.)
  find $dir -type f | xargs sed -ri '\
    s/<script .+\/script>//g; \
    s/<a href="http:\/\/developers.facebook.com\/docs\/reference([^"]+)"/<a href="file:\/\/\/home\/ryanb\/docs\/facebook\1index.html"/g'
end


TODO:
- diff and notify of new columns, tables, changes etc. store old schema or
  deltas until explicitly dismissed so you can run it multiple times and still
  know what to go update later.
- look at BeautifulSoup or something similar for scraping
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import collections
import httplib
import itertools
import json
import logging
import operator
import optparse
import re
import sys
import traceback
import urllib
import urllib2
import urlparse

import graph
import schemautil


HTTP_RETRIES = 5
HTTP_TIMEOUT_S = 20

# regexps for scraping facebook docs. naturally, these are very brittle.
# TODO: use something like BeautifulSoup instead.
TABLE_RE = re.compile('<h1> *(?P<name>\w+)[^<]*</h1>')
TABLE_LINKS_RE = re.compile("""\
<h2 id="(objects|tables)">(Objects|Tables)</h2><div class="refindex">\
(<div class="page">.+
</div></div>)+""")
TABLE_LINK_RE = re.compile('<div class="title"><a href="([^"]+)"')
FQL_COLUMN_RE = re.compile("""\
<td class="indexable">(?P<indexable>\\*|)</td>\
<td class="name"> *(?P<name>[^< ]+) *</td>\
<td class="type"> *(?P<fb_type>[^< ]+) *</td>\
""")
GRAPH_COLUMN_RE = re.compile("""\
(?P<indexable>)\
</td></tr><tr><td><code>(?P<name>.+)</code></td><td><p>.+</p>
</td><td><p>.+</p>
</td><td><p>(?:<code>)?(?P<fb_type>\w+).*</p>\
""")

# regexp for extracting the fb type from a graph api metadata field description
# e.g.: "The user's birthday. `user_birthday`. Date `string` in `MM/DD/YYYY` format."
GRAPH_DESCRIPTION_TYPE_RE = re.compile('\\. *`?(\w+)[^.]*\\.? *$')

# maps Facebook column type to (sanitized type name, SQLite type). unknown
# types map to no (ie unspecified) SQLite type.
COLUMN_TYPES = {
  'array':      ('array', ''),
  'booelean':   ('bool', 'INTEGER'), # typo for application.is_facebook_app
  'bool':       ('bool', 'INTEGER'),
  'boolean':    ('bool', 'INTEGER'),
  'comments':   ('array', ''),       # only comment.comments
  'contains':   ('object', ''),      # Post.to: "Contains in `data` an array..."
  'date':       ('string', 'TEXT'),  # User.birthday: "Date `string`..."
  'dictionary': ('object', ''),
  'float':      ('float', 'REAL'),
  'int':        ('int', 'INTEGER'),
  'integer':    ('int', 'INTEGER'),
  'number':     ('int', 'INTEGER'),
  'object':     ('object', ''),
  'string':     ('string', 'TEXT'),
  'structure':  ('object', ''),
  'time':       ('int', 'INTEGER'),
  'uid':        ('int', 'INTEGER'),
}

# overridden column types. maps table name to dict mapping column name to
# facebook type. lower case tables are FQL, capitalized tables are Graph API.
#
# Filed a Facebook API bug to fix the docs:
# http://bugs.developers.facebook.net/show_bug.cgi?id=20470
OVERRIDE_COLUMN_TYPES = collections.defaultdict(dict, {
    # FQL tables
    'album': {'cover_object_id': 'string', },
    'application': {'app_id': 'string', 'developers': 'object', },
    'comment': {'id': 'string', 'object_id': 'int', },
    'domain_admin': {'domain_id': 'string', 'owner_id': 'string', },
    'event': {'venue': 'object', },
    'friend': {'uid1': 'string', 'uid2': 'string', },
    'friendlist': {'owner': 'integer', },
    'friendlist_member': {'uid': 'integer', },
    'group': {'version': 'int', },
    'group_member': {'positions': 'object', },
    'link': {'link_id': 'int', },
    'like': {'object_id': 'int', }, #'version': 'int', },
    'page': {'hours': 'object', 'is_community_page': 'boolean',
             'location': 'object', 'parking': 'object', },
    'page_fan': {'uid': 'int', 'page_id': 'int', },
    'place': {'page_id': 'int', },
    'photo': {
      'owner': 'string', 'src_big_height': 'int', 'src_big_width': 'int',
      'src_small_height': 'int', 'src_small_width': 'int',
      'src_height': 'int', 'src_width': 'int',
      },
    'photo_tag': {'subject': 'string', },
    'privacy': {'id': 'int', 'object_id': 'int', },
    'profile': {'pic_crop': 'object', },
    'status': {'status_id': 'int', 'source': 'int', 'time': 'int', },
    'stream': {'actor_id': 'int', },
    'stream_filter': {'uid': 'int', },
    'user': {'timezone': 'int', },
    'video': {'vid': 'int', },
    })

# overridden indexable columns. maps table name to dict mapping column name to
# boolean for whether the column is indexable. Filed a Facebook API bug to fix
# the docs:
# http://bugs.developers.facebook.net/show_bug.cgi?id=20472
OVERRIDE_COLUMN_INDEXABLE = collections.defaultdict(dict, {
    'connection': {'target_id': True, },
    'friend_request': {'uid_from': True, },
    'friendlist_member': {'uid': True, },
    'like': {'user_id': True, },
    'stream_filter': {'filter_key': True, },
    })

# these aren't just flat tables, they're more complicated.
UNSUPPORTED_TABLES = ('insights', 'permissions', 'Subscription')

# query snippets used in a few WHERE clauses for fetching FQL example data.
#
MY_IDS = 'id = me() OR id IN (SELECT uid2 FROM friend WHERE uid1 = me())'
MY_UIDS = 'uid = me() OR uid IN (SELECT uid2 FROM friend WHERE uid1 = me())'
MY_ALBUM_IDS = '(SELECT aid FROM album WHERE owner = me())'
MY_APP_IDS = \
    'app_id IN (SELECT application_id FROM developer WHERE developer_id = me())'
MY_PAGE_IDS = \
    'page_id IN (SELECT page_id FROM page_admin WHERE uid = me())'
MY_THREAD_IDS = \
  'thread_id IN (SELECT thread_id FROM thread where folder_id = 0)' # 0 is inbox

# maps table name to WHERE clause used in query for FQL example row(s) for that
# table. a None value means the table isn't currently supported.
#
# these use data based on the access token's user. the --publishable flag
# makes make_schema use PUBLISHABLE_FQL_DATA_WHERE_CLAUSES.
ME_FQL_DATA_WHERE_CLAUSES = {
  'album': 'owner = me()',
  'application': MY_APP_IDS,
  'apprequest': 'app_id = 256884317673197 AND recipient_uid = me()', # bridgy
  'checkin': 'author_uid = me()',
  'comment': 'post_id IN (SELECT post_id FROM stream WHERE source_id = me())',
  'comments_info': MY_APP_IDS,
  'connection': 'source_id = me()',
  'cookies': 'uid = me()',
  'developer': 'developer_id = me()',
  'domain': 'domain_id IN (SELECT domain_id FROM domain_admin WHERE owner_id = me())',
  'domain_admin': 'owner_id = me()',
  'event': 'eid in (SELECT eid FROM event_member WHERE uid = me())',
  'event_member': 'uid = me()',
  'family': 'profile_id = me()',
  'friend': 'uid1 = me()',
  'friend_request': 'uid_to = me()',
  'friendlist': 'owner = me()',
  'friendlist_member': 'flid in (SELECT flid FROM friendlist WHERE owner = me())',
  'group': 'gid IN (SELECT gid FROM group_member WHERE uid = me())',
  'group_member': 'uid = me()',
  'insights': None,  # not supported yet
  'like': 'user_id = me()',
  'link': 'owner = me()',
  'link_stat': 'url IN (SELECT url FROM link WHERE owner = me())',
  'mailbox_folder': '1',  # select all of the user's folders
  'message': MY_THREAD_IDS,
  'note': 'uid = me()',
  'notification': 'recipient_id = me()',
  'object_url': MY_IDS,
  'page': MY_PAGE_IDS,
  'page_admin': MY_UIDS,
  'page_blocked_user': MY_PAGE_IDS,
  'page_fan': 'uid = me()',
  'permissions': None,
  'permissions_info': 'permission_name = "read_stream"',
  'photo': 'aid IN %s' % MY_ALBUM_IDS,
  'photo_tag': 'subject = me()',
  'place': MY_PAGE_IDS,
  'privacy': 'id in %s' % MY_ALBUM_IDS,
  'profile': MY_IDS,
  'review': 'reviewer_id = me()',
  'standard_friend_info': None,  # these need an app access token
  'standard_user_info': None,
  'status': 'uid = me()',
  'stream': 'source_id = me()',
  'stream_filter': 'uid = me()',
  # stream_tag always returns 500s
  # http://bugs.developers.facebook.net/show_bug.cgi?id=20657
  # 'stream_tag': 'actor_id = me()',
  'thread': MY_THREAD_IDS,
  'translation': None,  # not supported yet
  # these need an access token for an app where me() is a developer, which takes
  # more work than getting one from the graph explorer.
  'unified_message': None,
  'unified_thread': None,
  'unified_thread_action': None,
  'unified_thread_count': None,
  'url_like': 'user_id = me()',
  'user': MY_UIDS,
  'video': 'owner = me()',
  'video_tag': 'vid IN (SELECT vid FROM video WHERE owner = me())',
}

# where clauses for data, mostly Ryan's, that's ok to publish with mockfacebook.
PUBLISHABLE_FQL_DATA_WHERE_CLAUSES = {
  'album': 'object_id = 728033318233',         # Profile pictures
  'application': 'app_id IN (256884317673197, 350685531728)',  # bridgy, FB for android
  'apprequest': 'app_id = 256884317673197 AND recipient_uid = 212038',
  'checkin': 'checkin_id = 907227436783',      # AT&T Park, 2011/9/8
  # 9/11 truth and cookies picture, beer week note, privacy post link
  'comment': 'object_id IN ("130490263692746", "341677305872", "252878954730164")',
  'comments_info': 'app_id = "256884317673197"', # bridgy
  'connection': 'source_id = 212038 AND target_id = 173304932707127', # Hearsay Social
  'cookies': None,  # not supported
  'developer': 'developer_id = 212038',        # Ryan
  'domain': 'domain_name = "snarfed.org"',
  'domain_admin': 'owner_id = 212038',
  'event': 'eid = 209798352393506',            # Facebook tech talk
  'event_member': 'eid = 209798352393506 and uid = 1201226147280080',
  'family': 'profile_id = 1506309346',         # Ryan's mom :P
  'friend_request': 'uid_to = 212038 AND uid_from = 78203334',
  'friendlist': 'flid = "563724753913"',
  'friendlist_member': 'flid = "563724753913" AND uid = "1506309346"',
  'friend': 'uid1 = 212038 AND uid2 = 1506309346',
  'group': 'gid = 13243224451',                # the band NIAYH
  'group_member': 'uid = 212038 and gid = 13243224451',
  'insights': None,  # not supported
  'like': 'user_id = 212038 AND object_id = 610146888714', # Giants win!
  'link': 'link_id = 252878954730164',         # privacy post on snarfed.org
  'link_stat': 'url = "http://snarfed.org/"',
  'mailbox_folder': None,
  'message': None,
  'note': 'note_id = 341677305872',            # SF Beer Week post on snarfed.org
  'notification': None,
  'object_url': 'id = 212038',
  'page': 'page_id = 173304932707127',         # Hearsay Social
  'page_admin': 'uid = 212038',
  'page_blocked_user': 'page_id = 256884317673197', # bridgy
  'page_fan': 'uid = 212038',
  'permissions': None,
  'permissions_info': 'permission_name = "read_stream"',
  'photo': 'pid = 910696315249646',            # a rainbow! aww...
  'photo_tag': 'pid = 6469549378760275842',    # Ryan making a face
  'place': 'page_id = 116440731717551',        # AT&T Park
  'privacy': 'id = 514986660443',              # Ryan's profile picture
  'profile': 'username = "snarfed.org"',
  'review': 'reviewee_id = 256884317673197',
  'standard_friend_info': None,
  'standard_user_info': None,
  'status': 'uid = 212038',
   # privacy blog post and AT&T park checkin
  'stream': 'post_id IN ("212038_252878954730164", "212038_907227436783")',
  'stream_filter': 'uid = "212038" and filter_key = "fl_563724753913"',
  'stream_tag': 'target_id = 212038 AND post_id = 813353406219',
  # not supported here...
  'thread': None,
  'translation': None,
  'unified_message': None,
  'unified_thread': None,
  'unified_thread_action': None,
  'unified_thread_count': None,
  'url_like': 'user_id = 212038',
  # Ryan, Chris Babson, Mike Vernal (published the video below)
  'user': 'uid in (212038, 203128, 9074)',
  'video': 'vid = 741181354461',  # facebook developer platform gong
  'video_tag': None,
}

# Object IDs for example Graph API data, mostly Ryan's, that's ok to publish
# with mockfacebook.
PUBLISHABLE_GRAPH_DATA_IDS = [
  '728033318233',           # album
  '256884317673197',        # application
  '907227436783',           # checkin
  '130490263692746_848997', # comment
  '10150150038100285',      # domain
  '209798352393506',        # event
  '563724753913',           # friendlist
  '13243224451',            # group
  '252878954730164',        # link
  '341677305872',           # note
  'hearsaysocial',          # page
  '756014523673',           # photo
  '10101532385094874',      # post
  '869466649703',           # status
  'snarfed.org',            # user
  '741181354461',           # video
]


# names of connections that need special handling.
SPECIAL_CONNECTIONS = (
  'mutualfriends',  # needs either /USER_ID suffix or other user's access token
  'payments',       # http://developers.facebook.com/docs/creditsapi/#getorders
  'subscriptions',  # http://developers.facebook.com/docs/reference/api/realtime/
  # Comment.likes gives the error described here:
  # http://stackoverflow.com/questions/7635627/facebook-graph-api-batch-requests-retrieve-comments-likes-error
  )

# names of connections that shouldn't be published
NON_PUBLISHABLE_CONNECTIONS = (
  'inbox',
  'outbox',
  'updates',
  )

# global optparse.OptionValues that holds flags
options = None


def print_and_flush(str):
  """Prints str to stdout, without a newline, and flushes immediately.
  """
  sys.stdout.write(str)
  sys.stdout.flush()


class Redirected(Exception):
  pass

def urlopen_with_retries(url, data=None):
  """Wrapper for urlopen that automatically retries on HTTP errors.

  If redirect is False and the url is 302 redirected, raises Redirected
  with the destination URL in the exception value.
  """
  for i in range(HTTP_RETRIES + 1):
    try:
      opened = urllib2.urlopen(url, data=data, timeout=HTTP_TIMEOUT_S)
      #   # this isn't a great way to determine if we were redirected - you can
      #   # imagine some failure cases - but it's the simplest. discussion:
      #   # http://stackoverflow.com/questions/110498
      # if not redirect and opened.geturl() != url:
      #   raise Redirected(opened.geturl())
      # else:
        # return opened
      return opened

    except (IOError, urllib2.HTTPError), e:
      logging.debug('retrying due to %s' % e)

  print >> sys.stderr, 'Gave up on %s after %d tries. Last error:' % (
    url, HTTP_RETRIES)
  traceback.print_exc(file=sys.stderr)
  raise e


def make_column(table, column, fb_type, indexable=None):
  """Populates and returns a Column for a schema.

  Args:
    table: string
    column: string
    fb_type: string, type in facebook docs or graph api metadata field
    indexable: boolean, optional

  Returns: Column
  """
  fb_type, sqlite_type = COLUMN_TYPES.get(fb_type.lower(), (None, None))
  if fb_type is None:
    print >> sys.stderr, 'TODO: %s.%s has unknown type %s' % (
      table, column, raw_fb_type)

  return schemautil.Column(name=column,
                           fb_type=fb_type,
                           sqlite_type=sqlite_type,
                           indexable=indexable)

def column_from_metadata_field(table, field):
  """Converts a Graph API metadata field JSON dict to a Column for a schema.

  Args:
    table: string
    field: JSON dict from object['metadata']['field'], where object is a JSON
      object retrieved from the Graph API with ?metadata=true

  Returns: Column
  """
  name = field['name']
  match = GRAPH_DESCRIPTION_TYPE_RE.search(field['description'])
  if match:
    fb_type = match.group(1)
  else:
    print >> sys.stderr, 'Could not determine type of %s.%s from %r.' % (
      table, name, field['description'])
    fb_type = ''

  return make_column(table, name, fb_type)


def scrape_schema(schema, url, column_re):
  """Scrapes a schema from FQL or Graph API docs.

  Args:
    schema: schemautil.Schema to fill in
    url: base docs page URL to start from
    column_re: regexp that matches a column in a table page. Should include
      these named groups: name, fb_type, indexable (optional)
  """
  print_and_flush('Generating %s' % schema.__class__.__name__)

  index_html = urlopen_with_retries(url).read()
  print_and_flush('.')

  links_html = TABLE_LINKS_RE.search(index_html).group()
  for link in TABLE_LINK_RE.findall(links_html):
    table_html = urlopen_with_retries(link).read()
    tables = TABLE_RE.findall(table_html)
    assert len(tables) == 1
    table = tables[0].strip()

    if table in UNSUPPORTED_TABLES:
      continue

    # column_re has three groups: indexable, name, type
    column_data = column_re.findall(table_html)
    column_names = [c[1] for c in column_data]
    override_types = OVERRIDE_COLUMN_TYPES[table]
    override_indexable = OVERRIDE_COLUMN_INDEXABLE[table]
    for name in set(override_types.keys()) | set(override_indexable.keys()):
      if name not in column_names:
        column_data.append(('', name, ''))

    # preserve the column order so it matches the docs
    columns = []
    for indexable, name, fb_type in column_data:
      name = name.lower()
      fb_type = OVERRIDE_COLUMN_TYPES[table].get(name, fb_type)
      indexable = override_indexable.get(name, indexable == '*')
      columns.append(make_column(table, name, fb_type, indexable=indexable))

    schema.tables[table] = tuple(columns)
    print_and_flush('.')

  print
  return schema


def fetch_fql_data(schema):
  """
  Args:
    schema: schemautil.FqlSchema

  Returns:
    schemautil.FqlDataset
  """
  print_and_flush('Generating FQL example data')
  dataset = schemautil.FqlDataset(schema)
  if options.publishable:
    where_clauses = PUBLISHABLE_FQL_DATA_WHERE_CLAUSES
  else:
    where_clauses = ME_FQL_DATA_WHERE_CLAUSES

  # build FQL queries. this dict maps url to (table, query) tuple.
  urls = {}
  for table, columns in sorted(schema.tables.items()):
    if table not in where_clauses:
      print >> sys.stderr, 'TODO: found new FQL table: %s' % table
      continue

    where = where_clauses[table]
    if not where:
      # we don't currently support fetching example data for this table
      continue

    select_columns = ', '.join(c.name for c in columns)
    query = 'SELECT %s FROM %s WHERE %s LIMIT %d' % (
        select_columns, table, where, options.rows_per_table)
    url = 'method/fql.query?%s' % urllib.urlencode(
      {'query': query, 'format': 'json'})
    urls[url] = (table, query)

  # fetch data
  responses = batch_request(urls.keys())

  # store data
  for url, resp in responses.items():
    table, query = urls[url]
    dataset.data[table] = schemautil.Data(table=table, query=query, data=resp)

  print
  return dataset


def fetch_graph_schema_and_data():
  """Returns a (schemautil.GraphSchema, schemautil.GraphDataset) tuple.
  """
  schema = schemautil.GraphSchema()
  dataset = schemautil.GraphDataset(schema)

  print_and_flush('Generating Graph API schema and example data')
  if options.publishable:
    ids = PUBLISHABLE_GRAPH_DATA_IDS
  else:
    ids = ME_GRAPH_DATA_IDS

  # fetch the objects
  objects = batch_request(ids, args={'metadata': 'true'})

  # strip the metadata and generate and store the schema
  connections = []  # list of (name, url) tuples
  for id, object in objects.items():
    metadata = object.pop('metadata')
    table = object['type']

    # columns
    schema.tables[table] = [column_from_metadata_field(table, field)
                            for field in metadata['fields']]
    # connections
    conns = metadata.get('connections')
    if conns:
      schema.connections[table] = conns.keys()
      connections.extend(conns.items())

  # store the objects in the dataset
  dataset.data = dict((id, schemautil.Data(table=table, query=id, data=object))
                      for id, object in objects.items())

  # flatten, filter, and fetch the connections
  def include(conn):
    return not (conn in SPECIAL_CONNECTIONS or
                (options.publishable and name in NON_PUBLISHABLE_CONNECTIONS))

  conn_paths = [urlparse.urlparse(url).path
                for name, url in connections if include(name)]
  conn_paths = list(itertools.chain(conn_paths))  # flatten
  results = batch_request(conn_paths)

  # store the connections in the dataset
  for path, result in results.items():
    path = path.strip('/')
    id, name = path.split('/')
    object = objects[id]
    dataset.connections[path] = schemautil.Connection(
      table=object['type'],
      # id may be an alias, so get the real numeric id
      id=object['id'],
      name=name,
      # strip all but the 'data' key/value
      data={'data': result['data']})

  print_and_flush('.')
  print
  return schema, dataset


# this code works fine, but it's been replaced with batch_request().
# it's still good though. keep it or dump it?
#
# def facebook_query(url=None, args=None, query=None, table=None):
#   """Makes an FQL or Graph API request.

#   Args:
#     url: string
#     args: dict of query parameters
#     query: value for the query field in the returned Data object
#     table: string

#   Returns:
#     schemautil.Data
#   """
#   parts = list(urlparse.urlparse(url))
#   args['access_token'] = options.access_token
#   for arg, vals in urlparse.parse_qs(parts[4]).items():
#     args[arg] = vals[0]
#   parts[4] = urllib.urlencode(args)

#   url = urlparse.urlunparse(parts)
#   result = json.loads(urlopen_with_retries(url).read())
#   assert 'error_code' not in result, 'FQL error:\n%s' % result
#   url = re.sub('access_token=[^&]+', 'access_token=XXX', url)

#   return schemautil.Data(table=table, query=query, url=url, data=result)


def batch_request(urls, args=None):
  """Makes a Graph API batch request.

  https://developers.facebook.com/docs/reference/api/batch/

  Args:
    urls: sequence of string relative url
    args: dict with extra query parameters for each individual request

  Returns: dict mapping string url to decoded JSON object. only includes the
    urls that succeeded.
  """
  print_and_flush('.')

  params = '?%s' % urllib.urlencode(args) if args else ''
  requests = [{'method': 'GET', 'relative_url': url + params} for url in urls]

  # only 50 at a time TODO: constant
  responses = []
  for i in range(0, len(requests), 50):
    data = urllib.urlencode({'access_token': options.access_token,
                             'batch': json.dumps(requests[i:i + 50])})
    response = urlopen_with_retries(options.graph_url, data=data)
    responses.extend(json.loads(response.read()))
    print_and_flush('.')

  assert len(responses) == len(requests)

  results = {}
  for url, resp in zip(urls, responses):
    code = resp['code']
    body = resp['body']
    if code == 200:
      results[url] = json.loads(body)
    elif code == 302:
      headers = dict((h['name'], h['value']) for h in resp['headers'])
      results[url] = {'data': [headers['Location']]}
    else:
      print >> sys.stderr, 'Skipping %s due to %d error:\n%s' % (url, code, body)

  print_and_flush('.')
  return results


def parse_args():
  """Returns optparse.OptionValues with added access_token attr.
  """
  parser = optparse.OptionParser(
    usage='Usage: %prog [options] ACCESS_TOKEN',
    description="""
Generates FQL and Graph API schemas and example data for mockfacebook.'
You can get an access token here (grant it *all* permissions!):
http://developers.facebook.com/tools/explorer?method=GET&path=me""")

  parser.add_option(
    '--fql_docs_url', type='string',
    default='http://developers.facebook.com/docs/reference/fql/',
    help='Base URL for the Facebook FQL reference docs.')
  parser.add_option(
    '--graph_docs_url', type='string',
    default='http://developers.facebook.com/docs/reference/api/',
    help='Base URL for the Facebook Graph API reference docs.')
  parser.add_option(
    '--fql_url', type='string',
    default='https://api.facebook.com/method/fql.query',
    help='Facebook FQL API endpoint URL.')
  parser.add_option(
    '--graph_url', type='string',
    default='https://graph.facebook.com/',
    help='Facebook Graph API endpoint URL.')
  parser.add_option(
    '--rows_per_table', type='int', default=3,
    help='number of example rows to fetch for (most) tables')
  parser.add_option(
    '--publishable', action='store_true', dest='publishable', default=False,
    help='fetch specific publishable data that can go in mockfacebook releases')
  parser.add_option(
    '--no_fql_schema', action='store_false', dest='fql_schema', default=True,
    help="don't generate an FQL schema. Use the existing schema file instead.")
  parser.add_option(
    '--no_fql_data', action='store_false', dest='fql_data', default=True,
    help="don't generate FQL example data.")
  parser.add_option(
    '--no_graph', action='store_false', dest='graph', default=True,
    help="don't generate Graph API schema or data. Use the existing files instead.")

  options, args = parser.parse_args()
  logging.debug('Command line options: %s' % options)

  if len(args) != 1:
    parser.print_help()
    sys.exit(1)

  options.access_token = args[0]
  return options


def main():
  global options
  options = parse_args()

  if options.fql_schema:
    fql_schema = schemautil.FqlSchema()
    scrape_schema(fql_schema, options.fql_docs_url, FQL_COLUMN_RE)
    fql_schema.write()
  else:
    fql_schema = schemautil.FqlSchema.read()

  if options.fql_data:
    dataset = fetch_fql_data(fql_schema)
    dataset.write()

  if options.graph:
    schema, dataset = fetch_graph_schema_and_data()
    schema.write()
    dataset.write()


if __name__ == '__main__':
  main()
