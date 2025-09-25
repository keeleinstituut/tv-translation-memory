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
import tempfile, os, glob, shutil
import datetime
import copy
from TMDbApi.TMDbApi import TMDbApi
from TMX.TMXWriter import TMXIterWriter
from Config.Config import G_CONFIG
from RestApi.Models import Tags, app

class TMExport:
  ALL_FILENAME = 'all.tmx'

  def __init__(self, username):
    self.db = TMDbApi()
    self.username = username

  def export(self, export_id, langs, filters=None, duplicates_only=False, limit=None):
    # Export path will have "." in the beginning to indicate work in progress
    export_path = self._get_export_path("." + export_id)
    os.makedirs(export_path, exist_ok=True)

    # Temporary zip file.
    tmpfile = os.path.join(export_path, "_".join(langs).upper() + '.zip')
    writer = TMXIterWriter(tmpfile, langs[0])

    def segment_iter(filters):
      i = 0

      scan_fun = self.db.scan if not duplicates_only else self.db.get_duplicates
      seg_iter = scan_fun(langs, filters)
      for s in seg_iter:
        i += 1
        if limit and i > limit: return
        yield s

    def write_iter(segment_iterator):
      for fn, segments in segment_iterator:
        for data in writer.write_iter(segments, fn):
          # TODO: in addition, write data to a local file to import it
          # at the end of generation
          yield data
      # Zip footer
      for data in writer.write_close():
        yield data

    def by_file_name_iter():
      file_names = [self.ALL_FILENAME, *self.db.file_names(langs, filters)]

      # Iterate file by file
      for fn in file_names:
        if fn is self.ALL_FILENAME:
          segments = segment_iter(filters)
        else:
          segments = segment_iter({
            **filters,
            'file_name': [fn],
          })
        yield fn, segments

    def by_tag_iter():
      for tag_id in filters['domain']:
        filters_single_tag = copy.deepcopy(filters)
        filters_single_tag['domain'] = [tag_id]
        tag = self.fetch_tag(tag_id)
        fn = "{}.tmx".format(tag.name)

        segments = segment_iter(filters_single_tag)
        yield fn, segments

    def combined_iter():
      fn = "combined.tmx"
      segments = segment_iter(filters)
      yield fn, segments


    iter_function = combined_iter if len(list(filters['domain'])) > 1 else by_tag_iter

    # Generate zipped TMX file(s)
    of = open(tmpfile, "wb")
    for d in write_iter(iter_function()):
      of.write(d)
    # When is done, finalize by renaming export path
    os.rename(export_path, self._get_export_path(export_id))

    return tmpfile

  def list(self, export_id='*'):
    export_pattern = os.path.join(self._get_export_path(export_id), '*.zip')
    flist = []
    for f in glob.glob(export_pattern):
      fdict = dict()
      split_path = os.path.split(f)
      fdict["filename"] = split_path[-1]
      fdict["filepath"] = split_path[-2]
      fdict["id"] = os.path.basename(split_path[-2])
      fdict["export_time"] = datetime.datetime.fromtimestamp(os.path.getmtime(f))
      fdict["size"] = os.path.getsize(f)
      flist.append(fdict)
    return flist

  def fetch_tag(self, tag_id):
    with app.app_context():
      tag = Tags.query.get(tag_id)
    return tag

  def delete(self, export_id):
    try:
      shutil.rmtree(self._get_export_path(export_id))
    except FileNotFoundError:
      pass


  def _get_export_path(self, export_id):
    # Setup export path
    export_path = os.path.join(G_CONFIG.config.get('export_path', tempfile.gettempdir()),
                                    self.username,
                                    export_id)
    return export_path