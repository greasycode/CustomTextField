from django.conf import settings
import os
import uuid
if __name__ != "__main__":
    from zip_utils import *
import couchdb
from datetime import datetime
from django.core.files.storage import Storage, FileSystemStorage
from django.core.files.base import ContentFile
import zipfile
from exceptions import FileNotFoundError

# file system for storing temporary files
file_system = FileSystemStorage(location=settings.TEMP_FILES)


class CouchFSStorage(Storage):

    def __init__(self, zip_n_save=False):
        self.couch = couchdb.Server(getattr(settings,'COUCH_URL','http://localhost:5984/'))
        try:
            if not hasattr(settings, 'COUCHDB_DATABASE_NAME'):
                raise AttributeError, "Specify couchdb database name in settings.py"
            db = self.couch[settings.COUCHDB_DATABASE_NAME]
        except couchdb.http.ResourceNotFound:
            db = self.couch.create(settings.COUCHDB_DATABASE_NAME)
        self.db_name = settings.COUCHDB_DATABASE_NAME
        self.db = db
        self.zip_n_save = zip_n_save

    def _open(self, uid, mode='rb'):
        try:
            doc = self.db[uid]

            if doc.get('deleted'):
                print "document is deleted"
                return False

            filename = doc.get('filename')
            attachment = self.db.get_attachment(uid,
                                                filename, default=False)
            if not attachment:
                print "This is a serious error. This should not have happened"
                return False

            # if the doc is zipped
            if doc.get('zipped'):
                #file name of zipped file
                zipped_file = filename + ".zip"                
                zipped_file = file_system.save(zipped_file,
                                               ContentFile(attachment.read()))
                zf = zipfile.ZipFile(file_system.path(zipped_file), 'r')
                if filename not in zf.namelist():
                    assert False
                filecontent = zf.open(filename)
                if file_system.exists(zipped_file):
                    file_system.delete(zipped_file)

                return filecontent
            else:
                return io.BytesIO(attachment)
        except couchdb.http.ResourceNotFound:
            raise FileNotFoundError("File with name %s not found" % uid)

    def _save(self, new_unique_id, content):
        filename = new_unique_id
        
        if self.zip_n_save:
            zipped_file = filename + ".zip"
            zipped_file = file_system.save(zipped_file, ContentFile(""))
            zf = zipfile.ZipFile(file_system.path(zipped_file), 'w', zipfile.ZIP_DEFLATED)
            zf.writestr(filename, content.file.read())
            zf.close()
            filecontent = file_system.open(zipped_file).read()
            if file_system.exists(zipped_file):
                file_system.delete(zipped_file)

        self.db[new_unique_id] = {'filename': filename,
                                  'size': len(filecontent), 'deleted': False,
                                  'zipped': self.zip_n_save}
        self.db.put_attachment(self.db[new_unique_id],
                               filecontent, filename=filename)
        return new_unique_id

    def delete(self, name):
        doc = self.db.get(new_unique_id)
        self.db.delete(doc)

    def exists(self, new_unique_id):
        return (new_unique_id in self.db)

    def path(self, new_unique_id):
        return new_unique_id

    def size(self, uid):
        attachment = self.db.get_attachment(uid, 'doc', default=False)
        return os.path.getsize(attachment.read().encode('utf-8'))

    def url(self, new_unique_id):
        return new_unique_id

    def accessed_time(self, name):
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we change it
        del odict['couch']           # remove filehandle entry
        del odict['db']
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)   # update attributes
        self.couch = couchdb.Server()
        self.db = self.couch[dict['db_name']]
