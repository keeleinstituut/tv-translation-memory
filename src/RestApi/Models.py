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
import datetime
import logging
import uuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from Config.Config import G_CONFIG

POSTGRESQL_HOST = G_CONFIG.config['postgresql']['host']
POSTGRESQL_PORT = G_CONFIG.config['postgresql']['port']
POSTGRESQL_DB = G_CONFIG.config['postgresql']['db']
POSTGRESQL_USER = G_CONFIG.config['postgresql']['user']
POSTGRESQL_PASSWORD = G_CONFIG.config['postgresql']['password']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + POSTGRESQL_USER + ':' + POSTGRESQL_PASSWORD + '@' \
                                        + POSTGRESQL_HOST + ':' + str(POSTGRESQL_PORT) + '/' \
                                        + POSTGRESQL_DB + '?client_encoding=utf8'
db = SQLAlchemy(app)


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


class Tags(db.Model):
   id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
   institution_id = db.Column(db.Uuid)
   name = db.Column(db.Text)
   type = db.Column(db.Text)

   def __init__(self, institution_id, name, type):
     self.name = name
     self.type = type
     self.institution_id = institution_id

   def update(self, **kwargs):
     for key,value in kwargs.items():
       if value == '': continue
       if hasattr(self, key): setattr(self, key, value)

   def to_dict(self):
     return CRUD.to_dict(self)

   # Use this method to migrate existing tags (domains) from OpenSearch
   @staticmethod
   def get_add_tags(tags, institution_id):
     for tag_id in tags:
       with app.app_context():
        if not Tags.query.get((tag_id, institution_id)):
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

