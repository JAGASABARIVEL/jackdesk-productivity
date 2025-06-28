from django.db import models

class DeviceLogin(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hostname} -> {self.email}"
