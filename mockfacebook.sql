-- mockfacebook tables for storing OAuth and Graph API data. (The FQL tables are
-- automatically generated into fql_schema.sql by make_schema.py.)

CREATE TABLE oauth_codes (
  code TEXT NOT NULL PRIMARY KEY,
  client_id TEXT NOT NULL,
  redirect_uri TEXT NOT NULL
);

CREATE TABLE oauth_access_tokens (
  token TEXT NOT NULL,
  code TEXT NOT NULL,
  FOREIGN KEY(code) REFERENCES auth_codes(code)
);

CREATE TABLE graph_objects (
  id TEXT NOT NULL PRIMARY KEY,
  alias TEXT,         -- optional
  data TEXT NOT NULL  -- JSON dict
);

CREATE TABLE graph_connections (
  id TEXT NOT NULL,
  connection TEXT NOT NULL,
  data TEXT NOT NULL  -- JSON dict
);
