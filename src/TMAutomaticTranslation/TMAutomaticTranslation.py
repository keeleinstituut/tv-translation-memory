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
import logging
from Config.ConfigMTEngines import ENGINE_CONFIG


class NoOpTranslator:
  """
  No-op translator for deprecated MT engine functionality.
  Machine Translation engines have been deprecated and removed.
  This class provides backward compatibility by implementing the translator
  interface but always returns None (no translation).
  """
  
  def __init__(self, **kwargs):
    logging.warning("Machine Translation engines are deprecated. NoOpTranslator is being used - translations will return None.")
    pass

  def translate(self, text, to_lang, from_lang=None):
    """
    Deprecated: Machine Translation is no longer available.
    Returns None for all translation requests.
    """
    if isinstance(text, str):
      return None
    # list or tuple
    if isinstance(text, (list, tuple)):
      return [None] * len(text)
    return None

  def translate_batch(self, text_list, to_lang, from_lang=None):
    """
    Deprecated: Machine Translation is no longer available.
    Returns list of None values matching the input length.
    """
    return [None] * len(text_list) if text_list else []


class TMAutomaticTranslation:

  # MT engines have been deprecated - translators dict removed
  engines = dict()

  def __init__(self, src_lang, tgt_lang, mt_engine):
    self.src_lang = src_lang
    self.tgt_lang = tgt_lang
    self.translator = mt_engine

  @staticmethod
  def get_engine(src_lang, tgt_lang, domain):
    """
    Returns a no-op translator since MT engines have been deprecated.
    Maintains backward compatibility for code that expects a translator instance.
    """
    if not domain: domain = ""
    key = "{}-{}-{}".format(src_lang, tgt_lang, domain)
    if not key in TMAutomaticTranslation.engines:
      logging.warning("Machine Translation engines are deprecated. Using NoOpTranslator for key: {}".format(key))
      TMAutomaticTranslation.engines[key] = TMAutomaticTranslation(src_lang, tgt_lang, NoOpTranslator())
    return TMAutomaticTranslation.engines[key]

  # Get engine configuration (deprecated - kept for backward compatibility)
  @staticmethod
  def get_engine_config(src_lang, tgt_lang, domain):
    mt_domain = 'any' if not domain else domain
    config = ENGINE_CONFIG.get_engine_config(src_lang, tgt_lang, mt_domain)
    return config

  # Translate a list of segments. Receive a list of segments and return a list of translated segments
  def translate(self, str_or_list):
    return self.translator.translate(str_or_list, self.tgt_lang, self.src_lang)



if __name__ == "__main__":
  # Example usage - note that MT engines are deprecated, so translations will return None
  bt = TMAutomaticTranslation.get_engine('en', 'es', None)
  print("Translation result (will be None):", bt.translate(["What is your name?", "Who are you?"]))
  print("Translation result (will be None):", bt.translate("What is your name?"))
