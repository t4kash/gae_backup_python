# coding: utf-8
"""
GaeBackup

Copyright (c) 2014 t4kash

This software is released under the MIT License.

http://opensource.org/licenses/mit-license.php
"""
import logging
import datetime
import webapp2
import re
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.ext.ndb import metadata
from google.appengine.api import blobstore
from google.appengine.api import files
import config
from models import AeBackupInformation
from models import AeBackupInformationKindFiles


class GaeBackup(webapp2.RequestHandler):
    def get(self):
        self.backup()
        self.delete_old_backups()

        self.response.write('ok')
        self.response.set_status(200)

    def backup(self):
        if config.BACKUP_KINDS == '*':
            kinds = self.get_kinds()
        else:
            kinds = config.BACKUP_KINDS

        params = {
            'name': config.BACKUP_NAME,
            'kind': kinds,
            'filesystem': config.BACKUP_FILESYSTEM,
            'gs_bucket_name': config.BACKUP_GS_BUCKET_NAME,
        }
        url = '/_ah/datastore_admin/backup.create'
        taskqueue.add(url=url,
                      method='GET',
                      params=params,
                      target='ah-builtin-python-bundle')

    def get_kinds(self):
        """Retrieve all entity list"""
        kinds = []
        for kind in metadata.get_kinds():
            if not kind.startswith('_'):
                kinds.append(kind)
        return kinds

    def delete_old_backups(self):
        """
        Delete old backup files.
        if less than two backup files, it doesn't delete files.
        """
        try:
            backup_infos = self.get_old_backup_infos()
            for backup_info in backup_infos:
                logging.info('delete backup [%s]', backup_info.name)
                self.delete_backup(backup_info)
        except Exception as ex:
            logging.error('Failed to delete old backups')
            logging.error(ex)

    def get_old_backup_infos(self):
        infos = AeBackupInformation.query().fetch()
        # don't delete backup with a different name
        backup_infos = filter(
            lambda info: info.name.startswith(config.BACKUP_NAME), infos)
        if len(backup_infos) <= 2:
            return []

        delete_time = (datetime.datetime.utcnow()
                       - datetime.timedelta(
                           days=config.BACKUP_EXPIRE_DAYS + 0.5))
        return filter(lambda info: info.complete_time < delete_time,
                      backup_infos)

    def delete_backup(self, backup_info):
        """delete infomation entities and files"""
        kind_files = backup_info.get_kind_files()
        if backup_info.filesystem == 'blobstore':
            self.delete_blobstore_files(kind_files)
        elif backup_info.filesystem == 'gs':
            self.delete_gs_files(backup_info, kind_files)

        # delete backup information entities
        keys = [backup_info.key]
        for kind_file in kind_files:
            keys.append(kind_file.key)
        ndb.delete_multi(keys)

    def delete_blobstore_files(self, kind_files):
        """delete files in blobstore"""
        keys = []
        for kind_file in kind_files:
            for file_name in kind_file.files:
                key = files.blobstore.get_blob_key(file_name)
                if key:
                    keys.append(key)

        delete_files = []
        for key in keys:
            delete_files.append(key)
            if len(delete_files) == 100:
                blobstore.delete(delete_files)
                delete_files = []
        if delete_files:
            blobstore.delete(delete_files)

    def delete_gs_files(self, backup_info, kind_files):
        """delete files in cloud storage"""
        all_files = []
        for kind_file in kind_files:
            all_files += kind_file.files

        ma = re.match(r'^(.*)\.backup_info$', backup_info.gs_handle)
        if ma:
            prefix = ma.group(1)
        else:
            logging.error('gs file name is not match')
            raise Exception('gs file name is not match')

        for kind in backup_info.kinds:
            all_files.append(prefix + '.' + kind + '.backup_info')

        all_files.append(backup_info.gs_handle)

        delete_files = []
        for file_name in all_files:
            delete_files.append(file_name)
            if len(delete_files) == 100:
                files.delete(*delete_files)
                delete_files = []
        if delete_files:
            files.delete(*delete_files)


app = webapp2.WSGIApplication(
    [
        ('/gae-backup', GaeBackup),
    ], debug=True)
