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
import sys, os, datetime
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..'))

import json
from functools import reduce

from Config.Config import G_CONFIG
from JobApi.tasks.Task import Task

from RestApi.Models import app, CRUD, ContentChecks, Tags, db
from TMDbApi.TMDbApi import TMDbApi
from BuerokrattClient import BuerokrattAnonymizerClient


class ContentCheckTask(Task):
  def __init__(self, job_id):
    super().__init__(job_id)
    self.db = TMDbApi()
    self.buerokrattAnonymizerClient = BuerokrattAnonymizerClient()

  def run_sequential(self):
    with app.app_context():
      params = self.job['params']

      content_check = ContentChecks.query.get(params['content_check_id'])
      tag = Tags.query.get(content_check.tag_id)
      langs = tuple(tag.lang_pair.split('_'))

      try:
        stats = self.db.mstats()
        tag_segment_count = stats.get('domain', {}).get(str(tag.id))

        content_check.status = ContentChecks.STATUS_RUNNING
        content_check.segments_count = tag_segment_count
        content_check.segments_checked_count = 0
        CRUD.update()

        filters = {
          'domain': [tag.id]
        }

        iterator = self.segment_iter(langs, filters)
        segments = list(iterator)
        checks = []

        # for chunk in self.chunk_iterator(iterator, 50):
        # for chunk in self.chunk_iterator(iterator, 10):
        for chunk in self.chunk_iterator(iter(segments), 50):
          texts = list(reduce(lambda acc, seg: [*acc, seg.source_text, seg.target_text], chunk, []))
          results = self.buerokrattAnonymizerClient.predict(texts, truecase=False)

          for text, result in zip(texts, results):
            checks.append(self.check_for_anonymized_result(result))
          
          content_check.segments_checked_count += len(chunk)
          CRUD.update()

        content_check.status = ContentChecks.STATUS_DONE
        content_check.segments_passed_count = checks.count(True)
        content_check.segments_failed_count = checks.count(False)
        content_check.finished_at = datetime.datetime.now()
        CRUD.update()

      except Exception as e:
        content_check.status = ContentChecks.STATUS_FAILURE
        content_check.finished_at = datetime.datetime.now()
        CRUD.update()
        raise e

  # Checks if result has been anonymized or not
  def check_for_anonymized_result(self, result):
    input_text = result.get('sisendtekst', None)
    anonymized_text = result.get('anonümiseeritud_tekst', None)

    if not input_text or not anonymized_text:
      return True

    return result['sisendtekst'] != result['anonümiseeritud_tekst']

  def chunk_iterator(self, iterator, n=10):
    chunk = []

    try:
      while True:
        item = next(iterator)

        if item:
          chunk.append(item)

        if len(chunk) >= n:
          yield chunk
          chunk = []
    except StopIteration:
      yield chunk


  def segment_iter(self, langs, filters, limit=None):
    i = 0
    scan_fun = self.db.scan
    seg_iter = scan_fun(langs, filters)

    for s in seg_iter:
      i += 1
      if limit and i > limit: return
      yield s


if __name__ == "__main__":
  G_CONFIG.config_logging()

  task = ContentCheckTask(sys.argv[1])
  # Delete sequentially
  task.run_sequential()
  task.finalize()