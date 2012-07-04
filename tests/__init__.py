from django.utils import unittest
import os
from django.db import models
from django.core.files.base import ContentFile
from filefield.field.rboxtextfield import RboxTextField

class RboxTextFieldTest(unittest.TestCase):
    
    def setUp(self):
        """ Setup the objects need for running the tests"""
        
        class Mymodel(models.Model):
            text = RboxTextField()
            
        from django.core import management
        management.call_command('syncdb', interactive=False)
        self.mymodel_class = Mymodel
        self.filename =  os.path.dirname(__file__) + "/" + "text.txt"

    def get_content_file_obj(self, filename):
        f = open(filename, 'r')
        buff = f.read()
        return ContentFile(buff)
        
    def test_raises_exception(self):
        """  RboxTextField should raise an error
             if anything other than ContentFile obj
             is passed
        """
        self.assertRaises(TypeError, self.mymodel_class.objects.create,
                          {'text': 'This shouldnt be accepted'}
        )
        
        self.assertRaises(TypeError, self.mymodel_class.objects.create,
                          {'text': [1, 2, 3]}
        )
        contentfile_obj = self.get_content_file_obj(self.filename)
        
        self.assertRaises(TypeError, self.mymodel_class.objects.create,
                          {'text': contentfile_obj.read()}
        )

    def test_object_creation(self):
        """ Check the proper creation of object (includes db retreival)"""
        
        mym = self.mymodel_class.objects.create(text=self.get_content_file_obj(self.filename))
        mym_id = mym.id
        mym_db = self.mymodel_class.objects.get(id=mym_id)
        contentfile_obj = self.get_content_file_obj(self.filename)
        self.assertEqual(mym_db.text, contentfile_obj.read())