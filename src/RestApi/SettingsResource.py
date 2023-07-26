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

from RestApi.Models import UserSettings, CRUD, current_identity
from Auth import permission
from TMPreprocessor.TMRegExpPreprocessor import TMRegExpPreprocessor

class SettingsResource(Resource):
  regex_pp = TMRegExpPreprocessor()

  """
  @api {get} /settings Get user settings
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Settings
  @apiUse Header
  @apiPermission user
  """
  @permission()
  def get(self):
    user_settings = UserSettings.query.filter_by(user_uuid=current_identity()['id']).all()
    if not user_settings:
        abort(404, mesage="User settings doesn't exist")

    result = []
    for setting in user_settings:
      result.append(setting.to_dict())
    return result


  """
  @api {put} /settings Update user settings
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Settings
  @apiUse Header
  @apiPermission user
  """
  @permission()
  def put(self):
    args = self._put_reqparse()
    settings = UserSettings.query.filter_by(user_uuid=current_identity()['id']).first()

    if not settings:
      settings = UserSettings()
      CRUD.add(settings)
    if args.regex and args.regex.lower() == 'none':
      settings.regex = ''
    else:
      settings.regex = args.regex
      if not self.regex_pp.validate_pipe(settings.regex.split(',')):
        abort(400, mesage="Invalid regular expression(s). Possible values (joined with comman) are: {} ".format(settings.regex))

    CRUD.update()

    return settings.to_dict()

  def _put_reqparse(self):
      parser = RequestParser(bundle_errors=True)
      parser.add_argument(name='regex', help="List (separated with comma) of regular expression names to apply", required=True)

      return parser.parse_args()
