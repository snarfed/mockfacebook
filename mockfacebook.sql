-- mockfacebook tables for storing OAuth and Graph API data. (The FQL tables are
-- automatically generated into fql_schema.sql by download.py.)

CREATE TABLE IF NOT EXISTS oauth_codes (
  code TEXT NOT NULL PRIMARY KEY,
  client_id TEXT NOT NULL,
  redirect_uri TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_access_tokens (
  token TEXT NOT NULL,
  code TEXT NOT NULL,
  FOREIGN KEY(code) REFERENCES auth_codes(code)
);

CREATE TABLE IF NOT EXISTS graph_objects (
  id TEXT NOT NULL PRIMARY KEY,
  alias TEXT,         -- optional
  data TEXT NOT NULL  -- JSON dict
);

CREATE TABLE IF NOT EXISTS graph_connections (
  id TEXT NOT NULL,
  connection TEXT NOT NULL,
  data TEXT NOT NULL,  -- JSON dict
  UNIQUE(id, connection, data)
);
