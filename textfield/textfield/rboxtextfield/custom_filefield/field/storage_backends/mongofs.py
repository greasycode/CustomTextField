from django.conf import settings
import os
import itertools
from django.core.files.base import File
from django.core.files.storage import Storage
from django.db import connections
from django.utils.encoding import force_unicode
from zip_utils import RboxZippedFile, RboxUnZippedFile
from exceptions import FileNotFoundError
try:
    from gridfs import GridFS, NoFile
except ImportError:
    raise ImproperlyConfigured("Could not load gridfs dependency.\
    \nSee http://www.mongodb.org/display/DOCS/GridFS")

try:
    from pymongo import Connection
except ImportError:
    raise ImproperlyConfigured("Could not load pymongo dependency.\
    \nSee http://github.com/mongodb/mongo-python-driver")

class GridFSStorage(Storage):
    @property
    def fs(self, zip_n_save=False):
	# This should support both the django_mongodb_engine and the GSoC 2010
	# MongoDB backend
        if not hasattr(settings, "MONGODB_DATABASE_NAME"):
            raise AttributeError, "Specify mongodb database name in settings.py"
        connection = Connection(getattr(settings,'MONGODB_HOST','localhost'),getattr(settings,'MONGODB_PORT',27017))[settings.MONGODB_DATABASE_NAME]
   	self.zip_n_save = zip_n_save
	return GridFS(connection)
    
    def get_available_name(self, name):
	"""
	Returns a filename that's free on the target storage system, and
	available for new content to be written to.
	"""
	self.real_name = name
	dir_name, file_name = os.path.split(name)
	file_root, file_ext = os.path.splitext(file_name)
	# If the filename already exists, add an underscore and a number (before
	# the file extension, if one exists) to the filename until the generated
	# filename doesn't exist.
	count = itertools.count(1)
	while self.exists(name):
	    # file_ext includes the dot.
	    name = os.path.join(dir_name, "%s_%s%s" % (file_root, count.next(), file_ext))
	return name
	
    def _open(self, name, mode='rb'):
        try:
            fileobj = self.fs.get_last_version(name)
            if fileobj.metadata.get('zipped', True):
                return RboxUnZippedFile(fileobj)
            else:
                return GridFSFile(fileobj, mode)                
        except NoFile:
            raise FileNotFoundError("File with name %s not found" % name)
            

    def _save(self, name, content, chunk_size=256):
	name = force_unicode(name).replace('\\', '/')
	file = self.fs.new_file(filename=name, chunk_size=chunk_size, real_filename=content.name,
                                metadata={'zipped': self.zip_n_save})
	if self.zip_n_save:
	    zipped_file = RboxZippedFile(content.file)
	    for chunk in zipped_file:
		file.write(chunk)
	    file.close()
	else:
	    content.open()
	    if hasattr(content, 'chunks'):
		for chunk in content.chunks():
		    file.write(chunk)
	    else:
		file.write(content)
	    file.close()
	    content.close()
	return name

    def get_valid_name(self, name):
	return force_unicode(name).strip().replace('\\', '/')

    def delete(self, name):
	fileobj = self.fs.get_last_version(name)
        fileobj = self.fs.delete(fileobj._id)
	return fileobj

    def exists(self, name):
	try:
	    self.fs.get_last_version(name)
	    return True
	except NoFile:
	    return False

    def listdir(self, path):
	return ((), self.fs.list())

    def size(self, name):
	try:
	    return self.fs.get_last_version(name).length
	except NoFile:
	    raise ValueError('File with name "%s" does not exist' % name)

    def url(self, name):
	return name
	#raise NotImplementedError()	    

class GridFSFile(File):
    def __init__(self, file, mode):
	self.file = file
	self._mode = mode
        if not self.file:
	    raise ValueError("The file doesn't exist.")

    @property
    def size(self):
	return self.file.length

    @property
    def real_filename(self):
        return self.file.real_filename

    def read(self, num_bytes=None):
	return self.file.read(num_bytes)

    def write(self, content):
	raise NotImplementedError()

    def close(self):
	self.file.close()