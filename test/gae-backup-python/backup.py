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
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.ext.ndb import metadata
from google.appengine.api import blobstore
from google.appengine.api import files
import config


class AeBackupInformation(ndb.Model):
    """_AE_Backup_Information model"""
    name = ndb.StringProperty()
    kinds = ndb.StringProperty()
    namespaces = ndb.StringProperty(repeated=True)
    filesystem = ndb.StringProperty()
    start_time = ndb.StringProperty()
    completed_jobs = ndb.StringProperty(repeated=True)
    complete_time = ndb.DateTimeProperty()
    orginal_app = ndb.StringProperty()
    gs_handle = ndb.TextProperty()
    destination = ndb.StringProperty()

    @classmethod
    def _get_kind(cls):
        return '_AE_Backup_Information'

    def get_kind_files(self):
        return AeBackupInformationKindFiles.query(ancestor=self.key).fetch()


class AeBackupInformationKindFiles(ndb.Model):
    """_AE_Backup_Information_Kind_Files model"""
    files = ndb.StringProperty(repeated=True)

    @classmethod
    def _get_kind(cls):
        return '_AE_Backup_Information_Kind_Files'


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
        backup_infos = AeBackupInformation.query().fetch()
        if len(backup_infos) <= 2:
            return []

        delete_time = (datetime.datetime.utcnow()
                       - datetime.timedelta(
                           days=config.BACKUP_EXPIRE_DAYS + 0.5))
        return filter(lambda info: info.complete_time < delete_time,
                      backup_infos)

    def delete_backup(self, backup_info):
        kind_files = backup_info.get_kind_files()
        logging.info(backup_info.filesystem)
        if backup_info.filesystem == 'blobstore':
            self.delete_blobstore_files(kind_files)
        elif backup_info.filesystem == 'gs':
            pass

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


app = webapp2.WSGIApplication(
    [
        ('/gae-backup', GaeBackup),
    ], debug=True)
