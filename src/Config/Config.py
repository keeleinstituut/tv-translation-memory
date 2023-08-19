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
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS Oe ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import os
import re
import yaml
import logging


def parse_config(data, tag='!ENV'):
  """
  Load a yaml configuration file and resolve any environment variables
  The environment variables must have !ENV before them and be in this format
  to be parsed: ${VAR_NAME}.
  E.g.:
  database:
      host: !ENV ${HOST}
      port: !ENV ${PORT}
  app:
      log_path: !ENV '/var/${LOG_PATH}'
      something_else: !ENV '${AWESOME_ENV_VAR}/var/${A_SECOND_AWESOME_VAR}'
  :param str path: the path to the yaml file
  :param str data: the yaml data itself as a stream
  :param str tag: the tag to look for
  :return: the dict configuration
  :rtype: dict[str, T]
  """
  # pattern for global vars: look for ${word}
  pattern = re.compile('.*?\${(\w+)}.*?')
  loader = yaml.SafeLoader

  # the tag will be used to mark where to start searching for the pattern
  # e.g. somekey: !ENV somestring${MYENVVAR}blah blah blah
  loader.add_implicit_resolver(tag, pattern, None)

  def constructor_env_variables(loader, node):
    """
    Extracts the environment variable from the node's value
    :param yaml.Loader loader: the yaml loader
    :param node: the current node in the yaml
    :return: the parsed string that contains the value of the environment
    variable
    """
    value = loader.construct_scalar(node)
    match = pattern.findall(value)  # to find all env variables in line
    if match:
      full_value = value
      for g in match:
        full_value = full_value.replace(
          f'${{{g}}}', os.environ.get(g, g)
        )
      return full_value
    return value

  loader.add_constructor(tag, constructor_env_variables)
  return yaml.load(data, Loader=loader)


class Config:
  config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'conf', 'elastictm.yml')
  config = dict()
  is_loaded = False

  def __init__(self):
    self.config = dict()
    if not self.is_loaded:
      self.load(self.config_path)
      self.is_loaded = True

  def load(self, conf_file):
    with open(conf_file, 'r') as ymlfile:
      # self.config = yaml.full_load(ymlfile)
      self.config = parse_config(ymlfile)
      self.is_loaded = True

  def get_cleaning_rules(self, langs=None):
    rules = dict()
    m = self.config.get("maintenance")
    if not m: return []
    mr = m.get("cleaning_rules")
    if not mr: return []
    # Combine generic and language-specific rules
    rules["all"] = mr.get("all", [])
    if langs:
      # update with language-specific rules
      rules.update({lang: mr.get(lang, []) for lang in langs})
      # update with language pair-specific (en-es and es-en) rules
      rules.update({lang_pair: mr.get(lang_pair, []) for lang_pair in ['-'.join(langs), '-'.join(langs[::-1])]})
    return rules

  def get_split_rules(self, src_lang=None, tgt_lang=None):
    src_class = None
    s = self.config.get("split")
    # Search lang pairs especific rule
    if s:
      sr = s.get(src_lang.lower() + '-' + tgt_lang.lower())
      if not sr:
        sr = s.get(src_lang.lower() + '-' + 'any')
        if not sr:
          sr = s.get('any' + '-' + 'any')
          if sr:
            src_lang = 'any'
          else:
            return src_class # Return None
      src_class = sr.get(src_lang.lower())
    return src_class

  def get_dirty_threshold(self):
    default = 1
    m = self.config.get("maintenance")
    if not m: return default
    threshold = m.get("dirty_threshold")
    if not threshold: return default
    return threshold

  def get_query_penalize(self):
    default = 5
    m = self.config.get("query")
    if not m: return default, default
    domain = m.get("p_domain")
    if not domain: return default, default
    dirty = m.get("p_dirty")
    if not dirty: return default, default
    return domain, dirty

  def get_query_token_count(self):
    default = 50
    t = self.config.get("query")
    if not t: return default
    max_token_count = t.get("p_token_count")
    return max_token_count

  def get_src_tgt_threshold(self):
    default = 0.25
    t = self.config.get("query")
    if not t: return default
    p_src_tgt_align = t.get("p_src_tgt_align")
    return p_src_tgt_align

  def get_wait_query_time(self):
    default_aut = 7
    default = 4
    t = self.config.get("query")
    if not t: return default_aut, default
    wait_time_with_AT = t.get("wait_time_with_AT")
    wait_time_without_AT = t.get("wait_time_without_AT")
    return wait_time_with_AT, wait_time_without_AT

  def config_logging(self):
    # try:
    #   from logging.handlers import RotatingFileHandler
    #   log_path = self.config["general"]["log_path"]
    #   os.makedirs(log_path, exist_ok=True)
    #   handler = RotatingFileHandler(os.path.join(G_CONFIG.config["general"]["log_path"], "activatm.log"),
    #                                      maxBytes=1000000, backupCount=10)
    #   handler.setLevel(logging.INFO)
    #   formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    #   handler.setFormatter(formatter)
    #   logging.getLogger().addHandler(handler)
    # except:
    # Fallback - basic configuration
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
#      handler = None

    #return handler


# Global config
G_CONFIG = Config()

if __name__ == "__main__":
  print(G_CONFIG.config)
  print('\n')
  print(G_CONFIG.get_cleaning_rules())