from django.db import models
from rboxfilefield import RboxFileField
from storage_backends.couchfs import CouchFSStorage
from storage_backends.combinedfs import CombinedFSStorage
from storage_backends.s3botofs import S3BotoStorage
class Doc(models.Model):
    name = models.CharField('Name', max_length="100")
    doc = RboxFileField('File', max_length="2", primary_storage=CombinedFSStorage(), upload_to="plaban")
