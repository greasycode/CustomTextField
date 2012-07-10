from django.db import models
from django.core.files.base import ContentFile
from custom_filefield import GridFSStorage, S3BotoStorage, CombinedFSStorage
import uuid

combinedfs_obj  = CombinedFSStorage(primary_storage=GridFSStorage(zip_n_save=True),
                            backup_storage=S3BotoStorage(zip_n_save=True))

def check_format(string):
    dollar = False
    list_ind = xrange(0, len(string))
    for i in list_ind:        
        if i % 2 == 0:
            dollar = not dollar
            if dollar and string[i] == '$':
                continue
            elif string[i] == '#':
                continue
            return False
    return True

def revert_format(string):
    new_string = ""
    list_ind = xrange(0, len(string))
    for i in list_ind:
        if i % 2 == 1:
            new_string += string[i]
    return new_string
    

def change_format(string):
    """ Appends $ and # to every alternate odd position"""    
    new_string = ""
    list_ind = xrange(0, len(string))
    dollar = True
    for i in list_ind:
        if dollar:
            new_string += '$'
        else:
            new_string += '#'
        dollar = not dollar
        new_string += string[i]        
    return new_string
    
class RboxTextField(models.CharField):
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        self.fs = combinedfs_obj
        kwargs['max_length'] = 100
        super(RboxTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):        
        if not value:
            return value
            
        if not isinstance(value, basestring):
            raise TypeError('Value should be string')
            
        if len(value) == 64 and check_format(value):
            name = revert_format(value)
            fp = self.fs.open(name)
            return fp.read()
        else:
            return value            
            
    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert pickle object to a string"""
        fname = uuid.uuid4().hex
        content_file = ContentFile(value)
        content_file.name = fname
        name = self.fs.save(fname, content_file)
        return change_format(name)

    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = RboxTextField
        field = super(RboxTextField, self).formfield(**kwargs)
        if not field.help_text:
            field.help_text = "Enter valid text"
        return field    