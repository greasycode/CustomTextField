from django.db import models
from django.conf import settings
import uuid

# Create your models here.
from storage_backends.mongofs import GridFSStorage
from storage_backends.s3botofs import S3BotoStorage
from field.tasks import Backup
from django.contrib.contenttypes.models import ContentType
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["field.customfilefield.CustomFileField"])

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

@property
def real_name(self):
    name = self.name.split('/')[1]
    return name

def folder(instance, name):
    ctype = ContentType.objects.get_for_model(instance)
    return "%s.%s/%s/%s" % (ctype.app_label, ctype.model, uuid.uuid4().hex, name)
        

class CustomFileField(models.FileField):    
    def __init__(self, *args, **kwargs):
        setattr(self.attr_class, "real_name", real_name)
        backup_storage = kwargs.pop('backup_storage', None)
        default_primary_storage_class = getattr(settings, 'RBOXFILEFIELD_DEFAULT_STORAGE', None)
        if default_primary_storage_class:
            default_primary_storage_class = get_class(default_primary_storage_class)
        if not default_primary_storage_class:
            default_primary_storage_class = GridFSStorage
        primary_storage = kwargs.pop('primary_storage', default_primary_storage_class())
        upload_to = kwargs.pop('upload_to', folder)
        super(CustomFileField,self).__init__(upload_to=upload_to, *args, **kwargs)
        assert primary_storage.__class__ != backup_storage.__class__
        self.storage = primary_storage
        self.backup_storage = backup_storage

    def pre_save(self, model_instance, add):
        "Returns field's value just before saving."
        file_obj = super(CustomFileField, self).pre_save(model_instance, add)
        if self.backup_storage:
            Backup.delay(self.storage, self.backup_storage, file_obj.name)
        return file_obj

