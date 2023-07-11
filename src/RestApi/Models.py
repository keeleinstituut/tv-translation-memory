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
import os
import re
import uuid
import json
import dateutil
import datetime
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_oidc import OpenIDConnect
from Config.Config import G_CONFIG

POSTGRESQL_HOST = G_CONFIG.config['postgresql']['host']
POSTGRESQL_PORT = G_CONFIG.config['postgresql']['port']
POSTGRESQL_DB = G_CONFIG.config['postgresql']['db']
POSTGRESQL_USER = G_CONFIG.config['postgresql']['user']
POSTGRESQL_PASSWORD = G_CONFIG.config['postgresql']['password']

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + POSTGRESQL_USER + ':' + POSTGRESQL_PASSWORD + '@' \
                                        + POSTGRESQL_HOST + ':' + str(POSTGRESQL_PORT) + '/' \
                                        + POSTGRESQL_DB + '?client_encoding=utf8'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://activatm:activatm@localhost/activatm?client_encoding=utf8' #For local debugging
db = SQLAlchemy(app)


app.config['SECRET_KEY'] = 'super-secret'
app.config['VERSION'] = 1
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_AUTH_HEADER_PREFIX'] = "Bearer"

keycloak_config = G_CONFIG.config['keycloak']

if not os.path.exists('client_secrets.json'):
  with open('client_secrets.json', 'w') as f:
    content = {
        keycloak_config['client_id']: {
          "issuer": ''.join([keycloak_config['url'],'realms/',keycloak_config['realm']]),
          "auth_uri": ''.join([keycloak_config['url'],'realms/',keycloak_config['realm'],'/protocol/openid-connect/auth']),
          "client_id": keycloak_config['client_id'],
          "client_secret": keycloak_config['client_secret'],
          "redirect_uris": keycloak_config['redirect_uris'],
          "userinfo_uri": ''.join([keycloak_config['url'],'realms/',keycloak_config['realm'],'/protocol/openid-connect/userinfo']),
          "token_uri": ''.join([keycloak_config['url'],'realms/',keycloak_config['realm'],'/protocol/openid-connect/token']),
          "token_introspection_uri": ''.join([keycloak_config['url'],'realms/',keycloak_config['realm'],'/protocol/openid-connect/token/introspect'])
        }
      }
    f.write(json.dumps(content, indent=2))

app.config.update({
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'master',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_CALLBACK_ROUTE': '/oidc/callback'
})

oidc = OpenIDConnect(app)
oidc.init_app(app)


# Class to add, update and delete data via SQLALchemy sessions
class CRUD:
  @staticmethod
  def add(resource):
    try:
      db.session.add(resource)
      return db.session.commit()
    except Exception:
      logging.error("Exception in CRUD: {}, rolling back".format(str(CRUD.to_dict(resource))))
      db.session.rollback()
    return None

  @staticmethod
  def update():
    try:
      return db.session.commit()
    except Exception:
      logging.error("Exception in CRUD: {}, rolling back".format(str(CRUD.to_dict(resource))))
      db.session.rollback()
    return None

  @staticmethod
  def delete(resource):
    try:
      db.session.delete(resource)
      return db.session.commit()
    except Exception:
      logging.error("Exception in CRUD: {}, rolling back".format(str(CRUD.to_dict(resource))))
      db.session.rollback()
    return None

  @staticmethod
  def to_dict(resource):
    d = dict()
    for k in resource.__table__.columns:
      val = getattr(resource, k.name)
      if isinstance(val, datetime.datetime): val = val.strftime('%Y%m%dT%H%M%SZ')
      # Rename domains -> tags
      name = k.name if k.name != "domains" else "tags"
      d[name] = val
    return d


class Users(db.Model):
  uuid = db.Column(db.Text, primary_key=True)
  username = db.Column(db.Text)
  password = db.Column(db.Text)
  role = db.Column(db.Text, default="user")
  token_expires = db.Column(db.Boolean, default=True)
  is_active = db.Column(db.Boolean, default=True)
  scopes = db.relationship('UserScopes', backref='user')
  settings = db.relationship('UserSettings', backref='user')

  created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

  # Needed for JWT authentication
  @property
  def id(self):
    return self.uuid

  ADMIN = 'admin'

  def __init__(self, **kwargs):
    self.uuid = uuid.uuid4()
    self.update(**kwargs)

  def update(self, **kwargs):
    for key,value in kwargs.items():
      if value == '': continue
      if hasattr(self, key): setattr(self, key, value)
      if key == 'password': self.set_password(value)

  # Add/update user scope
  def update_scope(self, **kwargs):
    if 'id' in kwargs and kwargs['id']:
      scope = UserScopes.query.get(kwargs['id'])
      if not scope or scope.user_uuid != self.uuid: return None
    else:
      scope = UserScopes(self.uuid)

    for key,value in kwargs.items():
      if key == "tags":
        key = "domains" # keep backward compatitbility for now
      elif not value:
        continue
      if re.search('_date$', key):  # convert string to datetime
        value = dateutil.parser.parse(value)
      if hasattr(scope, key): setattr(scope, key, value)
    return scope

  def get_scope(self, id):
    scope = UserScopes.query.get(id)
    if not scope or scope.user_uuid != self.uuid:
      return None
    return scope

  def delete_scopes(self):
    UserScopes.query.filter_by(user_uuid = self.uuid).delete()

  def set_password(self, password):
    self.password = generate_password_hash(password)

  def check_password(self, password):
    if not self.password: return True
    if not password: return False
    return check_password_hash(self.password, password)

  def to_dict(self):
    d = CRUD.to_dict(self)
    del d["password"]
    d["scopes"] = [ s.to_dict() for s in self.scopes]
    return d

class UserScopes(db.Model):
  id = db.Column(db.Integer, primary_key=True)

  user_uuid = db.Column(db.Text, db.ForeignKey('users.uuid'))

  # Permission patterns (list of wildcards)
  lang_pairs = db.Column(db.Text)
  domains = db.Column(db.Text)
  # Additional permissions - update, import or export TM
  can_update = db.Column(db.Boolean, default=False)
  can_import = db.Column(db.Boolean, default=False)
  can_export = db.Column(db.Boolean, default=False)
  # Scope usage limitation (number of queries) and actual usage
  usage_limit = db.Column(db.Integer, default=0)
  usage_count = db.Column(db.Integer, default=0)

  # Start/end date of the scope
  start_date = db.Column(db.Date)
  end_date = db.Column(db.Date)

  # Scope creation date
  created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

  def __init__(self, user_uuid):
    self.user_uuid = user_uuid

  def to_dict(self):
    return CRUD.to_dict(self)

  def increase_usage_count(self, count):
    #self.usage_count += count
    # Avoid race condition
    try:
      self.usage_count = UserScopes.usage_count + count
      db.session.commit() # this should solve (or at least minimize deadlock occurrences
    except Exception:
      db.session.rollback()

class UserSettings(db.Model):
  id = db.Column(db.Integer, primary_key=True)

  user_uuid = db.Column(db.Text, db.ForeignKey('users.uuid'))
  # Regular expressions to apply (separated with comma)
  regex = db.Column(db.Text)

  def __init__(self, user_uuid):
    self.user_uuid = user_uuid

  def to_dict(self):
    return CRUD.to_dict(self)

class Tags(db.Model):
   id = db.Column(db.Text, primary_key=True)
   name = db.Column(db.Text)
   type = db.Column(db.Text)

   def __init__(self, id, name, type ):
     self.id = id
     self.name = name
     self.type = type

   def update(self, **kwargs):
     for key,value in kwargs.items():
       if value == '': continue
       if hasattr(self, key): setattr(self, key, value)

   def to_dict(self):
     return CRUD.to_dict(self)

   # Use this method to migrate existing tags (domains) from OpenSearch
   @staticmethod
   def get_add_tags(tags):
     for tag_id in tags:
       with app.app_context():
        if not Tags.query.get(tag_id):
          tag = Tags(tag_id, name=tag_id, type="unspecified")
          CRUD.add(tag)

   @staticmethod
   def has_public(tags):
     if isinstance(tags, str):
       tags = [tags]
     for tag_id in tags:
       tag = Tags.query.get(tag_id)
       if tag and tag.type == "public": return True
     return False

   @staticmethod
   def has_specified(tags):
     if isinstance(tags, str):
       tags = [tags]
     for tag_id in tags:
       tag = Tags.query.get(tag_id)
       if tag and tag.type != "unspecified": return True
     return False


   @staticmethod
   def has_public_name(tag_names):
     if isinstance(tag_names, str):
       tag_names = [tag_names]
     tag_ids = []
     for tag_name in tag_names:
       tag = Tags.query.filter_by(name=tag_name).first()
       if tag: tag_ids.append(tag.id)
     return Tags.has_public(tag_ids)

