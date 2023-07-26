#
# Copyright (c) 2020 Pangeanic SL.
#
# This file is part of NEC TM
# (see https://github.com/shasha79/nectm).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
from flask_restful import Resource, abort, inputs

from flask_restful.reqparse import RequestParser
from Auth import jwt_request_handler
from src.helpers.KeycloakHelper import keycloak
from flask_jwt import JWTError


class AuthResource(Resource):
  """
  @api {get} /token Dummy endpoint, needed to quickly validate token
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Login
  @apiUse Header
  @apiPermission user


  """
  def get(self):
      return {'token': 'valid'}


  # Authentication end-point
  """
   @api {post} /auth Authorize user with a username and a password
   @apiVersion 1.0.0
   @apiName Auth
   @apiGroup Authorization

   @apiParam {String} username
   @apiParam {String} password

   @apiSuccess {String} access_token Authorization token for use it in other endpoints
   @apiError {String} 401 Invalid credentials

   @apiExample {curl} Example usage:
   curl -H "Content-Type: application/json" -XPOST http://127.0.0.1:/api/v1/auth -d
   '{ "username": "user1", "password": "abcxy"}'
  """
  def post(self):
    args = self._reqparse_login()
    id_code = args["id_code"]
    return keycloak.get_token(id_code)

  # Authentication end-point
  """
   @api {patch} /auth Authorize user with a username and a password
   @apiVersion 1.0.0
   @apiName Auth
   @apiGroup Authorization

   @apiParam {String} refresh_token

   @apiSuccess {String} access_token Authorization token for use it in other endpoints
   @apiError {String} 401 Invalid credentials

   @apiExample {curl} Example usage:
   curl -H "Content-Type: application/json" -XPATCH http://127.0.0.1:/api/v1/auth -d
   '{ "refresh_token": "eyJhbGciOiJIUzI1NiI"}'
  """

  def patch(self):
    access_token = jwt_request_handler()
    if not access_token:
        abort(403, mesage="Token missing")
    args = self._reqparse_refresh_token()
    refresh_token = args["refresh_token"]
    return keycloak.refresh_token(refresh_token)

  def _reqparse_login(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument(name='id_code', help="Id Code")

      args =  parser.parse_args()

      return args

  def _reqparse_refresh_token(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument(name='refresh_token', help="Refresh token")
      args =  parser.parse_args()
      return args
