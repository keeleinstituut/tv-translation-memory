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
from flask_restful import Resource, abort
from flask_restful.reqparse import RequestParser
from lib.flask_jwt import current_identity, jwt_required

from Auth import admin_permission
from RestApi.Celery import job_kill_task
from JobApi.ESJobApi import ESJobApi
from RestApi.Auth import ADMIN, PermissionChecker
from helpers.AuditContext import set_current_auditlog_action


class JobsResource(Resource):
  decorators = [jwt_required()]

  def __init__(self):
    self.job_api = ESJobApi()

  """
   @api {get} /jobs/id Query job details (start time, status, end time etc.). If no job id specified, all jobs are returned
   @apiVersion 1.0.0
   @apiName GetJob
   @apiGroup Jobs
   @apiUse Header
   @apiPermission admin

   @apiParam {Integer} [limit] Limit number of output jobs. Default is 10

   @apiSuccess {Json} job_details Job details
   @apiError {String} 401 Job doesn't exist

  """
  # TODO: accept limit as a parameter
  @PermissionChecker(admin_permission)
  def get(self, job_id=None):
    set_current_auditlog_action('translation-memory.jobs.show' if job_id else 'translation-memory.jobs.index')
    args = self._get_reqparse()
    jobs = []
    username_filter = current_identity.id if current_identity.role != ADMIN else None
    if job_id:
      try:
        job = self.job_api.get_job(job_id)
        if username_filter and username_filter != job["username"]:
            abort(403, mesage="No permission to view status of job {}".format(job_id))
        jobs.append(job)
      except Exception:
        abort(401, mesage="Job {} doesn't exist".format(job_id))
    else:
      for job in self.job_api.scan_jobs(args.limit, username_filter):
        jobs.append(job.to_dict())
    return {"jobs" : jobs}

  def _get_reqparse(self):
    parser = RequestParser(bundle_errors=True)
    parser.add_argument(name='limit', type=int, default=10,
                        help="Limit output to this number of jobs", location='args')
    return parser.parse_args()

  """
   @api {delete} /jobs/:id Cancel job execution
   @apiVersion 1.0.0
   @apiName CancelJob
   @apiGroup Jobs
   @apiUse Header
   @apiPermission admin

   @apiSuccess {String} message Success message
   @apiError {String} 401 Job doesn't exist

  """
  @PermissionChecker(admin_permission)
  def delete(self, job_id):
    set_current_auditlog_action('translation-memory.jobs.destroy')
    # Setup a job using Celery & ES
    task = job_kill_task.apply_async([job_id])
    return {"job_id": task.id, "message": "Job submitted successfully"}
