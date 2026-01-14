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
import sys
import os
import requests
import logging
import time
import json
from timeit import default_timer as timer
from requests_toolbelt import MultipartEncoder


class RestClient:

  def __init__(self, username=None, password=None, host='http://localhost', port=5000, version='1', token=None):
    self.username = username
    self.password = password
    self.set_url(host, port, version)
    self.token = token

  def set_url(self, host, port, version):
    self.base_url = "{}:{}/api/v{}".format(host, port, version)

  def query(self, query, slang, tlang, out='json', strip_tags=False, min_match=75, limit=10, operation_match='regex,tags', concordance=False, aut_trans=False, domain=None, tag=None, smeta=None,tmeta=None): # split isn't default ,split
    params = {'slang': slang, 'tlang': tlang, 'out': out, 'q': query,
              'strip_tags': strip_tags, 'min_match': min_match, 'limit': limit,
              'operation_match': operation_match,
              'concordance': concordance,
              'smeta': smeta, 'tmeta': tmeta,
              'aut_trans': aut_trans,
              'tag' : tag if tag else domain} # backward compatibility

    response = self._call_get('/tm', params=params)
    if out == 'json':
      return response.json()
    # Moses format
    return response.content.decode('utf-8')

  def query_batch(self, queries, slang, tlang, out='json', strip_tags=False, min_match=75, limit=10, operation_match = 'regex,tags,posTag', aut_trans=False, domain=None, split_pattern=None):
    params = {
      'slang': slang,
      'tlang': tlang,
      'out': out,
      'strip_tags': strip_tags,
      'min_match': min_match,
      'limit': limit,
      'operation_match': operation_match,
      'aut_trans': aut_trans,
      'q': queries
    }
    if domain:
      params['tag'] = domain
    if split_pattern:
      params['split_pattern'] = split_pattern

    response = self._call_post('/tm/query_batch', params=params)
    if out == 'json':
      return response.json()
    # Moses format
    return response.content.decode('utf-8')



  def add_tu(self, stext, ttext, slang, tlang, domain, file_name='', smeta=None,tmeta=None):
    json_data = {
      'stext': stext,
      'ttext': ttext,
      'slang': slang,
      'tlang': tlang,
      'tag': [domain] if isinstance(domain, str) else domain,  # tag should be a list
      'file_name': file_name
    }
    if smeta:
      json_data['smeta'] = smeta
    if tmeta:
      json_data['tmeta'] = tmeta
    
    response = self._call_post('/tm', data=json_data)
    return response.json()

  def import_tm(self, tmx_file, domain, lang_pairs=None):
    if lang_pairs is None:
        lang_pairs = []

    with open(tmx_file, 'rb') as f:
      file_content = f.read()

    import io
    file_obj = io.BytesIO(file_content)
    files = {'file': (os.path.basename(tmx_file), file_obj, 'application/zip')}
    data = {}

    if isinstance(domain, list):
      data['tag'] = domain
    else:
      data['tag'] = [domain]

    if lang_pairs:
      if isinstance(lang_pairs, list):
        data['lang_pair'] = lang_pairs
      else:
        data['lang_pair'] = [lang_pairs]

    response = self._call_multipart('/tm/import', data=data, files=files)
    return response.json()

  def export_tm(self, slang, tlang, squery=None, tquery=None, duplicates_only=False, filters=None):
    if filters is None:
        filters = {}
    params = {'slang': slang, 'tlang': tlang}
    if squery: params['squery'] = squery
    if tquery: params['tquery'] = tquery
    if duplicates_only: params['duplicates_only'] = True
    params.update(filters)
    # Actual call
    response = self._call_post('/tm/export', params=params)
    return JobMonitor(self, response.json())()

  def generate_tm(self, slang, tlang, plang, domain=None, force=False):
    if domain is None:
        domain = []
    response = self._call_put('/tm/generate', params={'slang': slang, 'tlang': tlang, 'plang': plang, 'tag': domain, 'force': force})
    return JobMonitor(self, response.json())()


  def delete_tm(self, slang, tlang, duplicates_only=False, filters=None):
    if filters is None:
        filters = {}
    params = {'slang': slang, 'tlang': tlang}
    params.update(filters)
    if duplicates_only: params['duplicates_only'] = True

    response = self._call_delete('/tm', params=params)
    # Return the job response directly instead of waiting for completion
    # This allows tests to query the data instead of checking job status
    return response.json()

  def pos(self, slang, tlang, universal=False, filters=None):
    if filters is None:
        filters = {}
    params = {'slang': slang, 'tlang': tlang, 'universal': universal}
    params.update(filters)
    response = self._call_put('/tm/pos', params=params)
    return JobMonitor(self, response.json())()

  def maintain(self, slang, tlang, filters=None):
    if filters is None:
        filters = {}
    params = {'slang': slang, 'tlang': tlang}
    params.update(filters)
    response = self._call_post('/tm/maintain', params=params)
    return JobMonitor(self, response.json())()

  def clean(self, slang, tlang, filters=None):
    if filters is None:
        filters = {}
    params = {'slang': slang, 'tlang': tlang}
    params.update(filters)
    response = self._call_post('/tm/clean', params=params)
    return JobMonitor(self, response.json())()

  def stats(self):
    response = self._call_get('/tm/stats')
    return response.json()

  def get_user(self, username):
    api_path = '/users'
    if username:
      api_path += '/{}'.format(username)
    response = self._call_get(api_path)
    return response.json()

  def set_user(self, username, **kwargs):
    response = self._call_post('/users/{}'.format(username), params=kwargs)
    return response.json()

  def delete_user(self, username):
    response = self._call_delete('/users/{}'.format(username))
    return response.json()


  def get_tag(self, tagname=None):
    api_path = '/tags'
    if tagname:
      api_path += '/{}'.format(tagname)
    response = self._call_get(api_path)
    return response.json()

  def set_tag(self, tagname=None, **kwargs):
    if tagname:
      response = self._call_post('/tags/{}'.format(tagname), data=kwargs)
    else:
      response = self._call_post('/tags', data=kwargs)
    return response.json()

  def delete_tag(self, tagname, **kwargs):
    response = self._call_delete('/tags/{}'.format(tagname), params=kwargs)
    return response.json()

  def set_user_scope(self, username, **kwargs):
    response = self._call_post('/users/{}/scopes'.format(username), params=kwargs)
    return response.json()

  def delete_scope(self, username, scope, **kwargs):
    response = self._call_delete('/users/{}/scopes/{}'.format(username, scope), params=kwargs)
    return response.json()

  def get_job(self, job_id, **kwargs):
    response = self._call_get('/jobs/{}'.format(job_id), params=kwargs)
    return response.json()

  def kill_job(self, job_id, **kwargs):
    response = self._call_delete('/jobs/{}'.format(job_id), params=kwargs)
    return response.json()

  def get_settings(self, **kwargs):
    response = self._call_get('/settings', params=kwargs)
    return response.json()

  def set_settings(self, **kwargs):
    response = self._call_put('/settings', params=kwargs)
    return response.json()


  # --- Helper methods ------

  def _call_post(self, suffix, data=None, params=None, **kwargs):
    """Call API with POST - JSON body if data provided, query params if params provided"""
    import json
    if data is not None:
      headers = kwargs.pop('headers', {})
      headers['Content-Type'] = 'application/json'
      json_data = json.dumps(data)
      return self._call_api(suffix, 'post', data=json_data, headers=headers, **kwargs)
    else:
      return self._call_api(suffix, 'post', params=params or {}, **kwargs)

  def _call_put(self, suffix, data=None, params=None, **kwargs):
    """Call API with PUT - JSON body if data provided, query params if params provided"""
    import json
    if data is not None:
      headers = kwargs.pop('headers', {})
      headers['Content-Type'] = 'application/json'
      json_data = json.dumps(data)
      return self._call_api(suffix, 'put', data=json_data, headers=headers, **kwargs)
    else:
      return self._call_api(suffix, 'put', params=params or {}, **kwargs)

  def _call_multipart(self, suffix, data=None, files=None, **kwargs):
    """Call API with PUT and multipart/form-data (for file uploads)"""
    return self._call_api(suffix, 'put', data=data or {}, files=files or {}, **kwargs)

  def _call_get(self, suffix, params=None, **kwargs):
    """Call API with GET and query parameters"""
    return self._call_api(suffix, 'get', params=params or {}, **kwargs)

  def _call_delete(self, suffix, params=None, **kwargs):
    """Call API with DELETE and query parameters"""
    return self._call_api(suffix, 'delete', params=params or {}, **kwargs)

  def _call_api(self, suffix, method='get', params={}, data={}, headers={}, files={}, stream=False):
    # Imitating do-while: first, try to call method with JWT authentication. If failed, try authorizing with the credentials
    # and call it again. If failed again -> raise an exception
    logging.debug("Api: {}, method: {}, Params: ".format(suffix, method, params))
    t_start = timer()

    for i in range(0,2):
      response = None
      if self.token:
        logging.info("Bearer Token: {}".format(self.token[:20] + '...' if len(self.token) > 20 else self.token))
        headers.update({'Authorization': 'Bearer {}'.format(self.token)})
        response = getattr(requests, method)(self._get_url(suffix), params=params, data=data, headers=headers, files=files, stream=stream, verify=False)
      logging.debug("------ {}, response: {}".format(i, response))
      #if response != None: logging.debug("Request: {}".format(response.request.__dict__))
      # If token expired, authorize again and repeat
      if response == None or response.status_code == 401:
        if i: 
          if response:
            response.raise_for_status() # we are here for the second time, something is wrong with authorization,
          else:
            raise Exception("Authentication failed and no credentials available")
        # Only try to auth if we have username/password (legacy auth endpoint)
        if self.username and self.password:
          self._auth() # get token
        else:
          # No credentials available, raise error
          if response:
            response.raise_for_status()
          else:
            raise Exception("Authentication required but no token or credentials provided")
      elif not response.ok:
        # Some other problem has occured - raise an exception
        try:
          logging.error("Server returned error message: {}".format(response.json()))
        except:
          pass # if response is not json
        response.raise_for_status()
      else:
        # success
        t_end = timer()
        logging.debug("Execution time: {}".format(t_end-t_start))
        return response

  def _auth(self):
    auth_response = requests.post(self._get_url('/auth'),
                                  data=json.dumps({'username': self.username, 'password': self.password}),
                                  headers={"content-type": "application/json"},
                                  verify=False)
    # TODO: cache token for future requests
    if auth_response.ok:
      self.token = auth_response.json()['access_token']
      logging.debug("Authorized user {} successfully".format(self.username))
      return True
    auth_response.raise_for_status()

  def _get_url(self, suffix):
    if suffix[0] != '/': suffix = '/' + suffix
    return self.base_url + suffix

class JobMonitor:
  def __init__(self, client, job_json):
    self.client = client
    print(job_json)
    self.job_id = job_json['job_id']
    self.end_statuses = {'finished', 'failed', 'succeded', 'killed'}

  def __call__(self, *args, **kwargs):
    status_json = self.client.get_job(self.job_id)
    print("STATUS: {}".format(status_json))
    job_status = status_json['jobs'][0]['status']
    logging.info('Monitoring job: {}'.format(self.job_id))
    logging.info('Job status: {}'.format(job_status))
    while not job_status in self.end_statuses: # failed? killed?
      time.sleep(5)
      status_json = self.client.get_job(self.job_id)
      print(status_json)
      job_status = status_json['jobs'][0]['status']
      logging.info('Job status: {}'.format(job_status))
    return status_json

if __name__ == "__main__":
  logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO, stream=sys.stderr)
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  import json, pprint
  from CommandLine import CommandLine
  cl = CommandLine()
  client = RestClient("admin", "admin")
  out = cl(client)
  if isinstance(out, dict):
    pprint.pprint(json.dumps(out, indent=4))
  else:
    for o in out:
      pprint.pprint(o)
