# coding: utf-8
import webapp2
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.ext.ndb import metadata
import config


class GaeBackup(webapp2.RequestHandler):
    def get(self):
        #self.response.set_status(404)

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

        self.response.write('ok')
        self.response.set_status(200)

    def get_kinds(self):
        """Retrieve all entity list"""
        kinds = []
        for kind in metadata.get_kinds():
            if not kind.startswith('_'):
                kinds.append(kind)
        return kinds


app = webapp2.WSGIApplication(
    [
        ('/gae-backup', GaeBackup),
    ], debug=True)
