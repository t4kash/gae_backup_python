# coding: utf-8
import unittest
import webapp2
import urlparse
import datetime
import os
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util
from google.appengine.api import apiproxy_stub_map
from google.appengine.ext import ndb
from google.appengine.api import files
from gae_backup_python import config
from gae_backup_python import backup
from gae_backup_python.models import AeBackupInformation
from gae_backup_python.models import AeBackupInformationKindFiles


class BackupTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

        self.testbed.init_memcache_stub()
        self.testbed.init_blobstore_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_files_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_request(self):
        """test for push taskqueue"""
        config.BACKUP_NAME = 'gae_backup_'
        config.BACKUP_KINDS = ['Model1', 'Model2']
        config.BACKUP_FILESYSTEM = 'gs'
        config.BACKUP_GS_BUCKET_NAME = 'xxx.appspot.com'

        request = webapp2.Request.blank('/gae-backup')
        response = request.get_response(backup.app)
        self.assertEqual(200, response.status_int)
        self.assertEqual('ok', response.body)

        taskqueue_stub = apiproxy_stub_map.apiproxy.GetStub('taskqueue')
        tasks = taskqueue_stub.GetTasks("default")

        url = tasks[0]['url']
        result = urlparse.urlparse(url)
        self.assertEqual('/_ah/datastore_admin/backup.create', result.path)

        params = urlparse.parse_qs(result.query)
        self.assertEqual(config.BACKUP_NAME, params['name'][0])
        kinds = sorted(params['kind'])
        self.assertEqual(config.BACKUP_KINDS, kinds)
        self.assertEqual(config.BACKUP_FILESYSTEM, params['filesystem'][0])
        self.assertEqual(config.BACKUP_GS_BUCKET_NAME,
                         params['gs_bucket_name'][0])

    def test_delete_old_backups_blobstore(self):
        """test for delete old backup files of blobstore"""
        self._make_backup_info_blobstore(8)

        config.BACKUP_EXPIRE_DAYS = 4
        config.BACKUP_KINDS = '*'
        config.BACKUP_FILESYSTEM = ''

        request = webapp2.Request.blank('/gae-backup')
        response = request.get_response(backup.app)
        self.assertEqual(200, response.status_int)

        infos = AeBackupInformation.query().fetch()
        self.assertEqual(5, len(infos))

        info_files = AeBackupInformationKindFiles.query().fetch()
        self.assertEqual(5, len(info_files))

    def _make_backup_info_blobstore(self, num):
        file_num = 3
        dt = datetime.datetime.utcnow()
        for i in range(num):
            # _AE_Backup_Information
            info = AeBackupInformation(
                name=config.BACKUP_NAME,
                filesystem='blobstore',
                start_time=dt,
                complete_time=dt + datetime.timedelta(hours=1)
            )
            info.put()
            dt -= datetime.timedelta(days=1)

            # _AE_Backup_Information_Kind_Files
            info_files = AeBackupInformationKindFiles()
            info_files.files = []
            if i == (num - 1):
                file_num = 120  # 100 over at last
            for j in range(file_num):
                # make blobstore file
                file_name = files.blobstore.create(
                    mime_type='application/octet-stream')
                with files.open(file_name, 'a') as f:
                    f.write('asdfghjkl')
                files.finalize(file_name)
                info_files.files.append(file_name)

            info_files.key = ndb.Key(
                AeBackupInformationKindFiles._get_kind(),
                AeBackupInformationKindFiles.allocate_ids(1)[0],
                parent=info.key
            )
            info_files.put()

    def test_delete_old_backups_gs(self):
        """test for delete old backup files of cloud storage"""
        self._make_backup_info_gs(8)

        config.BACKUP_EXPIRE_DAYS = 3
        config.BACKUP_KINDS = '*'
        config.BACKUP_FILESYSTEM = 'gs'
        config.BACKUP_GS_BUCKET_NAME = 'xxx.appspot.com'

        request = webapp2.Request.blank('/gae-backup')
        response = request.get_response(backup.app)
        self.assertEqual(200, response.status_int)

        infos = AeBackupInformation.query().fetch()
        self.assertEqual(4, len(infos))

        info_files = AeBackupInformationKindFiles.query().fetch()
        self.assertEqual(4, len(info_files))

    def _make_backup_info_gs(self, num):
        file_num = 3
        dt = datetime.datetime.utcnow()
        for i in range(num):
            # _AE_Backup_Information
            kinds = ['Model1', 'Model2']

            info = AeBackupInformation(
                name=config.BACKUP_NAME,
                filesystem='gs',
                kinds=kinds,
                start_time=dt,
                complete_time=dt + datetime.timedelta(hours=1)
            )
            info.put()
            prefix = ('/gs/' + config.BACKUP_GS_BUCKET_NAME
                      + '/' + info.key.urlsafe() + '.')
            info.gs_handle = prefix + 'backup_info'
            info.put()
            dt -= datetime.timedelta(days=1)

            self._make_gs_file(info.gs_handle)
            for kind in kinds:
                self._make_gs_file(prefix + kind + '.backup_info')

            # _AE_Backup_Information_Kind_Files
            info_files = AeBackupInformationKindFiles()
            info_files.files = []
            if i == (num - 1):
                file_num = 120  # 100 over at last
            for j in range(file_num):
                # make blobstore file
                file_name = ('/gs/' + config.BACKUP_GS_BUCKET_NAME
                             + '/datastore_backup_' + config.BACKUP_NAME
                             + os.urandom(16).encode('hex') + '-output')
                self._make_gs_file(file_name)
                info_files.files.append(file_name)

            info_files.key = ndb.Key(
                AeBackupInformationKindFiles._get_kind(),
                AeBackupInformationKindFiles.allocate_ids(1)[0],
                parent=info.key
            )
            info_files.put()

    def _make_gs_file(self, file_name):
        gs = files.gs.create(file_name,
                             mime_type='application/octet-stream')
        with files.open(gs, 'a') as f:
            f.write('asdfghjkl')
        files.finalize(gs)
