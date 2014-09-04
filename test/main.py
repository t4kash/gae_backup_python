# coding: utf-8
import webapp2
from google.appengine.ext import ndb


class Model1(ndb.Model):
    hoge = ndb.StringProperty()
    fuga = ndb.StringProperty()
    piyo = ndb.StringProperty()

class Model2(ndb.Model):
    hoge = ndb.StringProperty()
    fuga = ndb.StringProperty()
    piyo = ndb.StringProperty()


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')


class MakeData(webapp2.RequestHandler):
    def get(self):
        hoge = ''
        fuga = ''
        piyo = ''
        for i in range(10):
            hoge += 'あいうえおかきくけこさしすせそ'
            fuga += 'あいうえおかきくけこさしすせそ'
            piyo += 'あいうえおかきくけこさしすせそ'

        for i in range(30):
            models = []
            for j in range(10):
                models.append(Model1(hoge=hoge, fuga=fuga, piyo=piyo))
            ndb.put_multi(models)

        for i in range(30):
            models = []
            for j in range(10):
                models.append(Model2(hoge=hoge, fuga=fuga, piyo=piyo))
            ndb.put_multi(models)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('ok')

class BackupMock(webapp2.RequestHandler):
    def get(self):
        self.response.set_status(200)


app = webapp2.WSGIApplication(
    [
        ('/', MainPage),
        ('/makedata', MakeData),
        ('/_ah/datastore_admin/backup.create', BackupMock),
    ]
    , debug=True)
