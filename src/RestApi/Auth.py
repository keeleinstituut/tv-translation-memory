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

import jwt
from flask import current_app
from flask_principal import identity_changed, identity_loaded, RoleNeed, UserNeed, Permission, PermissionDenied
from RestApi.Keycloak import KeycloakIdentity
from lib.flask_jwt import _jwt_required, current_identity
from flask_restful import abort
from functools import wraps

import fnmatch
import datetime

import logging


ADMIN = 'admin'
TOLKEVARAV_PHYSICAL_USER = 'TOLKEVARAV_PHYSICAL_USER'

SSO_REALM_ROLE_PREFIX = 'sso_realm/'
SSO_REALM_FULL_READ_ONLY = SSO_REALM_ROLE_PREFIX + "tv-translation-memory-service-full-read-only-access"

# Admin permission requires admin role
admin_permission = Permission(RoleNeed(ADMIN))
full_read_only_permission = Permission(RoleNeed(SSO_REALM_FULL_READ_ONLY))

# User permission requires either admin or user role
# user_permission = Permission(RoleNeed(TOLKEVARAV_PHYSICAL_USER)).union(admin_permission)

create_tag_permission = Permission(RoleNeed('CREATE_TM'))
edit_tag_permission = Permission(RoleNeed('EDIT_TM_METADATA'))
import_tm_permission = Permission(RoleNeed('IMPORT_TM'))
export_tm_permission = Permission(RoleNeed('EXPORT_TM'))
delete_tm_permission = Permission(RoleNeed('DELETE_TM'))
view_tm_permission = Permission(RoleNeed('VIEW_TM')).union(full_read_only_permission)

def identity(access_token):
    identity = KeycloakIdentity(access_token=access_token)
    identity_changed.send(current_app._get_current_object(), identity=identity)
    return identity

@identity_loaded.connect
def on_identity_loaded(sender, identity: KeycloakIdentity):
  logging.info("UserScopeChecker: identity loaded for insitutionUser: {}; institution: {}".format(identity.institution_user_id, identity.institution_id))


  if identity.is_physical_user:
    # Add the UserNeed to the identity
    identity.provides.add(UserNeed(identity.institution_user_id))
    # Mark user as physical user
    identity.provides.add(RoleNeed(TOLKEVARAV_PHYSICAL_USER))

    # Add all privileges to identity
    for privilege in identity.privileges:
      identity.provides.add(RoleNeed(privilege))

  # Mark user as service account
  for realm_role in identity.realm_access_roles:
    identity.provides.add(RoleNeed('{}{}'.format(SSO_REALM_ROLE_PREFIX, realm_role)))

  # identity.provides.add(RoleNeed(identity.role))
  identity.provides.add(RoleNeed('IMPORT_TM'))


# Decorator class, combining JWT token check and Principals permission check
class PermissionChecker:
  # Principal's Permission object
  def __init__(self, permission, jwt_required=_jwt_required):
    self.permission = permission
    self.jwt_required = jwt_required  # function for checking JWT token

  # Wraps given func with JWT token and Principal permission check
  def __call__(self, func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      # Check JWT token in the default realm (sets current_identity object)
      self.jwt_required(current_app.config['JWT_DEFAULT_REALM'])
      # Inform Principal about changed identity by sending a signal. Current identity is
      # taken from JWT-provided current_identity object
      # identity_changed.send(current_app,
      #                     identity=current_identity)
      ctx = self.permission.require()
      logging.info("Principal context: {}, identity: {}".format(ctx.__dict__, ctx.identity))
      # Test whether current identity has enough permissions
      try:
        self.permission.test()
      except PermissionDenied as e:
        logging.info("PermissionChecker: denied access to institutionUser: {}; reason: {}".format(current_identity.institution_user_id, str(e)))
        abort(403, message="You don't have sufficient permissions for this operation")
      logging.info("PermissionChecker: authorized access to institutionUser: {}".format(current_identity.institution_user_id))
      return func(*args, **kwargs)
    return wrapper

# from RestApi.Models import Users

# Check user scope (language pair, domain, usage limit)
class UserScopeChecker:

  @staticmethod
  def check(lang_pair, domain, is_update=False, is_import=False, is_export=False):
    user = current_identity

    failed = is_update and not user.can(Permission(RoleNeed('IMPORT_TM'))) or \
             is_import and not user.can(Permission(RoleNeed('IMPORT_TM'))) or \
             is_export and not user.can(Permission(RoleNeed('EXPORT_TM')))

    status = not failed

    if not status:
      message = "UserScopeChecker: access denied to {}, language pair: {}, domain: {}, update: {}"
      logging.info(message.format(user.id, lang_pair, domain, is_update))
      return False
    else:
      message = "UserScopeChecker: authorized access to: {}, language pair: {}, domain: {}, update: {}"
      logging.info(message.format(user.id, lang_pair, domain, is_update))
      return True

  @staticmethod
  def filter_lang_pairs(lp_str_list, allow_reverse=False): # for ex. ['en_es', 'en_ar']
    user = current_identity
    if not user.scopes:
      # no scope defined, all pairs are accessible
      return lp_str_list
      #if user.role == Users.ADMIN:
      #  return lp_str_list  # no scope defined, all pairs are accessible
      #else:
      #  return []

    lp_set = set()
    for scope in user.scopes:
      if not UserScopeChecker._is_valid(scope): continue
      for lp in lp_str_list:
        if UserScopeChecker._check_pattern(scope.lang_pairs, lp):
          lp_set.add(lp)
        elif allow_reverse:
          reverse_lp = '_'.join(lp.split('_')[::-1])
          if UserScopeChecker._check_pattern(scope.lang_pairs, reverse_lp):
            lp_set.add(lp)
    return list(lp_set)


  @staticmethod
  def filter_domains(domains, lp=None, key_fn=lambda k: k, allow_unspecified=True):
    if (current_identity.can(Permission(RoleNeed(SSO_REALM_FULL_READ_ONLY)))):
      return domains

    return [d for d in domains if d["type"] == "public" or allow_unspecified and d["type"] == "unspecified" or str(d['institution_id']) == current_identity.institution_id]  # return only public and unspecified tags


  @staticmethod
  def _check(user, lang_pair_str, domain_list, is_update, is_import, is_export):
    if not user.scopes or not domain_list:
      # Deny actions
      if current_identity.role != ADMIN and (is_update or is_import or is_export): return False
      return True

    today = datetime.date.today()

    found = False
    for scope in user.scopes:
      # Check for expired scope
      if scope.start_date and today < scope.start_date \
        or scope.end_date and today > scope.end_date: continue
      # Check lang pair pattern(s)
      s = UserScopeChecker._check_pattern(scope.lang_pairs, lang_pair_str)
      if not s: continue
      # Make sure all scope's domain appear in the domain_list of TU
      if domain_list:
        s = True
        for scope_domain in scope.domains.split(","):
          if scope_domain not in domain_list:
            s = False
            logging.info("Scope domain {} is not in the list: {}".format(scope_domain, domain_list))
            break
        if not s: continue
      # Check if can update (for update check only)
      if is_update and not scope.can_update or \
              is_import and not scope.can_import or \
              is_export and not scope.can_export:
        continue
      else:
        # Check usage limit (only for queiries)
        if scope.usage_limit and scope.usage_count > scope.usage_limit:
          continue
        else:
          scope.increase_usage_count(1)
      found = True
    return found

  @staticmethod
  def _is_valid(scope):
    today = datetime.date.today()
    return not(scope.start_date and today < scope.start_date \
            or scope.end_date and today > scope.end_date)

  @staticmethod
  def _check_pattern(patterns, value):
    if not value or not isinstance(value, (str,bytes)):
       logging.warning("Invalid domain value: {} - skipping".format(value))
       return False
    if not patterns: return True # any value is matching null pattern
    pattern_list = patterns.split(',')
    for p in pattern_list:
      logging.info("Checking domain(tag): {} against pattern: {}".format(value,p)) 
      if fnmatch.fnmatch(value, p):
        return True
    return False


def decode_handler(token):
  leeway = current_app.config['JWT_LEEWAY']
  verify_claims = current_app.config['JWT_VERIFY_CLAIMS']
  required_claims = current_app.config['JWT_REQUIRED_CLAIMS']

  options = {
    'verify_' + claim: True
    for claim in verify_claims
  }

  options.update({
    'require_' + claim: True
    for claim in required_claims
  })

  header = jwt.get_unverified_header(token)
  alg = header["alg"]
  kid = header["kid"]
  jwk = current_app.keycloak.get_jwk(kid)
  return jwt.decode(token, jwk.key, options=options, algorithms=[alg], leeway=leeway, audience=['account'])
