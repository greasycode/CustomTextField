from django.db import models
from django.core.files.base import ContentFile
from django.core.files import File
from storage_backends import GridFSStorage, S3BotoStorage, CombinedFSStorage, CouchFSStorage
import uuid
combinedfs_obj  = CombinedFSStorage(primary_storage=GridFSStorage(),
                            backup_storage=S3BotoStorage())


class RboxTextField(models.CharField):
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        self.fs = combinedfs_obj
        kwargs['max_length'] = 100
        super(RboxTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        
        if not value:
            return value
            
        if isinstance(value, ContentFile):
            fname = uuid.uuid4().hex
            value.name = fname
            return value
        try:
            fp = self.fs.open(value)
            return fp.read()
        except:
            pass
        
        raise TypeError("field '%s' accepts only ContentFile objects" % self.name)
                
    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert pickle object to a string"""
        
        name = self.fs.save(value.name, value)
        return name


    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = RboxTextField
        field = super(RboxTextField, self).formfield(**kwargs)
        if not field.help_text:
            field.help_text = "Enter valid text"
        return field
try:
    from south.modelsinspector import add_introspection_rules
    introspection_rules = []
    add_introspection_rules(introspection_rules, ["field.rboxtextfield.RboxTextField"])
except ImportError:
    pass

        


