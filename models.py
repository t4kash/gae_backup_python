# coding: utf-8
"""
GaeBackup

Copyright (c) 2014 t4kash

This software is released under the MIT License.

http://opensource.org/licenses/mit-license.php
"""
import logging
from google.appengine.ext import ndb


class AeBackupInformation(ndb.Model):
    """_AE_Backup_Information model"""
    name = ndb.StringProperty()
    kinds = ndb.StringProperty(repeated=True)
    namespaces = ndb.StringProperty(repeated=True)
    filesystem = ndb.StringProperty()
    start_time = ndb.DateTimeProperty()
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
