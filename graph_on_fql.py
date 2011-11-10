"""Graph API request handler that uses the FQL data in SQLite.

This is currently on hold. It requires a schema mapping between FQL and the
Graph API, which is labor intensive. This is a good start, but there's a fair
amount of work left to do.

TODO:
- finish schema mapping (all the TODOs inside OBJECT_QUERIES)
- errors
- field selection with ?fields=...
- multiple object selection with ?ids=...
- /picture suffix
- paging
- ?date_format=...
- ?metadata=1 introspection

- handle special cases for which values are omitted when, e.g. null, 0, ''. 0
  is omitted for some things, like page.likes, but not others, like
  group.version. same with '', e.g. group.venue.street. may need another
  override dict in download.py. :/
- time zones in timestamps. (it 's currently hard coded to PST.)
- id aliases, e.g. comment ids can have the user id as a prefix, or not:
  https://graph.facebook.com/212038_227980440569633_3361295
  https://graph.facebook.com/227980440569633_3361295
- connections
- unusual objects: messages, reviews, insights
- comments via .../comments
- likes via .../likes
- batch requests: http://developers.facebook.com/docs/reference/api/batch/
- real time updates: http://developers.facebook.com/docs/reference/api/realtime/
- insights: http://developers.facebook.com/docs/reference/api/insights/
- search via /search?q=...&type=...
- publishing via POST
- deleting via DELETE
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import logging
import json
import sqlite3

import webapp2

import schemautil


# Columns that should always be included, even if they have null/empty/0 value.
OVERRIDE_PINNED_COLUMNS = frozenset(
  ('Group', 'version'),
)

# SQLite queries to fetch and generate Graph API objects. Maps FQL table name
# to SQLite query. (The FQL table name is used when converting values from
# SQLite to JSON.)

# TODO: names with double quotes inside them will break this. ideally i'd use
# quote(u.name) and quote(owner), but that uses single quotes, which JSON
# doesn't support for string literals. :/
USER_TEMPLATE = """ '{"name": "' || %s.name || '", "id": "' || %s.uid || '"}' """
USER_OBJECT = USER_TEMPLATE % ('user', 'user')
APP_OBJECT = """ '{"name": "' || application.display_name || '", "id": "' || application.app_id || '"}' """

OBJECT_QUERIES = {
  'Album': """
SELECT
 CAST(object_id AS TEXT) AS id,
 """ +  USER_OBJECT + """ AS `from`,
 album.name as name,
 description,
 location,
 link,
 CAST(cover_object_id AS TEXT) AS cover_photo,
 visible AS privacy,
 photo_count AS count,
 strftime("%Y-%m-%dT%H:%M:%S+0000", created, "unixepoch") AS created_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", modified, "unixepoch") AS updated_time,
 type
FROM album
  LEFT JOIN user ON (owner = uid)
WHERE object_id = ?;
""",

  'Application': """
SELECT
 CAST(app_id AS TEXT) as id,
 display_name as name,
 description,
 category,
 subcategory,
 "http://www.facebook.com/apps/application.php?id=" || app_id as link,
 icon_url,
 logo_url
FROM application
WHERE app_id = ?;
""",

  'Checkin': """
SELECT
 CAST(checkin_id AS TEXT) as id,
 """ +  USER_OBJECT + """ AS `from`,
 tagged_uids as tags,
 coords as place,
 """ + APP_OBJECT + """ as application,
 strftime("%Y-%m-%dT%H:%M:%S+0000", timestamp, "unixepoch") AS created_time,
-- stream.likes.count, TODO
 checkin.message,
 stream.comments
FROM checkin
  LEFT JOIN application USING (app_id)
  LEFT JOIN stream USING(post_id)
  LEFT JOIN user ON (checkin.author_uid = uid)
WHERE checkin_id = ?;
""",

  'Comment': """
SELECT
 id,
 """ +  USER_OBJECT + """ AS `from`,
 text as message,
 1 as can_remove,
 strftime("%Y-%m-%dT%H:%M:%S+0000", time, "unixepoch") AS created_time,
 likes,
 nullif(user_likes, 0) as user_likes
FROM comment
  LEFT JOIN user ON (fromid = uid)
WHERE id = ?;
""",

  'Domain': """
SELECT
 CAST(domain_id AS TEXT) as id,
 domain_name as name
FROM domain
WHERE domain_id = ?;
""",

  'Event': """
SELECT
 CAST(eid AS TEXT) as id,
 -- TODO test data event is owned by FB Eng page, add that or get new event
 """ +  USER_OBJECT + """ AS owner,
 event.name,
 description,
 -- TODO these should be PST (7h behind) but they're UTC
 strftime("%Y-%m-%dT%H:%M:%S+0000", start_time, "unixepoch") AS start_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", end_time, "unixepoch") AS end_time,
 location,
 venue,  -- TODO id is int but should be string 
 privacy,
 strftime("%Y-%m-%dT%H:%M:%S+0000", update_time, "unixepoch") AS updated_time
FROM event
  LEFT JOIN user ON (creator = uid)
WHERE eid = ?;
""",

  'FriendList': """
SELECT
 CAST(flid AS TEXT) as id,
 name
FROM friendlist
WHERE flid = ?;
""",

  'Group': """
SELECT
 CAST(gid AS TEXT) as id,
 CAST(version AS INTEGER) as version,
 "http://static.ak.fbcdn.net/rsrc.php/v1/y_/r/CbwcMZjMUbR.png" as icon,
 """ +  USER_OBJECT + """ AS owner,
 g.name,
 description,
 g.website as link,
 venue,
 privacy,
 strftime("%Y-%m-%dT%H:%M:%S+0000", update_time, "unixepoch") AS updated_time
FROM `group` g
  LEFT JOIN user ON (creator = uid)
WHERE gid = ?;
""",

  'Link': """
SELECT
 CAST(link_id AS TEXT) as id,
 """ +  USER_OBJECT + """ AS `from`,
 url as link,
 title as name,
 null as comments, -- TODO
 summary as description,
 "http://static.ak.fbcdn.net/rsrc.php/v1/yD/r/aS8ecmYRys0.gif" as icon,
 picture,
 owner_comment as message,
 strftime("%Y-%m-%dT%H:%M:%S+0000", created_time, "unixepoch") AS created_time
FROM link
  LEFT JOIN user ON (owner = uid)
WHERE link_id = ?;
""",

  'Note': """
SELECT
 note_id as id,
 """ +  USER_OBJECT + """ AS `from`,
 title as subject,
 content_html as message,
 null as comments, -- TODO
 strftime("%Y-%m-%dT%H:%M:%S+0000", created_time, "unixepoch") AS created_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", updated_time, "unixepoch") AS updated_time,
 "http://static.ak.fbcdn.net/rsrc.php/v1/yY/r/1gBp2bDGEuh.gif" as icon
FROM note
  LEFT JOIN user USING (uid)
WHERE note_id = ?;
""",

  'Page': """
SELECT
 CAST(page_id AS TEXT) as id,
 name,
 pic as picture,
 page_url as link,
 -- capitalize
 upper(substr(type, 1, 1)) || lower(substr(type, 2)) as category,
 -- if page_url is of the form http://www.facebook.com/[USERNAME], parse
 -- username out of that. otherwise give up and return null.
 nullif(replace(page_url, "http://www.facebook.com/", ""), page_url) as username,
 founded,
 company_overview,
 fan_count as likes,
 parking,
 hours,
 null as payment_options, -- TODO
 null as restaurant_services, -- TODO
 null as restaurant_specialties, -- TODO
 null as general_info, -- TODO
 '{"amex": 0, "cash_only": 0, "visa": 0, "mastercard": 0, "discover": 0}'
   as payment_options, -- TODO
 location,
 null as phone, -- TODO
 null as checkins, -- TODO: use place.checkin_count? but this isn't a place :/
 null as access_token, -- TODO
 1 as can_post -- TODO
FROM page
WHERE page_id = ?;
""",

  'Photo': """
SELECT
 CAST(object_id AS TEXT) as id,
 """ +  USER_OBJECT + """ AS `from`,
 null as tags, -- TODO
 caption as name,
 "http://static.ak.fbcdn.net/rsrc.php/v1/yz/r/StEh3RhPvjk.gif" as icon,
 src as picture,
 src_big as source,
 CAST(src_big_height AS INTEGER) as height,
 CAST(src_big_width AS INTEGER) as width,
 null as images, -- TODO
 link,
 null as comments, -- TODO
 strftime("%Y-%m-%dT%H:%M:%S+0000", created, "unixepoch") AS created_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", modified, "unixepoch") AS updated_time,
 1 as position -- TODO: this isn't in FQL?
FROM photo
  LEFT JOIN user ON (owner = uid)
WHERE object_id = ?;
""",

 'Post': """
SELECT
 post_id AS id,
 """ +  (USER_TEMPLATE % ('from_user', 'from_user')) + """ AS `from`,
 '{"data": [' || """ +  (USER_TEMPLATE % ('to_user', 'to_user')) + """ || ']}' AS `to`,
 message,
 null AS picture, -- TODO parse all of these out of attachment
 null AS link,
 null AS name,
 null AS caption,
 null AS description,
 null AS source,
 null AS properties,
 null AS icon,
 action_links AS actions,
 privacy,
 null AS type, -- TODO parse out of attachment
 likes, -- TODO parse out of attachment and restructure
 null as comments, -- TODO parse comments and restructure (remove can_remove, can_post)
 null AS object_id, -- TODO
 """ + APP_OBJECT + """ AS application,
 strftime("%Y-%m-%dT%H:%M:%S+0000", created_time, "unixepoch") AS created_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", updated_time, "unixepoch") AS updated_time,
 null as targeting
FROM stream
  LEFT JOIN application USING (app_id)
  LEFT JOIN user AS from_user ON (actor_id = from_user.uid)
  LEFT JOIN user AS to_user ON (target_id = to_user.uid)
WHERE post_id = ?;
""",

  'Status': """
SELECT
 CAST(status_id AS TEXT) as id,
 """ +  USER_OBJECT + """ AS `from`,
 message,
 strftime("%Y-%m-%dT%H:%M:%S+0000", time, "unixepoch") AS updated_time
FROM status
  LEFT JOIN user USING (uid)
WHERE status_id = ?;
""",

  'User': """
SELECT
 CAST(uid AS TEXT) AS id,
 name,
 first_name,
 middle_name,
 last_name,
 sex AS gender,
 locale,
 null AS languages,
 profile_url AS link,
 username,
 third_party_id, -- TODO ok as is
   -- should just append ?fields=third_party_id to the User ID in the
   -- download.py publishable graph api ID URLs, but then it doesn't return the
   -- rest of the fields. :/
 CAST(timezone AS INTEGER) AS timezone,
 strftime("%Y-%m-%dT%H:%M:%S+0000", profile_update_time, "unixepoch") AS updated_time,
 verified,
 about_me AS bio,
 birthday_date AS birthday,
 education,
 contact_email AS email,
 hometown_location AS hometown,
 meeting_sex AS interested_in,
 current_location AS location,  -- TODO ok as is
 political,
 null AS favorite_athletes,  -- TODO
 null AS favorite_teams,  -- TODO
 quotes,
 relationship_status,
 null AS religion,  -- TODO
 null AS significant_other, -- significant_other_id
 null AS video_upload_limits,
 website,
 work -- TODO close enough
FROM user
WHERE uid = ?;
""",

  'Video': """
SELECT
 CAST(vid AS TEXT) as id,
 """ +  USER_OBJECT + """ AS `from`,
 null as tags, -- TODO
 title as name,
 description,
 thumbnail_link as picture,
 embed_html,
 "http://static.ak.fbcdn.net/rsrc.php/v1/yD/r/DggDhA4z4tO.gif" as icon,
 src as source,
 strftime("%Y-%m-%dT%H:%M:%S+0000", created_time, "unixepoch") AS created_time,
 strftime("%Y-%m-%dT%H:%M:%S+0000", updated_time, "unixepoch") AS updated_time,
 null as comments -- TODO
FROM video
  LEFT JOIN user ON (owner = uid)
WHERE vid = ?;
""",
}


class OverrideValueFunctions(object):
  """Holds custom processing functions for some field values. Each function
  takes a single parameter, the object id.
  """

  @classmethod
  def get(cls, table, field):
    """Returns the function for the given table and field, or None.
    """
    name = '%s_%s' % (table.lower(), field.lower())
    try:
      return getattr(cls, name)
    except AttributeError:
      return None

  @staticmethod
  def photo_images(id):
    return 'foobax'


class GraphOnFqlHandler(webapp2.RequestHandler):
  """The Graph API request handler.

  Not thread safe!

  Class attributes:
    conn: sqlite3.Connection
    me: integer, the user id that /me should use
    schema: schemautil.GraphSchema
  """

  @classmethod
  def init(cls, conn, me):
    """Args:
      conn: sqlite3.Connection
      me: integer, the user id that /me should use
    """
    cls.conn = conn
    cls.me = me
    cls.schema = schemautil.GraphSchema.read()

  def get(self, id):
    if id == 'me':
      id = self.me

    result = None
    # TODO: parallelize these queries
    for table, query in OBJECT_QUERIES.items():
      cursor = self.conn.execute(query, [id])
      result = self.schema.values_from_sqlite(cursor, table)
      if result:
        break

    if result:
      assert len(result) == 1
      result = result[0]
      for field, val in result.items():
        fn = OverrideValueFunctions.get(table, field)
        if fn:
          result[field] = fn(val)
        # Facebook omits null/empty values entirely in the Graph API
        # TODO: there are some exceptions, e.g. Group.version = 0
        if val in (None, [], 0):
          del result[field]
    else:
      # Facebook reports no results with 'false'.
      # TODO: if the id has non-digits, then it's an "alias," and Facebook says:
      # {"error":
      #   {"message": "(#803) Some of the aliases you requested do not exist: abc",
      #    "type": "OAuthException"}
      # }
      resp = 'false'

    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    self.response.out.write(json.dumps(result))
