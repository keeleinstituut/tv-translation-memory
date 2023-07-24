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


from RestApi.Models import app, Users, CRUD
from Auth import permission, \
  current_identity_roles, current_username, current_userid, jwt_request_handler, access_token
from helpers.KeycloakHelper import keycloak


class UsersResource(Resource):
  """
   @apiDefine UserParams
   @apiParam {String} password User password
   @apiParam {String} role User role: admin or user
  """
  """
  @api {get} /users/<username> Get user details. If no user specified, all users' details are returned
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Users
  @apiUse Header
  @apiPermission admin

  @apiParam {String} [username]

  @apiError {String} 404 User doesn't exist

  """
  @permission("user")
  def get(self, username=None):
    # Non-admin can query only themselves
    if "admin" in current_identity_roles():
        return keycloak.get_user_info(username=username)
    else:
        username = current_username() # force to get only current user
        if username and username != current_username():
            abort(403, mesage="Permission denied")

    return keycloak.get_user_info(username=username)

  """
  @api {post} /users/<username> Add/update user details
  @apiVersion 1.0.0
  @apiName AddUpdate
  @apiGroup Users
  @apiUse Header
  @apiPermission admin

  @apiParam {String} username
  @apiUse UserParams

  @apiError {String} 403 Insufficient permissions

  """
  @permission("admin")
  def post(self):
    args = self._reqparse()
    keycloak.add_user(args)
    keycloak_user_by_username = keycloak.get_user_info(username=args['username'])
    if not len(keycloak_user_by_username) > 0:
        abort(500, message="Error creating user")
    user = Users.query.get(keycloak_user_by_username[0]['id'])
    try:
      if user:
        keycloak.edit_user(keycloak_user_by_username[0]['id'], args)
        user.update(**args)
        CRUD.update()
      else:
        user = Users(keycloak_user_by_username[0]['id'], **args)
        CRUD.add(user)
    except Exception as e:
      abort(500, message=str(e))
    return keycloak_user_by_username[0]

  """
    @api {delete} /users/<username> Delete user
    @apiVersion 1.0.0
    @apiName Delete
    @apiGroup Users
    @apiUse Header
    @apiPermission admin

    @apiParam {String} username
    @apiUse UserParams

    @apiError {String} 403 Insufficient permissions
    @apiError {String} 404 User doesn't exist

  """
  @permission("admin")
  def delete(self, username):
    if username == Users.ADMIN:
      abort(403, message="You can't delete {} user".format(Users.ADMIN))

    keycloak_user = keycloak.get_user_info(username=username)
    user = Users.query.get(keycloak_user[0]['id'])
    if user:
        try:
            user.delete_scopes()  # First, delete all user scopes
            CRUD.delete(user)
        except Exception as e:
            abort(500, message=str(e))
    else:
        abort(404, mesage="User {} doesn't exist".format(username))

    return keycloak.delete_user(keycloak_user[0]['id'])

  def _reqparse(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument('email', type=str, required=True, help='Email address')
      parser.add_argument('username', type=str, required=True, help='Username')
      parser.add_argument('firstName', type=str, required=True, help='First name')
      parser.add_argument('lastName', type=str, required=True, help='Last name')
      parser.add_argument('credentials', type=dict, required=True, action="append", help='Credentials')
      parser.add_argument('enabled', type=bool, required=True, help='Enabled')
      parser.add_argument('emailVerified', type=bool, required=True, help='Email verified')
      args =  parser.parse_args()

      return args


class UserScopesResource(Resource):
  """
   @apiDefine UserParams
   @apiParam {String} password User password
   @apiParam {String} role User role: admin or user
  """
  """
  @api {get} /users/<username>/scopes Get user scopes
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Users
  @apiUse Header
  @apiPermission admin

  @apiParam {String} username

  @apiError {String} 404 User doesn't exist

  """
  @permission("admin")
  def get(self, username):
    user = Users.query.filter_by(username=username).first()
    if user:
      return {'user_scopes': [scope.to_dict() for scope in user.scopes]}
    else:
      abort(404, mesage="User {} doesn't exist".format(username))

  """
  @api {post} /users/<username>/scopes Add/update user scope
  @apiVersion 1.0.0
  @apiName AddUpdate
  @apiGroup UserScopes
  @apiUse Header
  @apiPermission admin

  @apiParam {String} username
  @apiParam {Integer} [id] Scope id
  @apiParam {String} [lang_pairs] List (separated with comma) of allowed language pairs to query, ex.: en_es,es_en,es_fr. By default, allows all pairs
  @apiParam {String} [tags] List (separated with comma) of allowed tags to query, ex.: Health,Insurance. By default, allows all tags
  @apiParam {Boolean} [can_update] Allow/forbid update TM in the given scope. Default is false.
  @apiParam {Boolean} [can_import] Allow/forbid import of TM in the given scope. Default is false.
  @apiParam {Boolean} [can_export] Allow/forbid export of TM in the given scope. Default is false.
  @apiParam {Integer} [usage_limit] Limit allowed usage (queries number). Default: no limit

  @apiParam {Date} [start_date] Scope starts at that date. Default - not limited
  @apiParam {Date} [end_date] Scope ends at that date. Default - not limited

  @apiError {String} 403 Insufficient permissions
  @apiError {String} 404 User doesn't exist

  """
  @permission("admin")
  def post(self, username):
    args = self._post_reqparse()
    user = Users.query.filter_by(username=username).first()

    try:
      if user:
        scope = user.update_scope(**args)
        if not scope:
          abort(404, mesage="User {} - scope doesn't exist".format(username))
        import logging
        logging.info("Adding/updating scope: {}".format(scope))
        CRUD.add(scope)
      else:
        abort(404, mesage="User {} doesn't exist".format(username))
    except Exception as e:
      abort(500, message=str(e))
    return {"message" : "User {} - scope added/updated successfully".format(username)}

  """
    @api {delete} /users/<username>/scope Delete scope
    @apiVersion 1.0.0
    @apiName Delete
    @apiGroup UserScopes
    @apiUse Header
    @apiPermission admin

    @apiParam {String} username
    @apiParam {Integer} id Scope id

    @apiError {String} 403 Insufficient permissions
    @apiError {String} 404 User doesn't exist

  """
  @permission("admin")
  def delete(self, username):
    args = self._delete_reqparse()

    user = Users.query.filter_by(username=username).first()
    if user:
      try:
        scope = user.get_scope(**args)
        if scope:
          CRUD.delete(scope)
      except Exception as e:
        abort(500, message=str(e))
    else:
      abort(404, mesage="User {} doesn't exist".format(username))
    return {"message" : "User {} - scope deleted successfully".format(username)}


  def _post_reqparse(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument(name='id',help="Scope id")
      parser.add_argument(name='lang_pairs', help="List (separated with comma) of allowed language pairs to query, ex.: en_es,es_en,es_fr")
      parser.add_argument(name='tags', help="List (separated with comma) of allowed tags to query, ex.: Health,Insurance")
      parser.add_argument(name='can_update', type=inputs.boolean, help="Allow/forbid update TM in the given scope")
      parser.add_argument(name='can_import', type=inputs.boolean, help="Allow/forbid import of TM in the given scope")
      parser.add_argument(name='can_export', type=inputs.boolean, help="Allow/forbid export of TM in the given scope")
      parser.add_argument(name='usage_limit', type=int, help="Limit allowed usage (queries number) for this scope")

      parser.add_argument(name='start_date', help="Scope starts at that date")
      parser.add_argument(name='end_date', help="Scope ends at that date")

      return parser.parse_args()

  def _delete_reqparse(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument(name='id', required=True, help="Scope id")
      return parser.parse_args()
