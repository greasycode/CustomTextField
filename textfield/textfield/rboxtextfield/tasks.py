from celery.task  import Task
from celery.registry import tasks
from django.core.files.base import ContentFile

class AsyncSaveInBackup(Task):
    def run(self, primary_storage, backup_storage,  filename):
        primary_file = primary_storage.open(filename)
        real_filename = primary_file.real_filename
        primary_file = ContentFile(primary_file.read())
        primary_file.name = real_filename
        backup_storage.save(filename, primary_file)
        
class AsyncDeleteFromBackup(Task):
    def run(self, backup_storage, filename):
        backup_storage.delete(filename)

tasks.register(AsyncSaveInBackup)
tasks.register(AsyncDeleteFromBackup)
