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

import re
from flask_restful import Resource, abort
from flask_restful.reqparse import RequestParser

from AuditLogClient import send_audit_log, AuditLogMessage
from lib.flask_jwt import current_identity, jwt_required

from RestApi.Models import Tags, CRUD
from Auth import admin_permission, PermissionChecker, UserScopeChecker, view_tag_permission, create_tag_permission, delete_tag_permission, sso_realm_create_tm_permission, edit_tag_permission
from TMPreprocessor.TMRegExpPreprocessor import TMRegExpPreprocessor
from helpers.AuditContext import set_current_auditlog_action

class TagsResource(Resource):
  decorators = [jwt_required()]
  regex_pp = TMRegExpPreprocessor()

  """
  @api {get} /tags/<tag_id> List available tags or get specific tag details
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Tags
  @apiUse Header
  @apiPermission user

  @apiParam {String} [tag]
  
  @apiError {String} 404 Tag doesn't exist
  @apiError {String} 403 Insufficient permissions
  
  """
  @PermissionChecker(view_tag_permission)
  def get(self, tag_id=None):
    set_current_auditlog_action('translation-memory.tags.show' if tag_id else 'translation-memory.tags.index')

    args = self._get_reqparse()

    tags = []
    if tag_id:
      tag = Tags.query.get(tag_id)
      if tag:
        tags = [tag.to_dict()]
      else:
        abort(404, message="Tag {} doesn't exist".format(tag_id))
    else:
        tags = [tag.to_dict() for tag in Tags.query.all()]

    # Filter scopes according to permissions
    tags = UserScopeChecker.filter_domains(tags, key_fn=lambda t: t["id"])

    name_filter = args.get('name')
    if name_filter:
      tags = filter(lambda t: str(name_filter).lower() in str(t['name']).lower(), tags)

    id_filter = args.get('id')
    if id_filter:
      tags = filter(lambda t: str(t['id']) in id_filter, tags)

    type_filter = args.get('type')
    if type_filter:
      tags = filter(lambda t: t['type'] in type_filter, tags)

    tv_domain_filter = args.get('tv_domain')
    if tv_domain_filter:
      tags = filter(lambda t: t['tv_domain'] in tv_domain_filter, tags)

    tv_tags_filter = args.get('tv_tags')
    if tv_tags_filter:
      tags = filter(lambda t: set(tv_tags_filter) & set(t['tv_tags'] or []), tags)

    lang_pair_filter = args.get('lang_pair')
    if lang_pair_filter:
      tags = filter(lambda t: t['lang_pair'] in lang_pair_filter, tags)

    institution_id_filter = args.get('institution_id')
    if institution_id_filter:
      tags = filter(lambda t: str(t['institution_id']) == institution_id_filter, tags)

    if tag_id:
      if not tags:
        abort(404, message="Tag {} doesn't exist".format(tag_id))
      return tags[0]
    # List of all tags
    return {
      'tags': list(tags)
    }

  def _get_reqparse(self):
    parser = RequestParser(bundle_errors=True)
    parser.add_argument(location='args', name='name', help="Tag's name")
    parser.add_argument(location='args', name='id', action='append', help="Tag's id")
    parser.add_argument(location='args', name='type', action='append', help="Tag's type")
    parser.add_argument(location='args', name='tv_domain', action='append', help="Tõlkevärav specific domain")
    parser.add_argument(location='args', name='tv_tags', action='append', help="Tõlkevärav specific tags")
    parser.add_argument(location='args', name='institution_id', help="Tag's Tõlkevärav specific institution id")
    parser.add_argument(location='args', name='lang_pair', action='append',
                        help="Language pair to parse from TMX. \ "
                             "Pair is a string of 2-letter language codes joined with underscore")
    args = parser.parse_args()

    lang_pairs = args.get('lang_pair')
    if lang_pairs is not None:
      for lang_pair in lang_pairs:
        if not re.match('^[a-zA-Z]{2,3}_[a-zA-Z]{2,3}$', lang_pair):
          abort(400, mesage="Language pair format is incorrect: {} The correct format example : en_es".format(lang_pair))

    return args

  """
  @api {post} /tags/:id Update tag
  @apiVersion 1.0.0
  @apiName Post
  @apiGroup Tags
  @apiUse Header
  @apiPermission admin

  @apiParam {String} id
  @apiParam {String} name
  @apiParam {String} type

  @apiError {String} 403 Insufficient permissions

  """
  def post(self, tag_id=None):
    args = self._reqparse(tag_id)
    set_current_auditlog_action('translation-memory.tags.create')

    if tag_id:
      edit_tag_permission.test(http_exception=403)
      tag = Tags.query.get(tag_id)
      tag_object_identity_subset = tag.get_audit_log_identity_subset()
      tag_pre_modification_subset = tag.to_audit_log_representation()
      tags = UserScopeChecker.filter_domains([tag], key_fn=lambda t: t["id"])
      tag = tags[0] if tags else None

      if not tag:
        abort(404, message="Tag {} doesn't exist".format(tag_id))

      tag.update(**args)
      CRUD.update()

      tag_post_modification_subset = tag.to_audit_log_representation()
      send_audit_log(AuditLogMessage(
        event_type='MODIFY_OBJECT',
        event_parameters={
          'object_type': Tags.AUDIT_LOG_OBJECT_TYPE,
          'object_identity_subset': tag_object_identity_subset,
          'pre_modification_subset': tag_pre_modification_subset,
          'post_modification_subset': tag_post_modification_subset,
        }))
    else:
      create_tag_permission.test(http_exception=403)
      institution_id = current_identity.institution_id

      if current_identity.can(sso_realm_create_tm_permission) and args.institution_id:
        institution_id = args.pop('institution_id')

      tag = Tags(**args, institution_id=institution_id)
      CRUD.add(tag)

      send_audit_log(AuditLogMessage(
        event_type='CREATE_OBJECT',
        event_parameters={
          'object_type': Tags.AUDIT_LOG_OBJECT_TYPE,
          'object_data': tag.to_audit_log_representation(),
          'object_identity_subset': tag.get_audit_log_identity_subset()
        }))


    return {
      "message": "Tag {} added/updated successfully".format(tag.id),
      "tag": tag.to_dict()
    }

  def _reqparse(self, tag_id):
      creation = not tag_id

      parser = RequestParser(bundle_errors=True)
      parser.add_argument(required=creation, name='name', help="Tag's name")
      parser.add_argument(required=creation, name='type', help="Tag's type")
      parser.add_argument(required=creation, name='tv_domain', help="Tag's Tõlkevärav specific domain")
      parser.add_argument(name='comment', help="Tag's comment")
      parser.add_argument(name='tv_tags', action='append', help="Tag's Tõlkevärav specific tags")


      if creation:
        parser.add_argument(required=creation, name='lang_pair',
                            help="Language pair to parse from TMX. \ "
                                 "Pair is a string of 2-letter language codes joined with underscore")
        if current_identity.can(sso_realm_create_tm_permission):
          parser.add_argument(required=creation, name='institution_id', help="Tag's Tõlkevärav specific institution id")

      args = parser.parse_args()

      name_length_limit = 150
      if len(args.name) > name_length_limit:
        abort(400, message="Name can't be longer than {} characters".format(name_length_limit))

      if 'lang_pair' in args and not re.match('^[a-zA-Z]{2,3}_[a-zA-Z]{2,3}$', args.lang_pair):
        abort(400, message="Language pair format is incorrect: {} The correct format example : en_es".format(args.lang_pair))

      return args


  """
  @api {delete} /tags/:id Delete tag
  @apiVersion 1.0.0
  @apiName Delete
  @apiGroup Tags
  @apiUse Header
  @apiPermission admin

  @apiParam {String} tag

  @apiError {String} 403 Insufficient permissions
  @apiError {String} 404 Tag doesn't exist

  """
  @PermissionChecker(delete_tag_permission)
  def delete(self, tag_id):
    set_current_auditlog_action('translation-memory.tags.destroy')
    tag = Tags.query.get(tag_id)

    tags = UserScopeChecker.filter_domains([tag], key_fn=lambda t: t["id"])
    tag = tags[0] if tags else None

    if tag:
      try:
        CRUD.delete(tag)
      except Exception as e:
        abort(500, message=str(e))
    else:
      abort(404, message="Tag {} doesn't exist".format(tag_id))


    send_audit_log(AuditLogMessage(
      event_type='REMOVE_OBJECT',
      event_parameters={
        'object_type': Tags.AUDIT_LOG_OBJECT_TYPE,
        'object_identity_subset': tag.get_audit_log_identity_subset()
      }))

    return {
      "message": "Tag {} deleted successfully".format(tag_id),
      "tag": tag.to_dict()
    }
