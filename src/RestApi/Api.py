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
import sys,os
sys.path.append(os.path.dirname(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path = [p for p in sys.path if p]
import logging
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

from flask import Flask, g
from flask_restful import Api

from flask_principal import Principal
from flask_jwt import JWT

from celery import Celery

from datetime import timedelta

from Config.Config import G_CONFIG
from RestApi.Models import db, app, CRUD, Users

# Setup logging
handler = G_CONFIG.config_logging()
if handler: app.logger.addHandler(handler)
# Add file logger
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
app.logger.addHandler(stream_handler)
# fix gives access to the gunicorn error log facility
app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)

principals = Principal(app)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


from RestApi.TmResource import TmResource, TmBatchQueryResource, TmImportResource, TmExportResource, TmExportFileResource, \
                                TmGenerateResource, TmMaintainResource, TmPosTagResource, TmCleanResource, \
                                TmStatsResource, TmUsageStatsResource
from RestApi.UsersResource import UsersResource, UserScopesResource
from RestApi.JobsResource import JobsResource
from RestApi.AdminUi.AdminUi import admin_ui
from RestApi.SettingsResource import SettingsResource
from RestApi.TokenResource import TokenResource
from RestApi.AuthResource import AuthResource
from RestApi.TagsResource import TagsResource

api = Api(app)
api_prefix = "/api/v{}".format(app.config['VERSION'])
# Dummy endpoint to quickly validate JWT token
api.add_resource(TokenResource, api_prefix + '/token')
api.add_resource(AuthResource, api_prefix + '/auth')
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

# User management endpoint
api.add_resource(UsersResource, api_prefix + '/users',
                                api_prefix + '/users/<string:username>')
api.add_resource(UserScopesResource, api_prefix + '/users/<string:username>/scopes')

# Jobs management endpoint
api.add_resource(JobsResource, api_prefix + '/jobs', api_prefix + '/jobs/<string:job_id>')

# Settings
api.add_resource(SettingsResource, api_prefix + '/settings')

# Tags (domains)
api.add_resource(TagsResource, api_prefix + '/tags',
                                api_prefix + '/tags/<string:tag_id>')

#Admin UI panel
#api.add_resource(AdminUiResource, '/admin/<path:page>')
# TODO: serve static resources using nginx. Here used for demo only 
#api.add_resource(AdminUiAssetsResource, '/admin/assets/<string:type>/<string:asset>')

# TODO: uncomment if needed to pass token via URL parameter
# jwt.request_handler(jwt_request_handler)

# Admin UI
#app.register_blueprint(admin_ui)

with app.app_context():
    # Extensions like Flask-SQLAlchemy now know what the "current" app
    # is while within this block. Therefore, you can now run........
    db.create_all()

if __name__ == '__main__':
    print(os.getcwd())
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)
    # fix gives access to the gunicorn error log facility
    app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)
    # db.init_app(app)
    # app.run(host='0.0.0.0', debug=True, port=5002) #For local debugging
    app.run(host='0.0.0.0', debug=True)

