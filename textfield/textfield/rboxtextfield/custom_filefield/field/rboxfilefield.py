import django.dispatch
from django.db import models
from django.conf import settings
import uuid

# Create your models here.
from storage_backends.mongofs import GridFSStorage
from storage_backends.s3botofs import S3BotoStorage
from tasks import AsyncSaveInBackup, AsyncDeleteFromBackup
from storage_backends.exceptions import FileNotFoundError
from django.contrib.contenttypes.models import ContentType
from south.modelsinspector import add_introspection_rules
from django.db.models.fields.files import FieldFile
#from django.core.files.base import ContentFile

saving_to_primary_failed = django.dispatch.Signal(providing_args=['exception'])
reading_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])
deleting_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def make_filename_generator(upload_to):
    return lambda instance=None,name=None: "%s/%s" %(upload_to,uuid.uuid4().hex)
    #ctype = ContentType.objects.get_for_model(instance)
    #return "%s.%s" % (ctype.app_label, ctype.model)

class RboxFieldFile(FieldFile):

    @property
    def real_filename(self):
        return self.file.real_filename

    def _get_file(self):
        self._require_file()
        if not hasattr(self, '_file') or self._file is None:
            try:
                self._file = self.storage.open(self.name, 'rb')
            except Exception,e:
                reading_from_primary_failed.send(sender=self, exception=e)
                if self.backup_storage:
                    self._file = self.backup_storage.open(self.name, 'rb')                
        return self._file

    def _set_file(self, file):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    def delete(self,*args,**kwargs):
        if self.backup_storage:
            AsyncDeleteFromBackup.delay(self.backup_storage, self.name)
        try:
            super(RboxFieldFile,self).delete(*args,**kwargs)
        except Exception,e:
            deleting_from_primary_failed.send(sender=self, exception=e)
    delete.alters_data = True

    def save_in_backup(self, name, content, save=True , *args, **kwargs):
        name = self.field.generate_filename(self.instance, name)
        self.name = self.backup_storage.save(name, content)
        setattr(self.instance, self.field.name, self.name)

        # Update the filesize cache
        self._size = len(content)
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()

    def save(self, name, content, save=True, *args, **kwargs):
        try:
            super(RboxFieldFile,self).save(name, content, save, *args, **kwargs) #assigns the variable self.name
        except Exception,e:
            saving_to_primary_failed.send(sender=self, exception=e)
            if self.backup_storage:
                self.save_in_backup(name, content, save, *args, **kwargs)
        else:
            if self.backup_storage:
                AsyncSaveInBackup.delay(self.storage, self.backup_storage, self.name)
    save.alters_data = True

class RboxFileField(models.FileField):
    attr_class = RboxFieldFile
    def __init__(self, *args, **kwargs):
        #setattr(self.attr_class, "real_name", real_name)
        backup_storage = kwargs.pop('backup_storage', None)
        default_primary_storage_class = getattr(settings, 'RBOXFILEFIELD_DEFAULT_STORAGE', None)
        if default_primary_storage_class:
            default_primary_storage_class = get_class(default_primary_storage_class)
        if not default_primary_storage_class:
            default_primary_storage_class = GridFSStorage
        primary_storage = kwargs.pop('primary_storage', default_primary_storage_class())
        upload_to = kwargs['upload_to']
        if not callable(upload_to):
            upload_to = make_filename_generator(upload_to)
        kwargs['upload_to'] = upload_to
        super(RboxFileField,self).__init__(*args, **kwargs)
        assert primary_storage.__class__ != backup_storage.__class__
        self.storage = primary_storage
        self.backup_storage = backup_storage
        setattr(self.attr_class, "backup_storage", backup_storage)

introspection_rules = [((RboxFileField,),[],{"upload_to": ["upload_to",{}],},)]
add_introspection_rules(introspection_rules, ["modules.custom_filefield.field.rboxfilefield.RboxFileField"])

