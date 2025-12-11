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

from RestApi.Models import Tags, ContentChecks, CRUD
from Auth import admin_permission, PermissionChecker, UserScopeChecker, view_tag_permission, create_tag_permission, delete_tag_permission, sso_realm_create_tm_permission, edit_tag_permission
from TMPreprocessor.TMRegExpPreprocessor import TMRegExpPreprocessor
from helpers.AuditContext import set_current_auditlog_action
from RestApi.Celery import content_check_task
from JobApi.ESJobApi import ESJobApi


class ContentChecksResource(Resource):
  decorators = [jwt_required()]
  job_api = ESJobApi()

  """
  @api {get} /content_checks/<tag_id> List available content checks or get specific content_check details
  @apiVersion 1.0.0
  @apiName Get
  @apiGroup Content checks
  @apiUse Header
  @apiPermission user

  @apiParam {String} [content_check]
  
  @apiError {String} 404 Content check doesn't exist
  @apiError {String} 403 Insufficient permissions
  
  """
  @PermissionChecker(view_tag_permission)
  def get(self, tag_id=None):
    set_current_auditlog_action('translation-memory.content-checks.show' if tag_id else 'translation-memory.content-checks.index')

    args = self._get_reqparse()
    institution_id = current_identity.institution_id

    tags_subquery = Tags.query.filter_by(institution_id=institution_id).with_entities(Tags.id).subquery('tags')
    content_checks_query = ContentChecks.query \
                                        .filter(ContentChecks.tag_id.in_(tags_subquery)) \
                                        .order_by(ContentChecks.created_at.desc())

    if args.tag_id:
      content_checks_query = content_checks_query.filter(ContentChecks.tag_id.in_([args.tag_id]))

    content_checks = content_checks_query.paginate()

    # List of all tags
    return {
      'meta': {
        'current_page': content_checks.page,
        'last_page': content_checks.pages,
        'per_page': content_checks.per_page,
        'total': content_checks.total,
      },
      'data': [o.to_dict() for o in content_checks.items],
    }

  def _get_reqparse(self):
    parser = RequestParser(bundle_errors=True)
    parser.add_argument(location='args', name='tag_id', help="ID of the tag on which the content check should be performed")

    args = parser.parse_args()

    return args

  """
  @api {post} /content_checks/:id Update content check
  @apiVersion 1.0.0
  @apiName Post
  @apiGroup Content checks
  @apiUse Header
  @apiPermission admin

  @apiParam {String} id

  @apiError {String} 403 Insufficient permissions

  """
  def post(self):
    set_current_auditlog_action('translation-memory.content-checks.create')


    args = self._reqparse()
    institution_id = current_identity.institution_id

    tag_id = args.get('tag_id')
    tag = Tags.query.filter_by(institution_id=institution_id, id=tag_id).one_or_none()

    if not tag:
      abort(404, message="Tag {} doesn't exist".format(tag_id))

    content_check = ContentChecks(
      tag_id=tag.id
    )

    CRUD.add(content_check)

    task = content_check_task.apply_async()
    self.job_api.init_job(job_id=task.id, username=current_identity.id, type='content_check', content_check_id=content_check.id)

    return {
      "message": "Content check {} started successfully".format(content_check.id),
      "data": content_check.to_dict()
    }

  def _reqparse(self):
    parser = RequestParser(bundle_errors=True)
    parser.add_argument(name='tag_id', required=True, help="ID of the tag on which the content check should be performed")

    args = parser.parse_args()

    return args