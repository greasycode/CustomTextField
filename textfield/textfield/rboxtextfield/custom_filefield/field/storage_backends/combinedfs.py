import django.dispatch
from textfield.rboxtextfield.custom_filefield.field.tasks import AsyncSaveInBackup, AsyncDeleteFromBackup
from django.core.files.storage import Storage
saving_to_primary_failed = django.dispatch.Signal(providing_args=['exception'])
reading_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])
deleting_from_primary_failed = django.dispatch.Signal(providing_args=['exception'])

class CombinedFSStorage(Storage):
    def __init__(self, primary_storage, backup_storage=None):
        self.primary_storage = primary_storage
        self.backup_storage = backup_storage

    def save_in_backup(self, name, content, save=True , *args, **kwargs):
        self.name = self.backup_storage.save(name, content)
        return self.name

	
    def _open(self, name, mode='rb'):
        try:
            self._file  = self.primary_storage.open(name, 'rb')
        except Exception, e:
             reading_from_primary_failed.send(sender=self, exception=e)
             if self.backup_storage:
                 self._file = self.backup_storage.open(self.name, 'rb')
             else:
                 raise
        return self._file            
            

    def _save(self, name, content):
        try:
            self.name = self.primary_storage.save(name, content)
            import ipdb; ipdb.set_trace()
        except Exception, e:
            saving_to_primary_failed.send(sender=self, exception=e)
            if self.backup_storage:
                self.name = self.save_in_backup(name, content)
            else:
                raise            
        else:
            if self.backup_storage:
                AsyncSaveInBackup.delay(self.primary_storage, self.backup_storage, self.name)
            
        return self.name                
        
    def delete(self, name):
        if self.backup_storage:
            AsyncDeleteFromBackup.delay(self.backup_storage, self.name)
        try:
            self.primary_storage.delete(name)
        except Exception,e:
            deleting_from_primary_failed.send(sender=self, exception=e)

    def exists(self, name):
        try:
            in_primary = self.primary_storage.exists(name)
            in_backup = self.backup_storage.exists(name)
        except Exception, e:
            return locals().get('in_primary', False) or locals().get('in_backup', False)
        return in_primary or in_backup

    def listdir(self):
	return ((), self.primary_storage.list())

    def size(self, name):
	try:
	    return self.primary_storage.size(name)
	except :
            return self.backup_storage.size(name)

    def url(self, name):
	return name