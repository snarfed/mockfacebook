"""The OAuth request handler.

Based on http://developers.facebook.com/docs/authentication/ .
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import base64
import logging
import os
import urllib
import urlparse

from webob import exc
import webapp2


AUTH_CODE_PATH = '/dialog/oauth'
ACCESS_TOKEN_PATH = '/oauth/access_token'
EXPIRES = '999999'
RANDOM_BYTES = 16

ERROR_TEXT = """
mockfacebook

Error

An error occurred: %s. Please try again later. (In the real Facebook, this is
nicely formatted HTML.)
"""

ERROR_JSON = '{"error":{"type":"OAuthException","message":"%s."}}'


class BaseHandler(webapp2.RequestHandler):
  """Base handler class for OAuth handlers.

  Attributes:
    conn: sqlite3.Connection
  """

  @classmethod
  def init(cls, conn, me=None):
    # me is unused
    cls.conn = conn

  def get_required_args(self, *args):
    """Checks that one or more args are in the query args.

    If any are not in args or are empty, raises an AssertionError with the
    argument name as its associated value.

    Args:
      args: tuple of strings

    Returns: list of strings
    """
    values = [self.request.get(arg) for arg in args]
    for arg, val in zip(args, values):
      assert val, arg
    return values

  def create_auth_code(self, client_id, redirect_uri):
    """Generates, stores, and returns an auth code using the given parameters.

    Args:
      client_id: string
      redirect_uri: string

    Returns: string auth code
    """
    code = base64.urlsafe_b64encode(os.urandom(RANDOM_BYTES))
    self.conn.execute(
      'INSERT INTO oauth_codes(code, client_id, redirect_uri) VALUES(?, ?, ?)',
      (code, client_id, redirect_uri))
    self.conn.commit()
    return code

  def create_access_token(self, code, client_id, redirect_uri):
    """Generates, stores, and returns an access token using the given parameters.

    Args:
      code: string auth code
      client_id: string
      redirect_uri: string

    Returns: string auth code
    """
    cursor = self.conn.execute(
      'SELECT client_id, redirect_uri FROM oauth_codes WHERE code = ?', (code,))
    row = cursor.fetchone()
    assert row, ERROR_JSON % (
      'Error validating verification code: auth code %s not found' % code)
    code_client_id, code_redirect = row

    for code_arg, arg, name in ((code_client_id, client_id, 'client_id'),
                                (code_redirect, redirect_uri, 'redirect_uri')):
      assert code_arg == arg, ERROR_JSON % (
        'mismatched %s values: %s received %s, %s received %s' %
        (name, AUTH_CODE_PATH, code_arg, ACCESS_TOKEN_PATH, arg))

    token = base64.urlsafe_b64encode(os.urandom(RANDOM_BYTES))
    self.conn.execute('INSERT INTO oauth_access_tokens(code, token) VALUES(?, ?)',
                      (code, token))
    self.conn.commit()

    return token


class AuthCodeHandler(BaseHandler):
  """The auth code request handler.
  """

  ROUTES = [(r'/dialog/oauth/?', 'oauth.AuthCodeHandler')]

  def get(self):
    state = self.request.get('state')
    response_type = self.request.get('response_type')
    try:
      client_id, redirect_uri = self.get_required_args('client_id',
                                                       'redirect_uri')
    except AssertionError, e:
      self.response.out.write(ERROR_TEXT % 'missing %s' % unicode(e))
      return

    code = self.create_auth_code(client_id, redirect_uri)

    redirect_parts = list(urlparse.urlparse(redirect_uri))
    if response_type == 'token':
      # client side flow. get an access token and put it in the fragment of the
      # redirect URI. (also uses expires_in, not expires.) background:
      # http://developers.facebook.com/docs/authentication/#client-side-flow
      token = self.create_access_token(code, client_id, redirect_uri)
      if redirect_parts[5]:
        logging.warning('dropping original redirect URI fragment: %s' %
                        redirect_parts[5])
      redirect_parts[5] = urllib.urlencode(
        {'access_token': token, 'expires_in': EXPIRES})
    else:
      # server side flow. just put the auth code in the query args of the
      # redirect URI. background:
      # http://developers.facebook.com/docs/authentication/#server-side-flow
      #
      # dict(parse_qsl()) here instead of just parse_qs() so that the dict
      # values are individual elements, not lists.
      redirect_args = dict(urlparse.parse_qsl(redirect_parts[4]))
      redirect_args['code'] = code
      if state:
        redirect_args['state'] = state
      redirect_parts[4] = urllib.urlencode(redirect_args)

    self.redirect(urlparse.urlunparse(redirect_parts))


class AccessTokenHandler(BaseHandler):
  """The access token request handler.
  """

  ROUTES = [(r'/oauth/access_token/?', 'oauth.AccessTokenHandler')]

  def is_valid_token(self, access_token):
    """Returns True if the given access token is valid, False otherwise."""
    cursor = self.conn.execute('SELECT token FROM oauth_access_tokens WHERE token = ?',
                               (access_token,))
    return cursor.fetchone() is not None

  def get(self):
    """Handles a /oauth/access_token request to allocate an access token.

    Writes the response directly.
    """
    try:
      grant_type = self.request.get('grant_type')
      redirect_uri = self.request.get('redirect_uri')
      try:
        client_id, _, code = self.get_required_args('client_id', 'client_secret',
                                                    'code')
      except AssertionError, e:
        assert False, ERROR_JSON % 'Missing %s parameter' % unicode(e)
  
      # app login. background:
      # http://developers.facebook.com/docs/authentication/#applogin
      if grant_type == 'client_credentials':
        redirect_uri = ''
        code = self.create_auth_code(client_id, redirect_uri)
  
      token = self.create_access_token(code, client_id, redirect_uri)
  
      self.response.charset = 'utf-8'
      self.response.out.write(
          urllib.urlencode({'access_token': token, 'expires': EXPIRES}))
    except AssertionError, e:
      raise exc.HTTPClientError(unicode(e).encode('utf8'))
