#!/usr/bin/python
"""Unit tests for oauth.py.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import httplib
import json
import re
import sqlite3
import threading
import time
import unittest
import urllib
import urlparse

import testutil

import oauth


class OAuthHandlerTest(testutil.HandlerTest):

  def setUp(self):
    super(OAuthHandlerTest, self).setUp(oauth.AuthCodeHandler,
                                        oauth.AccessTokenHandler)
    self.access_token_args = {
      'client_id': '123',
      'client_secret': '456',
      'redirect_uri': 'http://x/y',
      'code': None  # filled in by individual tests
      }

  def expect_oauth_redirect(self, redirect_re='http://x/y\?code=(.+)',
                            args=None):
    """Requests an access code, checks the redirect, and returns the code.
    """
    full_args = {
      'client_id': '123',
      'redirect_uri': 'http://x/y',
      }
    if args:
      full_args.update(args)

    resp = self.get_response('/dialog/oauth', args=full_args)
    self.assertEquals('302 Moved Temporarily', resp.status)
    location = resp.headers['Location']
    match = re.match(redirect_re, location)
    assert match, location
    return urllib.unquote(match.group(1))

  def test_auth_code(self):
    self.expect_oauth_redirect()

  def test_auth_code_with_redirect_uri_with_params(self):
    self.expect_oauth_redirect('http://x/y\?code=(.+)&foo=bar',
                               args={'redirect_uri': 'http://x/y?foo=bar'})

  def test_auth_code_with_state(self):
    self.expect_oauth_redirect('http://x/y\?state=my_state&code=(.+)',
                               args={'state': 'my_state'})

  def test_auth_code_missing_args(self):
    for arg in ('client_id', 'redirect_uri'):
      resp = self.get_response('/dialog/oauth/', args={arg: 'x'})
      self.assertEquals('200 OK', resp.status)
      assert 'An error occurred: missing' in resp.body, resp.body

  def test_access_token(self):
    code = self.expect_oauth_redirect()
    self.access_token_args['code'] = code
    resp = self.get_response('/oauth/access_token', args=self.access_token_args)

    args = urlparse.parse_qs(resp.body)
    self.assertEquals(2, len(args), `args`)
    self.assertEquals('999999', args['expires'][0])
    assert oauth.AccessTokenHandler.is_valid_token(self.conn, args['access_token'][0])

  def test_access_token_nonexistent_auth_code(self):
    self.access_token_args['code'] = 'xyz'
    resp = self.get_response('/oauth/access_token/', args=self.access_token_args)
    assert 'not found' in resp.body

  def test_nonexistent_access_token(self):
    self.assertFalse(oauth.AccessTokenHandler.is_valid_token(self.conn, ''))
    self.assertFalse(oauth.AccessTokenHandler.is_valid_token(self.conn, 'xyz'))

  def test_access_token_missing_args(self):
    for arg in ('client_id', 'client_secret'):
      args = dict(self.access_token_args)
      del args[arg]
      resp = self.get_response('/oauth/access_token', args=args)
      self.assertEquals('400 Bad Request', resp.status)
      assert ('Missing %s parameter.' % arg) in resp.body, (arg, resp.body)

  def test_access_token_different_redirect_uri_or_client_id(self):
    for arg in ('redirect_uri', 'client_id'):
      code = self.expect_oauth_redirect()
      args = dict(self.access_token_args)
      args['code'] = code
      args[arg] = 'different'
      resp = self.get_response('/oauth/access_token', args)
      self.assertEquals('400 Bad Request', resp.status)
      assert ('mismatched %s values' % arg) in resp.body, resp.body

  def test_app_login(self):
    del self.access_token_args['redirect_uri']
    self.access_token_args['grant_type'] = 'client_credentials'
    resp = self.get_response('/oauth/access_token', args=self.access_token_args)
    args = urlparse.parse_qs(resp.body)
    assert oauth.AccessTokenHandler.is_valid_token(self.conn, args['access_token'][0])

  def test_client_side_flow(self):
    token = self.expect_oauth_redirect(
      'http://x/y#access_token=(.+)&expires_in=999999',
      args={'response_type': 'token'})
    assert oauth.AccessTokenHandler.is_valid_token(self.conn, token)


if __name__ == '__main__':
  unittest.main()
