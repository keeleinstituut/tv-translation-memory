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


from RestApi.Models import app, CRUD, current_identity_roles, current_userid, current_username
from Auth import permission
from src.RestApi.Models import UserScopes, current_identity


class UsersResource(Resource):
  """
   @apiDefine UserParams
   @apiParam {String} password User password
   @apiParam {String} role User role: admin or user
  """
  """
  @api {get} /users Get user details. If no user specified, all users' details are returned
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Users
  @apiUse Header
  @apiPermission admin

  @apiError {String} 404 User doesn't exist

  """
  @permission()
  def get(self):
    # Non-admin can query only themselves
    return current_identity()

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
  @api {get} /users/scopes Get user scopes
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Users
  @apiUse Header
  @apiPermission admin

  @apiError {String} 404 User doesn't exist

  """
  @permission()
  def get(self):
    user_scopes = UserScopes()
    user_scopes_list = user_scopes.get_scope_by_user_id()
    result = []
    for scope in user_scopes_list:
      result.append(scope.to_dict())
    if result:
        return {'user_scopes': result}
    else:
      abort(404, mesage="User Scopes doesn't exist")

  """
  @api {post} /users/scopes Add/update user scope
  @apiVersion 1.0.0
  @apiName AddUpdate
  @apiGroup UserScopes
  @apiUse Header
  @apiPermission admin

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
  @permission()
  def post(self):
    args = self._post_reqparse()
    user_scopes = UserScopes()
    try:
      scope = user_scopes.update_scope(**args)
      if not scope:
        abort(404, mesage="User scope doesn't exist")
      import logging
      logging.info("Adding/updating scope: {}".format(scope))
      CRUD.add(scope)
    except Exception as e:
      abort(500, message=str(e))
    return {"message" : "User scope added/updated successfully"}

  """
    @api {delete} /users/scope Delete scope
    @apiVersion 1.0.0
    @apiName Delete
    @apiGroup UserScopes
    @apiUse Header
    @apiPermission admin

    @apiParam {Integer} id Scope id

    @apiError {String} 403 Insufficient permissions
    @apiError {String} 404 User doesn't exist

  """
  @permission()
  def delete(self):
    args = self._delete_reqparse()
    user_scopes = UserScopes()
    try:
      scope = user_scopes.get_scope(**args)
      if scope:
        CRUD.delete(scope)
    except Exception as e:
      abort(500, message=str(e))
    return {"message" : "User scope deleted successfully"}


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
