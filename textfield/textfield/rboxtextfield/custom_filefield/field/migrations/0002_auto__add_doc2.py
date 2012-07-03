# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Doc2'
        db.create_table('field_doc2', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('doc', self.gf('field.rboxfilefield.RboxFileField')(max_length='2')),
        ))
        db.send_create_signal('field', ['Doc2'])

    def backwards(self, orm):
        # Deleting model 'Doc2'
        db.delete_table('field_doc2')

    models = {
        'field.doc': {
            'Meta': {'object_name': 'Doc'},
            'doc': ('field.rboxfilefield.RboxFileField', [], {'max_length': "'2'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"})
        },
        'field.doc2': {
            'Meta': {'object_name': 'Doc2'},
            'doc': ('field.rboxfilefield.RboxFileField', [], {'max_length': "'2'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"})
        }
    }

    complete_apps = ['field']