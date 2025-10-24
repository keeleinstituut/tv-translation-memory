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

#####
# Uncomment this to enable remote debugging using pycharm's built-in remote debugger.
# Additional pip dependency must be installed depending on the version of pycharm you are using.
# ATTACH_DEBUGGER = False
#
# if ATTACH_DEBUGGER:
#     import pydevd_pycharm
#     pydevd_pycharm.settrace('host.docker.internal', port=5010, stdoutToServer=True, stderrToServer=True)
#####

import sys,os
sys.path.append(os.path.dirname(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path = [p for p in sys.path if p]

import logging
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

# Limit logging
# log = logging.getLogger()
# log.setLevel(logging.ERROR)

from flask_restful import Api
from flask_principal import Principal
from lib.flask_jwt import JWT

from Config.Config import G_CONFIG
from RestApi.Models import db, app
from RestApi.Keycloak import Keycloak
from helpers.AuditContext import current_auditlog_action

app.config['SECRET_KEY'] = 'super-secret'
app.config['VERSION'] = 1
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['FILEUPLOAD_IMPORT_EXTENSIONS'] = ['.tmx', '.zip']

# Setup logging
# handler = G_CONFIG.config_logging()
# if handler: app.logger.addHandler(handler)
# # Add file logger
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.DEBUG)
# app.logger.addHandler(stream_handler)
# # fix gives access to the gunicorn error log facility
# app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)


import RestApi.Celery

from RestApi.Auth import identity, decode_handler
from RestApi.TmResource import TmResource, TmBatchQueryResource, TmImportResource, TmExportResource, \
                                TmExportFileResource, TmGenerateResource, TmMaintainResource, TmPosTagResource, \
                                TmCleanResource, TmStatsResource, TmUsageStatsResource
from RestApi.JobsResource import JobsResource
from RestApi.TagsResource import TagsResource

from flask_cors import CORS
CORS(app)

api = Api(app)
api_prefix = "/api/v{}".format(app.config['VERSION'])

# TM endpoint (query, export and import)
tms_prefix = api_prefix + '/tm'
api.add_resource(TmResource, tms_prefix)
api.add_resource(TmBatchQueryResource, tms_prefix + '/query_batch')
api.add_resource(TmImportResource, tms_prefix + '/import')
api.add_resource(TmExportResource, tms_prefix + '/export')
api.add_resource(TmExportFileResource, tms_prefix + '/export/file',
                                      tms_prefix + '/export/file/<string:export_id>')

api.add_resource(TmGenerateResource, tms_prefix + '/generate')
api.add_resource(TmPosTagResource, tms_prefix + '/pos')
api.add_resource(TmMaintainResource, tms_prefix + '/maintain')
api.add_resource(TmCleanResource, tms_prefix + '/clean')
api.add_resource(TmStatsResource, tms_prefix + '/stats')
api.add_resource(TmUsageStatsResource, tms_prefix + '/stats/usage')

# Jobs management endpoint
api.add_resource(JobsResource, api_prefix + '/jobs', api_prefix + '/jobs/<string:job_id>')

# Tags (domains)
api.add_resource(TagsResource, api_prefix + '/tags',
                                api_prefix + '/tags/<uuid:tag_id>')

@app.route('/healthz')
def healthz():
    return "OK"

app.config['JWT_AUTH_URL_RULE'] = None
app.config['JWT_AUTH_HEADER_PREFIX'] = 'Bearer'
app.keycloak = Keycloak(
    url=G_CONFIG.config['keycloak']['url'],
    realm=G_CONFIG.config['keycloak']['realm'],
    client_id=G_CONFIG.config['keycloak']['client_id'],
    client_secret=G_CONFIG.config['keycloak']['client_secret'],
)
principal = Principal(app, use_sessions=False)
jwt_middleware = JWT(app=app, identity_handler=identity)
jwt_middleware.jwt_decode_handler(decode_handler)

@app.after_request
def append_auditlog_action_header(response):
    response.headers['X-Log-Action'] = str(current_auditlog_action)
    return response

# Admin UI
# from RestApi.AdminUi.AdminUi import admin_ui
# app.register_blueprint(admin_ui)

# ApiDoc
from RestApi.ApiDoc import apidoc
app.register_blueprint(apidoc)

with app.app_context():
    # Extensions like Flask-SQLAlchemy now know what the "current" app
    # is while within this block. Therefore, you can now run........
    db.create_all()


if __name__ == '__main__':
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)
    # fix gives access to the gunicorn error log facility
    app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)
    app.run(host='0.0.0.0', debug=True)


