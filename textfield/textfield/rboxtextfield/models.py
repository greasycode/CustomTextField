from django.db import models
from django.core.files.base import ContentFile
from custom_filefield import GridFSStorage, S3BotoStorage, CombinedFSStorage
import uuid
import django.dispatch
saving_to_primary_failed = django.dispatch.Signal(providing_args=['exception'])
reading_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])
deleting_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])


class RboxTextField(models.CharField):
    __metaclass__ = models.SubfieldBase
    
    def save_in_backup(self, name, content, save=True , *args, **kwargs):
        self.name = self.backup_storage.save(name, content)
        return name
    
    def __init__(self, *args, **kwargs):
        self.fs = CombinedFSStorage(primary_storage=GridFSStorage(),
                                    backup_storage=S3BotoStorage())

        kwargs['max_length'] = 100
        super(RboxTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):        
        if not value:
            return value
        if isinstance(value, ContentFile):
            return value
            
        fp = self.fs.open(value)
        return fp.read()
                
    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert pickle object to a string"""        
        fname = uuid.uuid4().hex
        name = self.fs.save(fname, value)
        return name


    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = RboxTextField
        field = super(RboxTextField, self).formfield(**kwargs)
        if not field.help_text:
            field.help_text = "Enter valid pickle"
        return field    

class MyModel(models.Model):
    text = RboxTextField()
