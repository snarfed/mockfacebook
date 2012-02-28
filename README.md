mockfacebook is a standalone HTTP server that implements Facebook's FQL and Graph API. It's useful for unit and integration testing and limited manual testing.

It includes a download utility that seeds its database with data and schemas from Facebook, which helps it keep up with Facebook API changes. You can also add your own data manually or programmatically.

mockfacebook is backed by SQLite. It's single threaded, so it's not suitable for load testing, high throughput, or performance.

## Features

The [Graph API](http://developers.facebook.com/docs/reference/api/) is served
at the `/...` endpoint. It supports:

* read access to all object types except `Insights`, `Permissions`, and `Subscription`
* aliases as well as ids
* read access to all connection types except `insights`, `mutualfriends`, `payments`, `subscriptions`, and `Comment/likes`
* multiple selection via `?ids=...`
* checks access token if provided
* most error codes and messages

[FQL](http://developers.facebook.com/docs/reference/fql/) is served at the
`/method/fql.query` and `/fql` endpoints. It supports:

* full FQL syntax, including subselects
* read access to all tables except `insights` and `permissions`
* indexable columns. returns an error if a non-indexable column is used in a `WHERE` clause.
* all functions: `me(), now(), strlen(), substr(), strpos()`
* checks access token if provided
* JSON and XML output formats
* most error codes and messages

Right now, the FQL and Graph API use _separate_ data. There's progress toward unifying them, but it's incomplete and would be labor intensive to maintain. Still, feel free to [pitch in](#Contributing)!

[OAuth authentication](http://developers.facebook.com/docs/authentication/) is served at the `/dialog/oauth` and `/oauth/access_token` endpoints. It supports:

* auth codes
* access tokens
* server and client side flows
* app login

See the [issue tracker](https://github.com/rogerhu/mockfacebook/issues) for a list of other features that may eventually be supported.


## Download and setup

No packages or tarballs, just git clone from head!

```
git clone https://github.com/rogerhu/mockfacebook
```

mockfacebook depends on [webapp2](http://webapp-improved.appspot.com/), which comes bundled as a git submodule:

```
git submodule init
git submodule update
```

webapp2 also depends on [WebOb](http://www.webob.org/):

```
pip install webob  # or sudo apt-get install python-webob
```

and [sqlparse](http://code.google.com/p/python-sqlparse/):

```
# in the mockfacebook dir:
wget http://python-sqlparse.googlecode.com/files/sqlparse-0.1.3.tar.gz
tar xzf sqlparse-0.1.3.tar.gz
ln -s sqlparse-0.1.3/sqlparse sqlparse
```


## Using

First, you'll need data. The easiest way to get some is the `download.py` script, which downloads your own data and some public data.

You'll need an access token, which you can get from the [Graph API Explorer](http://developers.facebook.com/tools/explorer). Click on the Get Access Token button and select all of the permissions under each tab, especially `offline_access` under Extended Permissions.

Now, run `download.py ACCESS_TOKEN`. By default, it only downloads a small amount of data. You can use flags like `--num_per_type`, `--crawl_friends`, and `--graph_ids` to get more.

You can also add data to the SQLite database directly. See [mockfacebook.sql](https://github.com/rogerhu/mockfacebook/blob/master/mockfacebook.sql) and [fql_schema.sql](https://github.com/rogerhu/mockfacebook/blob/master/fql_schema.sql) for the table definitions and, if you've run `download.py`, `graph_data.sql` and `fql_data.sql` for examples. For example:

```
sqlite3 mockfacebook.db
...
sqlite> INSERT INTO graph_objects(id, alias, data) VALUES(
  '123',
  'fake_user',
  '{"id": "123", "username": "fake_user", "first_name": "John", "last_name": "Doe", ...}');
```

(You'll need to run `download.py` or `server.py` first to create the database file.)

Once you have some data, just run `server.py`, point your Facebook app at `http://localhost:8000/`, and start testing!

NOTE: You can supply a `--me` option, e.g. `server.py --me=12345` to designate which id resolves to `/me`. More work will be done to expand to support multiple page_tokens to correlate this information automatically.

## Contributing

Interested in adding features or fixing bugs? Check out the [issue tracker](https://github.com/rogerhu/mockfacebook/issues) for some ideas.

The code base has two top-level applications. `download.py` downloads FQL and Graph API schemas and data from Facebook. It uses `schemautil.py`, which defines `*Schema` and `*Dataset` DAO classes. The `*Dataset` classes are only used in the unit tests; the server itself queries the SQLite database directly. Schemas and data are written to `*_{data,schema}.{py,sql}` and the SQLite db file, `mockfacebook.db` by default.

`server.py` serves the data stored in the SQLite db. `graph.py`, `fql.py`, and `oauth.py` are the individual HTTP request handlers served by `server.py`. `oauth.py` provides access token checking for the other two, but otherwise they're independent.

`download.py` and `server.py` both create the SQLite db, if necessary, and populate it with the OAuth and Graph API tables in `mockfacebook.sql` and the FQL tables in `fql_schema.sql`.

The server and handlers have unit tests in `*_test.py`. You can run them individually or with `alltests.py`. Please make sure all tests pass before sending patches!

`graph_on_fql.py` is an incomplete, experimental schema mapping from FQL to Graph API. It serves a Graph API endpoint using the data in the FQL tables. Much of the heavy lifting has already been done, but a fair amount of detail work remains, and it would be labor intensive to maintain, so it's not currently connected. Feel free to check it out though!
