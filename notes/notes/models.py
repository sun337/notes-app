from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    drive_id = models.CharField(max_length=200)
    time_created = models.DateTimeField(auto_now_add=True, blank=True)